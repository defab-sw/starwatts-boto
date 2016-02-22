# -*- coding: utf-8 -*-

import os
import logging

from boto.exception import EC2ResponseError


def security_group_exists(self, sg_id=None, name=None):
    """
    Checks if a security group already exists on this connection, by name or by ID.

    :param boto.ec2.EC2Connection self: Current connection.
    :param string sg_id: ID of the security group to check. Default : None.
    :param string name: Name of the security group to check. Default : None.

    :return: True if the security group is present, False otherwise
    :rtype: bool
    """
    if sg_id:
        return sg_id in [sg.id for sg in self.get_all_security_groups()]
    elif name:
        return name in [sg.name for sg in self.get_all_security_groups()]


def keypair_exists(self, name):
    """
    Checks if a keypair already exists on this connection with the same name.

    :param boto.ec2.EC2Connection self: Current connection.
    :param string name: Name of the key pair to check

    :return: True if the key pair is present, False otherwise
    :rtype: bool
    """
    return name in [key.name for key in self.get_all_key_pairs()]


def quick_instance(self, name, image, instance_type, env_tag='dev', zone_tag='starwatts', os_tag='debian', sg_id=None,
                   private=True, extra_sg_ids=None, extra_tags=None, terminate_on_shutdown=False,
                   debug=False):
    """
    Quickly create a new instance with Starwatts standards (tags/security group/keypair conventions).

    When this function starts, it will run preliminary tests and return if one of them fails. The tests are as follow :
        - The image (AMI) should be found.
        - No instance should have the same 'name' tag.
        - No keypair with the given 'name' should already exist.
        - No security group with the given 'name' should already exist. (or a security group id was provided)

    There is a difference between the sg_id argument and the extra_sg_ids argument. If the 'sg_id' argument is set to
    something else than None, it will cancel the creation of the security group named after the 'name' argument, and use
    the provided security group instead. The 'extra_sg_ids' is a list of extra security groups that will be applied to
    the newly created machine and won't interfere with the creation of the new security group.

    A default security group will also be applied to the newly created machine to allow the connection through the
    bastion machine and allow an outgoing connection through the proxy.

    :param boto.ec2.EC2Connection self:
        Current connection.
    :param string name:
        Name of the machine. This argument will be used to generate a named security group and a keypair.
    :param string image:
        ID of the image that will be used to create the machine. (e.g : "ami-6f800eea")
    :param string instance_type:
        The type of the instance. Defines the size of the machine. (e.g : "t2.medium")
    :param string env_tag:
        The env tag. Can be either 'prod' or 'dev'. (Will raise an error otherwise) Default : 'dev'.
    :param string zone_tag:
        The zone tag. Can be either 'starwatts' or 'defab'. (Will raise an error otherwise) Default : 'starwatts'.
    :param string os_tag:
        The os tag. Default : 'debian'.
    :param string sg_id:
        The ID of a security group to apply to this VM. This will disable the creation of the new security group.
        Default : None.
    :param bool private:
        Defines if the instance should be private or not. Also defines the private tag. Default : True.
    :param list extra_sg_ids:
        A list of extra security groups id to add to the newly created machine. Default : None.
    :param dict extra_tags:
        A dictionnary {'tag_name': 'tag_value'} of tags to apply to the newly created machine. Default : None.
    :param bool terminate_on_shutdown:
        Defines whether or not to terminate the machine when it stops. Default : False.
    :param bool debug:
        Defines if the function should be verbose or not about the operation it does. Default : False.

    :return: The created boto.ec2.instance.Instance
    :rtype: boto.ec2.instance.Instance
    """
    # Debug setting
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    # Preliminary tests
    try:
        ami = self.get_image(image_id=image)
    except EC2ResponseError:
        logging.error("The image {} could not be found. Aborting.".format(image))
        return
    print("Using AMI {} : {}".format(image, ami.name))
    if len(self.get_only_instances(filters={'tag:name': name, 'instance-state-name': 'running'})) > 0 or \
       len(self.get_only_instances(filters={'tag:name': name, 'instance-state-name': 'stopped'})) > 0:
        logging.error("An instance with the same name ({}) already exists. Aborting.".format(name))
        return
    logging.debug("Test passed : No instance has the same 'name' tag.")
    if self.keypair_exists(name):
        logging.error("A keypair with the same name ({}) already exists. Aborting.".format(name))
        return
    logging.debug("Test passed : No keypair was found with the same name.")
    if sg_id is None:
        if self.security_group_exists(name=name):
            logging.error("A security group with the same name ({}) already exists. Aborting.".format(name))
            return
        logging.debug("Test passed : No security group was found with the same name.")

    # Tags generation
    logging.debug("Generating tags to apply.")
    tags = dict(name=name, os=os_tag, env=env_tag, zone=zone_tag, privacy='true' if private else 'false')
    if extra_tags is not None:
        tags.update(extra_tags)
    print("Tags : {}".format(tags))

    # Fetching needed security groups (bastion and zabbix)
    standard_sg = self.get_all_security_groups(groupnames=['standard'])
    if len(standard_sg) != 1:
        logging.error("Multiple or no security group was found for the 'bastion' search. Aborting.")
        return
    standard_sg = standard_sg[0]
    logging.debug("The following security group was found for 'standard : {} {}".format(standard_sg.id,
                                                                                        standard_sg.description))

    # Security group creation
    if sg_id is None:
        sg = self.create_security_group(name, "SG applied to {} VM".format(name))
        sg_id = sg.id

    sg_ids = [sg_id, standard_sg.id, ]
    # Using the extra security groups if any
    if extra_sg_ids is not None:
        logging.debug("Extra security groups to add : {}".format(extra_sg_ids))
        sg_ids.extend(extra_sg_ids)
    logging.debug("Security Groups : {}".format(sg_ids))

    user_data = "-----BEGIN OUTSCALE SECTION-----\nprivate_only=true\n-----END OUTSCALE SECTION-----" if private else ""
    logging.debug("Creating keypair.")
    kp = self.create_key_pair(key_name=name)
    fp = os.path.join(os.path.expanduser('~/.ssh'), '%s.pem' % kp.name)
    with open(fp, 'wb') as fd:
        fd.write(bytes(kp.material, "UTF-8"))
    logging.debug("Keypair written to ~/.ssh/{}.pem".format(name))

    resa = self.run_instances(image_id=image, key_name=name, security_groups=sg_ids, instance_type=instance_type,
                              user_data=user_data,
                              instance_initiated_shutdown_behavior='terminate' if terminate_on_shutdown else 'stop')
    inst = resa.instances[0]
    logging.debug("Adding tags to the newly created machine.")
    inst.add_tags(tags)
    return inst


def connection_set_private(self, instances_ids):
    """
    Allows to set private a single or a bunch of instances by simply giving the IDs.

    :param boto.ec2.EC2Connection self:
        Current connection.
    :param list instances_ids:
        List of instance id (e.g ['i-xxxxx', 'i-yyyyy'])

    :return: List of result
    :rtype: list
    """
    return [inst.set_private() for inst in self.get_only_instances(instance_ids=instances_ids)]


def get_instances_by_tags(self, tags):
    """
    Get all instances tagged with the tags given in arguments.

    :param boto.ec2.EC2Connection self:
        Current connection.
    :param dict tags:
        Dict of tags as strings (e.g : {'name': 'toto', 'env': 'prod'})

    :return: List of EC2Object Instance
    :rtype: list
    """
    return self.get_only_instances(filters={'tag:{}'.format(key): val for key, val in tags.items()})
