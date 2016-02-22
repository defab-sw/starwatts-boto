# -*- coding: utf-8 -*-

from starwatts import StarWatts


def dummytest():
    """
    Code posted on the github issue regarding the SSH Banner Error on the paramiko github.
    https://github.com/paramiko/paramiko/issues/673
    """
    import os
    import paramiko
    import logging

    logging.basicConfig(level=logging.DEBUG)

    # Loading ssh configuration to get the IP and user of the desired host (here 'bastion')
    cfg = paramiko.SSHConfig()
    with open(os.path.expanduser("~/.ssh/config")) as f:
        cfg.parse(f)
    host_cfg = cfg.lookup('bastion')
    sock = paramiko.ProxyCommand("ssh {}@{} nc 10.8.9.160 22".format(host_cfg.get('user'), host_cfg.get('hostname')))
    sock.settimeout(30)
    # Sock stays open until a client tries to use it (or the program exits)

    # Client Setup
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Connect and execute command
    # The following line hangs for 15 seconds (increase with banner_timeout argument) and raises an SSHError
    client.connect("10.8.9.160", username='root', sock=sock)
    (stdin, stdout, stderr) = client.exec_command("echo 'Hello World !'")
    for line in stdout.readlines():
        print(line)
    client.close()


def main():
    s = StarWatts("conf.yml")
    test_instance = s.conn.get_instance_by_tags({'name': 'node_blender_job0'})[0]
    app = s.new_cloud_app("blender", "2.72", "prod", "job0", instance=test_instance, debug=True)

    # Direct connection works
    app.ssh_client.connect("171.33.90.69", username='root')
    (stdin, stdout, stderr) = app.ssh_client.exec_command("echo 'Hello World !'")
    for line in stdout.readlines():
        print(line)
    app.ssh_client.close()

    # Proxy connection doesn't
    (stdin, stdout, stderr) = app.through('bastion').connect(use_key=False).command("echo 'Hello World !'")
    for line in stdout.readlines():
        print(line)
    app.disconnect()

if __name__ == '__main__':
    dummytest()
