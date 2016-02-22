# -*- coding: utf-8 -*-
import sys
import paramiko


def paramiko_connect(host):
    client = paramiko.SSHClient()
    client._policy = paramiko.WarningPolicy()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_config = paramiko.SSHConfig()
    user_config_file = os.path.expanduser("~/.ssh/config")
    try:
        with open(user_config_file) as f:
            ssh_config.parse(f)
    except FileNotFoundError:
        print("{} file could not be found. Aborting.".format(user_config_file))
        sys.exit(1)
    cfg = {'hostname': options['hostname'], 'username': options["username"]}

    user_config = ssh_config.lookup(cfg['hostname'])
    for k in ('hostname', 'username', 'port'):
        if k in user_config:
            cfg[k] = user_config[k]

    if 'proxycommand' in user_config:
        cfg['sock'] = paramiko.ProxyCommand(user_config['proxycommand'])

    return client.connect(**cfg)
