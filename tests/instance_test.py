# -*- coding: utf-8 -*-

from boto.ec2.volume import Volume
from boto.ec2.securitygroup import SecurityGroup


def test_get_single_security_group(instance):
    sg = instance.get_single_security_group()
    assert isinstance(sg, SecurityGroup)


def test_get_all_security_groups(instance):
    sgs = instance.get_all_security_groups()
    assert isinstance(sgs, list)
    for sg in sgs:
        assert isinstance(sg, SecurityGroup)


def test_get_all_security_groups_ids(instance):
    sg_ids = instance.get_all_security_groups_ids()
    assert isinstance(sg_ids, list)
    for i in sg_ids:
        assert isinstance(i, str)


def test_get_all_attached_volumes(instance):
    volumes = instance.get_all_attached_volumes()
    assert isinstance(volumes, list)
    for v in volumes:
        assert isinstance(v, Volume)
        assert v.attach_data.instance_id == instance.id


def test_lower_tags(instance):
    instance.lower_tags()
    for key, val in instance.tags.items():
        assert key.islower()
        assert val.islower()


def test_set_private(new_instance):
    new_instance.set_private()




