# -*- coding: utf-8 -*-

import os
import time
import logging

import paramiko


class CloudApp:
    """
    Create a new CloudApp. The various arguments are used to define the behavior of this application.

    :param boto.ec2.EC2Connection connection:
        The connection to the cloud provider to use.
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
        correct access rights to this instance.
    :param boto.ec2.image.Image ami:
        An existing AMI to use when the VM will be created. If no AMI is supplied, the AMI used when creating the
        machine will be fetched using the API using the application, version and environment parameters.
    :param bool debug:
        Set to True in case you want to enable debug logging.

    :return: A new CloudApp instance.
    :rtype: CloudApp
    """
    workdir = '/home/starwatts/jobs/'

    def __init__(self, connection, application, version, environment, project, instance_type='m1.xlarge', user='root',
                 instance=None, ami=None, debug=False):
        if debug:
            logging.basicConfig(level=logging.DEBUG)

        # API attributes
        self.connection = connection

        # AMI and VM attributes
        self.application = application
        self.version = version
        self.environment = environment
        self.project = project
        self.user = user
        self.instance_type = instance_type
        self.ami = ami
        if instance is not None:
            self.instance_name = instance.tags.get('name')
        else:
            self.instance_name = "node_{}_{}".format(self.application, self.project)
        self.instance = instance

        # SSH connection and command attributes
        self.connected = False
        self.errors = list()
        self.ssh_sock = None
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client._policy = paramiko.WarningPolicy()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def fetch_ami(self):
        """
        Fetches the AMI according to the application name, version and environment. Called automatically when creating
        the machine if no AMI object was supplied when creating this CloudApp.

        :raises ValueError: If no AMI matched.
        :raises ValueError: If multiple AMIs matched.
        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        ami_filter = '{}-{}-{}'.format(self.application, self.version, self.environment)
        imgs = self.connection.get_all_images(filters={'name': ami_filter})
        if not imgs:
            raise ValueError("AMI wasn't found for {}.".format(ami_filter))
        if len(imgs) > 1:
            raise ValueError("Found multiple AMIs for {}.".format(ami_filter))
        self.ami = imgs[0]
        return self

    def fetch_application_id(self):
        """
        Fetch the application id for the specified application.
        :return:
        """
        files = self.connection.get_only_instances(filters={'tag:name': 'files', 'instance-state-name': 'running'})[0]
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(files.private_ip_address, username='root')
        (stdin, stdout, stderr) = client.exec_command("cat {}/{}/index".format(self.workdir, self.application))
        print(stdout)
        client.close()

    def through(self, host, user='root'):
        """
        Defines a proxy command to rebound on the host.
        This method is actually unsafe to use and will cause an SSH Banner Error. This library can't work through a
        proxy

        :param string host: Either a valid name stored in ~/.ssh/config or a valid IP address.
        :param string user: A valid user for the host. Default : 'root'.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        ssh_conf_file = os.path.expanduser("~/.ssh/config")
        try:
            ssh_conf = paramiko.SSHConfig()
            with open(ssh_conf_file) as f:
                ssh_conf.parse(f)
            if host in ssh_conf.get_hostnames():
                host_conf = ssh_conf.lookup(host)
                user = host_conf.get('user', 'root')
                host = host_conf.get('hostname')
            else:
                print("Could not find host {} in {}. Using raw hostname.".format(host, ssh_conf_file))
        except FileNotFoundError as e:
            print("Could not load {} : {}. Using raw hostname.".format(ssh_conf_file, e))

        # "ssh -W %h:%p {}@{}" doesn't create an entry in the logs. "ssh {}@{} nc %h %p"
        # Actually connects to name (causing an entry in the logs)
        print("ssh {}@{} nc {} 22".format(user, host, self.instance.private_ip_address))
        self.ssh_sock = paramiko.ProxyCommand("ssh {}@{} nc {} 22".format(user, host, self.instance.private_ip_address))
        return self

    def wait(self, seconds):
        """
        Waits for a certain time. Can be used in chained methods.

        :param int seconds: Number of seconds to wait.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        time.sleep(seconds)
        return self

    def connect(self, key_filename=None, use_key=True):
        """
        Connect to the server and keep the connection open.

        :param string key_filename:
            Path to the correct .pem file. Defaults to ~/.ssh/config/{project_name}.pem
        :param bool use_key:
            Whether or not to use the default key (or the one given as argument). Becomes handy if your public key is
            already in the authorized hosts.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        if not self.connected:
            if key_filename is None and use_key:
                key_filename = os.path.expanduser("~/.ssh/config/{}.pem".format(self.project))
            if not use_key:
                key_filename = None
            self.ssh_client.connect(hostname=self.instance.private_ip_address, username=self.user,
                                    key_filename=key_filename, sock=self.ssh_sock)
            self.connected = True
        return self

    def disconnect(self):
        """
        Closes the ssh connection if it was previously open.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        if self.connected:
            self.ssh_client.close()
            self.connected = False
        return self

    def command(self, command, show_stderr=True, show_stdout=True, timeout=None):
        """
        Runs a command on the remote host.

        :param string command:
            Command to execute.
        :param bool show_stderr:
            Show the stderr. Default : True.
        :param bool show_stdout:
            Show the stdout. Default : True.
        :param int timeout:
            Defines a timeout, raises an error if the command doesn't complete in the given delay. Default : None.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        if not self.connected:
            print("Currently not connected to the VM. Run self.connect() first.")
            return self

        (stdin, stdout, stderr) = self.ssh_client.exec_command(command, timeout=timeout)
        print("Exit Status Code : {}".format(stdout.channel.recv_exit_status()))
        if show_stdout:
            print("Stdout :")
            for line in stdout.readlines():
                print(line)
        if show_stderr:
            print("Stderr :")
            for line in stderr.readlines():
                self.errors.append(line)
                print(line)
        return self

    def create(self, terminate_on_shutdown=True):
        """
        Starts the associated VM, with the correct AMI, instance type and tags.

        :param bool terminate_on_shutdown:
            Determines whether or not to terminate the VM when it shutdowns or not. Default : True.

        :return: This instance. Allows to chain method calls.
        :rtype: CloudApp
        """
        if self.ami is None:
            print("Retrieving AMI for {} version {} in {} environment... ".format(
                self.application, self.version, self.environment
            ), end='')
            self.fetch_ami()
            print("Found {} ({})".format(self.ami.name, self.ami.id))
        if self.instance is not None:
            print("This CloudApp has already an associated instance.")
            return self
        self.instance = self.connection.quick_instance(
            name=self.instance_name, image=self.ami.id, instance_type=self.instance_type,
            env_tag=self.environment, os_tag='debian', zone_tag='starwatts', sg_id='sg-9b5adf25',
            terminate_on_shutdown=terminate_on_shutdown,
        )
        self.instance.wait_for('running')
        return self

    def terminate(self):
        """
        Terminates the VM.

        :return: This instance. Allows to chain method calls.
        :rtype: CloudApp
        """
        if self.instance is not None:
            self.instance.terminate()
            return self
        else:
            print("This CloudApp doesn't have an associated instance. Can't terminate.")
            return self

    def copy(self, src_vm, src_user='root', src_path=None, dest=workdir):
        """
        Copy a specific file from a remote server to this host.

        :param string src_vm:
            IP or name (can be defined in ~/.ssh/config) of the remote VM on which the file is fetched.

        :param string src_path:
            Absolute path on the remote VM of the file to fetch. If the argument isn't specified, the default path will
             be applied (/home/starwatts/deploy/{app}/{project}.sh).

        :param string src_user: Remote VM user. Default : 'root'.
        :param string dest: Destination directory in which to copy the file. Default : workdir.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        if src_path is None:
            src_path = '/home/starwatts/deploy/{app}/{project}.sh'.format(app=self.application, project=self.project)
        copy_cmd = "scp {src_user}@{src_vm}:{src_path} {dest}".format(
            src_user=src_user,
            src_vm=src_vm,
            src_path=src_path,
            dest=dest,
        )
        self.command(copy_cmd)
        return self

    def run(self):
        """
        Runs the script which is located in the workdir and that is named according to the project. For example :
        /home/starwatts/jobs/project1.sh

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        script_fullpath = os.path.join(self.workdir, "{}.sh".format(self.project))
        self.command("nohup {script}&".format(script_fullpath))
        return self

    def setup_hostname(self):
        """
        Setup the hostname of the machine. Must be called at some point because the monitoring of this VM depends on
        the hostname being unique.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        if not self.connected:
            print("Connection is closed. Run self.connect() first.")
            return
        self.command('echo "{hostname}" > /etc/hostname'.format(hostname=self.instance_name))
        self.command('hostname -F /etc/hostname')
        self.command('sed -i -e "s/node1-blender/{hostname}/g" /etc/hosts'.format(hostname=self.instance_name))
        return self

    def setup_monitoring(self):
        """
        Setup the monitoring on the machine. Must be called after the setup_hostname method otherwise it will be
        monotored with the wrong id.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        if not self.connected:
            print("Connection is closed. Run self.connect() first.")
            return
        self.command("systemctl enable zabbix-agent")
        self.command("service zabbix-agent restart")
        return self

    def setup(self):
        """
        Successive calls to setup_hostname and setup_monitoring.

        :return: This instance. Allows to chain methods.
        :rtype: CloudApp
        """
        self.setup_hostname()
        self.setup_monitoring()
        return self

    def fullchain(self):
        """
        Simple example on how to use this object
        """
        self.create().wait(5).connect().setup().copy('files').run().disconnect()
