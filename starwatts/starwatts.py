# -*- coding: utf-8 -*-
"""
Provides an object and an interface to work with the Outscale cloud.
"""

import yaml
import boto
from colorama import Fore, Style

from .cloud_app import CloudApp
from .constants import ENDPOINT, instance_types


class StarWatts:
    """
    Contains a set of methods to simplify the usage of the outscale API.
    Upon initialization, either pass a yaml configuration file path or BOTH the access_key and secret_key.
    Raises an error if one of the key is set and not the other.
    If none of the above are passed as argument, then the connection won't be initialized and will need to be
    initialized manually (using load_configuration() or setting self.conn to a valid EC2 Connection Object.

    :param string configuration: The path to a YAML configuration file containing crendentials (access_key, secret_key)
    :param string access_key: A string representing the access_key (required if using ak/sk method)
    :param string secret_key: A string representing the secret_key (required if using ak/sk method)
    :param string proxy: Address of the proxy to use
    :param string proxy_port: Port of the proxy to use
    """
    conn = None

    def __init__(self, configuration=None, access_key=None, secret_key=None, proxy=None, proxy_port=None):
        self.proxy = proxy
        self.proxy_port = proxy_port
        if configuration is not None:
            self.load_configuration(configuration)
        elif access_key is not None and secret_key is not None:
            self.conn = boto.connect_ec2_endpoint(ENDPOINT, access_key, secret_key, proxy=self.proxy,
                                                  proxy_port=self.proxy_port)
        elif access_key is not None and secret_key is None:
            raise ValueError("access_key is set but not secret_key")
        elif access_key is None and secret_key is not None:
            raise ValueError("secret_key is set but not access_key")

    def load_configuration(self, fp):
        """
        Opens a yaml file and reads from it, verifying that it contains at least the two authentication fields we need.

        :param string fp: Path to the yaml configuration file

        :raises ValueError: When the secret_key and/or access_key are missing in the configuration file.
        """
        with open(fp, 'r') as stream:
            cnf = yaml.load(stream)
            if 'access_key' in cnf and 'secret_key' in cnf:
                self.conn = boto.connect_ec2_endpoint(ENDPOINT, cnf['access_key'], cnf['secret_key'], proxy=self.proxy,
                                                      proxy_port=self.proxy_port)
            else:
                raise ValueError("Need access_key and secret_key in {} configuration file".format(fp))

    def get_connection(self):
        """
        Get the connection of the StarWatts instance.

        :return: The configured connection of the instance.
        :rtype: boto.ec2.EC2Connection
        """
        return self.conn

    def all_vms(self):
        """
        Shows all the VMs with tags that are in the outscale cloud

        :return: A list of tuple (tags, instance object)
        :rtype: tuple
        """
        return [(i.tags, i) for i in self.conn.get_only_instances()]

    def pretty_report(self, name=None, zone=None, os=None, env=None, privacy=None):
        """
        Prints out a pretty report of all the VMs if no argument is passed or filter by a single/multiple tags.

        :param string name: Include only the VMs that have the corresponding name tag.
        :param string zone: Include only the VMs that have the corresponding zone tag.
        :param string os: Include only the VMs that have the corresponding os tag.
        :param string env: Include only the VMs that have the corresponding env tag.
        :param string privacy: Include only the VMs that have the corresponding privacy tag.
        """
        for tags, inst in self.all_vms():
            missing = not all(key in tags for key in ['name', 'os', 'zone', 'env', 'privacy'])
            vm_name = tags.get('name', None)
            vm_zone = tags.get('zone', None)
            vm_os = tags.get('os', None)
            vm_env = tags.get('env', None)
            vm_privacy = tags.get('privacy', None)
            vm_type = inst.instance_type
            include = True
            if name:
                include = vm_name == name
            if zone and include:
                include = vm_zone == zone
            if os and include:
                include = vm_os == os
            if env and include:
                include = vm_env == env
            if privacy and include:
                include = vm_privacy == privacy
            if include:
                print("VM :           {}{}{}".format(
                    Fore.RED if missing else Fore.GREEN,
                    vm_name if vm_name else Fore.RED+"MISSING"+Style.RESET_ALL,
                    Style.RESET_ALL,
                ))
                print("OS :           {}".format(vm_os if vm_os else Fore.RED+'MISSING'+Style.RESET_ALL))
                print("Env :          {}".format(vm_env if vm_env else Fore.RED+'MISSING'+Style.RESET_ALL))
                print("Zone :         {}".format(vm_zone if vm_zone else Fore.RED+'MISSING'+Style.RESET_ALL))
                print("Private IP :   {}".format(inst.private_ip_address))
                print("Private Only : {}{}{}".format(
                    Fore.YELLOW if vm_privacy and vm_privacy == 'false' else Fore.GREEN,
                    vm_privacy if vm_privacy else Fore.RED+'MISSING',
                    Style.RESET_ALL,
                ))
                print("Type :         {}{}".format(
                    vm_type,
                    " - {} Core(s), {}GB of RAM".format(instance_types[vm_type]['core'], instance_types[vm_type]['ram'])
                    if vm_type in instance_types else "",
                ))
                print("State :        {}{}{}".format(
                    Fore.GREEN if inst.state == 'running' else Fore.RED,
                    inst.state,
                    Style.RESET_ALL,
                ))
                print()

    def list_ressources(self):
        """
        Prints out the total ammount of resources used.
        """
        core = 0
        ram = 0.0
        for instance in self.conn.get_only_instances():
            i_t = instance.instance_type
            if i_t in instance_types:
                core += instance_types[i_t]['core']
                ram += instance_types[i_t]['ram']
        print("CPU: {}, RAM: {}".format(core, ram))

    def generate_ansible_hosts_file(self, grain=None, local=False):
        """
        Generate an ansible hosts file (should be stored in /etc/ansible/hosts) according to the grain you define.
        Basically the grain's default is to generate groups for 'env' and 'zone' tags, but you can remove/add some if
        you wish to generate more complex hosts files. Note that this function returns a string (the content of the
        file).

        At the end of the first pass (first for loop) the matrix will be the combination of the different tags.
        An example of what the matrix will look like at the end of the first pass with default arguments :
        {'env': ['prod', 'dev'], 'zone': ['whatever', 'starwatts']}

        This will then generate the following groups :
        [env_prod:children], [env_dev:children], [zone_starwatts:children] and [zone_whatever:children]
        containing respectively the VMs that are matching against those tags.

        :param list grain:
            List of tags to generate the hosts file from
        :param bool local:
            Tells if the inventory file describes an inventory used inside the cloud or on a local machine

        :return: Content of the hosts file
        :rtype: string
        """
        if grain is None:
            grain = ['env', 'zone']
        matrix = {k: [] for k in grain}
        s = ""
        for tags, inst in self.all_vms():
            name = tags.get('name', None)
            if name:
                s += "[{name}]\n{ip}\n\n".format(name=name, ip=name if local else inst.private_ip_address)
            for k, v in matrix.items():
                # For every key inside the matrix (defined by the grain), we check if that key is in the tags of the VM
                # if so, we check if the value of the said tag is not already included in the matrix to avoid duplicates
                if k in tags and tags[k] not in v:
                    matrix[k].append(tags[k])

        for k, v in matrix.items():
            for group in v:
                s += "[{}_{}:children]\n".format(k, group)
                for inst in self.conn.get_instances_by_tags({k: group}):
                    if 'name' in inst.tags:
                        s += "{}\n".format(inst.tags['name'])
                s += "\n"
        return s

    def generate_ssh_config(self, local=False):
        """
        Generate a local or distant ssh config. If local is set to True, then it will also generate a ProxyCommand for
        each entry, forwarding the connections through the bastion.

        :param bool local: Defines whether or not to generate a ProxyCommand for each VM.

        :return: A formatted string representing a full ssh configuration
        :rtype: string
        """
        s = ""
        all_vms = self.all_vms()
        for i, (tags, inst) in enumerate(all_vms):
            name = tags.get('name', None)
            if name and name == 'bastion':
                s += "Host {name}\n\tHostName {ip}\n\tUser root{end}\n".format(
                        name=name,
                        ip=inst.ip_address,
                        end="\n" if i < len(all_vms)-1 else ""
                )
            elif name:
                s += "Host {name}\n\tHostName {ip}\n\tUser root\n".format(
                    name=name,
                    ip=inst.private_ip_address,
                )
                s += "\tProxyCommand ssh -q -W %h:%p bastion\n{end}".format(
                        end="\n" if i < len(all_vms)-1 else ""
                ) if local else "\n"
        return s

    def new_cloud_app(self, application, version, environment, project, instance_type='m1.xlarge', user='root',
                      instance=None, ami=None, debug=False):
        """
        Creates a new CloudApp instance from within the StarWatts instance. Applies the connection of the StarWatts
        instance on the CloudApp.

        :param string application:
            Name of the application that is used. This impacts the way the VM is named and thus the way it is monitored.
            It is advised to use a list of available names instead of using new ones. (e.g : "blender", "guerilla"…)
        :param string version:
            Represents the version of the application to use. This impacts AMI finding and the naming of the machine.
        :param string environment:
            Represents the version of the AMI to use. (e.g : "prod")
        :param string project:
            Name of the project. This may impact the way the script running the application is fetched if you don't
            specify a full path in the copy() method. Default : '/home/starwatts/deploy/{app}/{project}.sh'.
        :param string instance_type:
            A valid instance type. Default : 'm1.xlarge'.
        :param string user:
            A valid username that will be used to connect to the VM. Default : 'root'.
        :param boto.ec2.instance.Instance instance:
            An already existing instance. May be used to save some time when testing things out. Make sure you have the
            correct access rights to this instance. Default : None.
        :param boto.ec2.image.Image ami:
            An existing AMI to use when the VM will be created. If no AMI is supplied, the AMI used when creating the
            machine will be fetched using the API using the application, version and environment parameters. Default :
            None.
        :param bool debug:
            Set to True in case you want to enable debug logging. Default : False.

        :return: A new CloudApp instance.
        :rtype: CloudApp
        """
        return CloudApp(self.conn, application=application, version=version, environment=environment, project=project,
                        instance_type=instance_type, user=user, instance=instance, ami=ami, debug=debug)
