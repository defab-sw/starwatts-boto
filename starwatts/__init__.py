# -*- coding: utf-8 -*-

# Boto related imports
from boto.ec2.instance import Instance
from boto.ec2.image import Image
from boto.ec2.connection import EC2Connection
from boto.ec2.volume import Volume
from boto.ec2.snapshot import Snapshot

# General Outscale import
from .starwatts import StarWatts
from .cloud_app import CloudApp

# Instances related imports
from .meta.instance import get_all_attached_volumes, lower_tags
from .meta.instance import get_all_security_groups_ids, get_all_security_groups, get_single_security_group
from .meta.instance import instance_set_private, stop_and_wait, terminate_and_clean

# Connection related imports
from .meta.connection import security_group_exists, keypair_exists
from .meta.connection import connection_set_private, get_instances_by_tags, quick_instance

# Volume related imports
from .meta.volume import get_attached_instance, increase_size

# General related imports
from .meta.general import wait_for

setattr(Instance, 'get_all_attached_volumes', get_all_attached_volumes)
setattr(Instance, 'get_all_security_groups', get_all_security_groups)
setattr(Instance, 'get_all_security_groups_ids', get_all_security_groups_ids)
setattr(Instance, 'get_single_security_group', get_single_security_group)
setattr(Instance, 'lower_tags', lower_tags)
setattr(Instance, 'wait_for', wait_for)
setattr(Instance, 'set_private', instance_set_private)
setattr(Instance, 'stop_and_wait', stop_and_wait)
setattr(Instance, 'terminate_and_clean', terminate_and_clean)

setattr(Image, 'wait_for', wait_for)

setattr(Snapshot, 'wait_for', wait_for)

setattr(Volume, 'wait_for', wait_for)
setattr(Volume, 'get_attached_instance', get_attached_instance)
setattr(Volume, 'increase_size', increase_size)

setattr(EC2Connection, 'security_group_exists', security_group_exists)
setattr(EC2Connection, 'keypair_exists', keypair_exists)
setattr(EC2Connection, 'set_private', connection_set_private)
setattr(EC2Connection, 'get_instances_by_tags', get_instances_by_tags)
setattr(EC2Connection, 'quick_instance', quick_instance)
