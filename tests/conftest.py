# -*- coding: utf-8 -*-

import os

import pytest
from boto.exception import EC2ResponseError


@pytest.fixture(scope='function')
def volume(request):
    from starwatts import StarWatts
    s = StarWatts(access_key=os.environ['ACCESS_KEY'], secret_key=os.environ['PRIVATE_KEY'])
    c = s.get_connection()
    zone = c.get_all_volumes()[0].zone
    fixture_volume = c.create_volume(1, zone)
    fixture_volume.wait_for('available')

    def teardown():
        try:
            fixture_volume.delete()
        except EC2ResponseError:
            pass
    request.addfinalizer(teardown)

    return fixture_volume


@pytest.fixture(scope='function')
def attached_volume(request):
    from starwatts import StarWatts
    s = StarWatts(access_key=os.environ['ACCESS_KEY'], secret_key=os.environ['PRIVATE_KEY'])
    c = s.get_connection()
    inst = c.quick_instance('pytest-volume', 'ami-14506474', 't1.micro')
    inst.wait_for('running')

    def teardown():
        c.delete_key_pair(inst.key_name)
        inst.terminate()
    request.addfinalizer(teardown)

    return inst.get_all_attached_volumes()[0]


@pytest.fixture(scope='function')
def new_instance(request):
    from starwatts import StarWatts
    s = StarWatts(access_key=os.environ['ACCESS_KEY'], secret_key=os.environ['PRIVATE_KEY'])
    c = s.get_connection()
    inst = c.quick_instance('pytest-new', 'ami-14506474', 't1.micro', private=False)
    inst.wait_for('running')

    def teardown():
        c.delete_key_pair(inst.key_name)
        inst.terminate()
    request.addfinalizer(teardown)

    return inst


@pytest.fixture(scope='module')
def stw():
    from starwatts import StarWatts
    return StarWatts(access_key=os.environ['ACCESS_KEY'], secret_key=os.environ['PRIVATE_KEY'])


@pytest.fixture(scope='module')
def instance():
    from starwatts import StarWatts
    s = StarWatts(access_key=os.environ['ACCESS_KEY'], secret_key=os.environ['PRIVATE_KEY'])
    return s.conn.get_only_instances()[0]
