# -*- coding: utf-8 -*-

import pytest
from boto.exception import EC2ResponseError
from boto.ec2 import EC2Connection

from starwatts import StarWatts, CloudApp


def test_init_empty():
    assert isinstance(StarWatts(), StarWatts)


def test_init_wrong_file():
    with pytest.raises(ValueError):
        StarWatts("tests/data/wrong.yml")


def test_init_good_file():
    StarWatts("tests/data/valid.yml")


def test_load_configuration():
    s = StarWatts()
    s.load_configuration("tests/data/valid.yml")


def test_init_missing_arg():
    with pytest.raises(ValueError):
        StarWatts(access_key="0xSw4G")
    with pytest.raises(ValueError):
        StarWatts(secret_key="0xSw4G")


def test_init_wrong_keys():
    s = StarWatts(access_key="wrong", secret_key="wrong")
    c = s.get_connection()
    with pytest.raises(EC2ResponseError):
        c.get_only_instances()


def test_get_connection():
    s = StarWatts()
    assert s.get_connection() is None
    s = StarWatts(access_key="wrong", secret_key="wrong")
    assert isinstance(s.get_connection(), EC2Connection)


def test_all_vms(stw):
    c = stw.get_connection()
    assert len(stw.all_vms()) == len(c.get_only_instances())


def test_pretty_report(stw):
    stw.pretty_report()
    stw.pretty_report(name='bastion')
    stw.pretty_report(zone='starwatts', privacy=True)
    stw.pretty_report(os='debian', env='prod')


def test_list_ressources(stw):
    stw.list_ressources()


def test_generate_ansible_hosts_file(stw):
    classic = stw.generate_ansible_hosts_file()
    assert "[env_prod:children]" in classic
    assert "[env_dev:children]" in classic
    assert "[zone_starwatts:children]" in classic
    assert "[os_debian:children]" in stw.generate_ansible_hosts_file(grain=['env', 'zone', 'os'])


def test_generate_ssh_config(stw):
    assert "ProxyCommand ssh -q -W %h:%p bastion" not in stw.generate_ssh_config()
    assert "ProxyCommand ssh -q -W %h:%p bastion" in stw.generate_ssh_config(local=True)


def test_new_cloud_app(stw):
    test_cloudapp = stw.new_cloud_app("guerilla", "1.3.2", "prod", "fake_project")
    assert isinstance(test_cloudapp, CloudApp)
