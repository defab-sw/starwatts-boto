# -*- coding: utf-8 -*-

from boto.ec2.volume import Volume
from boto.ec2.instance import Instance


def test_get_attached_instance(volume):
    assert isinstance(volume, Volume)
    inst = volume.get_attached_instance()
    assert inst is None or isinstance(inst, Instance)


def test_increase_size_not_attached(volume):
    new = volume.increase_size(2)
    assert isinstance(new, Volume)
    assert new.size == 2
    assert new.delete()


def test_increase_size_attached(attached_volume):
    inst = attached_volume.get_attached_instance()
    assert isinstance(inst, Instance)
    new = attached_volume.increase_size(15)
    assert isinstance(new, Volume)
    assert new.size == 15
    new.delete()
