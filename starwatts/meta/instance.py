# -*- coding: utf-8 -*-

from utils import query_yes_no


def get_single_security_group(self):
    """
    Get one security groups applied to this instance.

    :param boto.ec2.instance.Instance self:
            Current instance.

    :return: A single security group applied to this instance.
    :rtype: boto.ec2.securitygroup.SecurityGroup
    """
    for sg in self.connection.get_all_security_groups():
        for inst in sg.instances():
            if inst.id == self.id:
                return sg


def get_all_security_groups(self):
    """
    Get all the security groups applied to this instance.

    :param boto.ec2.instance.Instance self:
        Current instance.

    :return: list of boto.ec2.securitygroup.SecurityGroup
    :rtype: list
    """
    sgs = list()
    for sg in self.connection.get_all_security_groups():
        for inst in sg.instances():
            if inst.id == self.id:
                sgs.append(sg)
    return sgs


def get_all_security_groups_ids(self):
    """
    Get all the security groups ids applied to this instance.

    :param boto.ec2.instance.Instance self:
        Current instance.

    :return: list of SecurityGroup.id (string)
    :rtype: list
    """
    sgs = list()
    for sg in self.connection.get_all_security_groups():
        for inst in sg.instances():
            if inst.id == self.id:
                sgs.append(sg.id)
    return sgs


def get_all_attached_volumes(self):
    """
    Get all the the volumes that are attached to an instance.

    :param boto.ec2.instance.Instance self:
        Current instance.

    :return: List of attached boto.ec2.volume.Volume
    :rtype: list
    """
    return [v for v in self.connection.get_all_volumes() if v.attach_data.instance_id == self.id]


def lower_tags(self):
    """
    Lowers all the tags of an instance.

    :param boto.ec2.instance.Instance self:
        Current instance.
    """
    new_tags = {key.lower(): val.lower() for key, val in self.tags.items()}
    self.remove_tags({key: None for key, val in self.tags.items()})
    self.add_tags(new_tags)


def instance_set_private(self, terminate=False):
    """
    Stop a list of Instance and recreate it with only a private ip. Keeps all tags, name and security groups.

    :param boto.ec2.instance.Instance self:
        Current instance.
    :param bool terminate:
        Terminates the old instance. Default : False.

    :return: List of tuple containing the old private ip, and the new corresponding private ip
    :rtype: list
    """

    log = []
    self.stop()
    self.wait_for('stopped')
    print("Fetching security groups... ", end="")
    sg_ids = self.get_all_security_groups_ids()
    print("Done.")
    print("Creating image... ", end="")
    img_id = self.create_image('temp')
    img = self.connection.get_image(img_id)
    print("Done.")
    img.wait_for('available')
    print("Creating new private instance... ", end="")
    new_private_instance = self.connection.create_private_instance(key_name=self.key_name, image=img_id,
                                                                   sg_ids=sg_ids, i_type=self.instance_type,
                                                                   tags=self.tags)
    log.append((self.private_ip_address, new_private_instance.private_ip_address))
    print("Done.")
    print("Removing image... ", end="")
    self.connection.deregister_image(image_id=img_id, delete_snapshot=True)
    print("Done.")
    if terminate:
        self.terminate()
    return log


def stop_and_wait(self):
    """
    Stops an instance and waits for it to be in stopped state.

    :param boto.ec2.instance.Instance self:
        Current instance.
    """
    self.stop()
    self.wait_for('stopped')


def terminate_and_clean(self, confirm=True, debug=False):
    """
    Terminates an instance and deletes the associated security group and private key if they are named after the name
    tag of the instance.

    For example if an instance has the following security groups ['standard', 'instance_name'] and the following keypair
    ['instance_name'], then only the security group 'instance_name' and the keypair 'instance_name' will be deleted.

    This method will also ask for confirmation, except if the argument 'confirm' is set to False.

    :param boto.ec2.instance.Instance self:
        Current instance.
    :param bool confirm:
        Whether or not to ask for confirmation when executing this method. Default : True.
    :param bool debug:
        Displays debug information. Default : False.
    """
    if 'name' not in self.tags:
        print("This instance doesn't have a name tag. Aborting.")
        return
    print("Please wait.")
    sgs = [sg for sg in self.get_all_security_groups() if sg.name == self.tags['name'] and len(sg.instances()) == 1]
    kp = self.connection.get_all_key_pairs(self.key_name)[0]
    print("SG : {}".format(", ".join(["{} {}".format(sg.name, sg.id) for sg in sgs])))
    print("KeyPair : {}".format(kp.name))
    if confirm:
        if not query_yes_no("Are you sure ?"):
            print("Aborting")
            return
    self.terminate()
    self.wait_for('terminated')
    print("Instance is terminated.")
    for sg in sgs:
        sg.delete()
    print("Security Group(s) are deleted.")
    kp.delete()
    print("KeyPair is deleted.")





