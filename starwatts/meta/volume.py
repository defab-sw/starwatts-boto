# -*- coding: utf-8 -*-


def get_attached_instance(self):
    """
    Returns the Instance object the volume is mounted on.

    :param boto.ec2.volume.Volume self:
        Current volume

    :return:
        boto.ec2.instance.Instance if the volume is attached to an instance and the instance is found. None otherwise.
    :rtype: boto.ec2.instance.Instance
    """
    if self.attachment_state() == 'attached':
        return self.connection.get_only_instances(self.attach_data.instance_id)[0]
    else:
        print("{} volume isn't attached to an instance".format(self))
        return None


def increase_size(self, new_size):
    """
    This command will resize the disk to a new size. If attached to a VM, the old disk will be detached and replaced
    by the new one. This function works fine, keep in mind that the partition will remain unchanged. Thus, you'll
    need to connect to the instance and recreate the partition table using fdisk and then start a resize2disk
    command.

    :param boto.ec2.volume.Volume self:
        Current volume
    :param int new_size:
        The new size of the disk
    :return:
        The new volume that was created or None of an error occured
    :rtype: boto.ec2.volume.Volume
    """
    snapshot = self.create_snapshot("temp")
    snapshot.wait_for('100%')
    if self.attachment_state() == 'attached':
        print("{} is attached to an instance.".format(self))
        instance = self.get_attached_instance()
        device = self.attach_data.device
        new = snapshot.create_volume(instance.placement, size=new_size)
        new.wait_for('available')
        instance.stop()
        instance.wait_for('stopped')
        if not self.detach():
            print("Detach failed, restarting the VM, deleting snapshot and new disk")
            self.connection.start_instances([instance.id])
            self.connection.delete_snapshot(snapshot.id)
            self.connection.delete_volume(new.id)
            return None
        else:
            if not new.attach(instance.id, device):
                print("Attach failed, attempting to re-attach old volume.")
                if self.attach(instance.id, device):
                    print("Old device re-attached")
                    self.connection.start_instances([instance.id])
                    self.connection.delete_snapshot(snapshot.id)
                    self.connection.delete_volume(new.id)
                    return None
                else:
                    print("Something went terribly wrong. Sometimes it happens. Fix by hand.")
                    self.connection.delete_snapshot(snapshot.id)
                    self.connection.delete_volume(new.id)
                    return None
            else:
                print("New volume attached, restarting the VM")
                self.connection.start_instances([instance.id])
                self.connection.delete_snapshot(snapshot.id)
                self.connection.delete_volume(self.id)
                print("Everything went fine. New volume created and attached.")
                return new

    else:
        vol = snapshot.create_volume('eu-west-2a', size=new_size)
        vol.wait_for('available')
        self.connection.delete_snapshot(snapshot.id)
        self.connection.delete_volume(self.id)
        return vol
