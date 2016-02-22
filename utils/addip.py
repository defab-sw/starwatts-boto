#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests


def get_ip():
    """
    Get IP from which the script is run.
    :return: IP address as string
    """
    getip = requests.get('https://api.ipify.org/?format=json')
    data = getip.json()
    return data['ip']


def get_sg_id(connector, instance):
    """
    Get one security groups applied to the given instance.

    :param connector: Active EC2Connection
    :param instance: EC2Object Instance

    :return: EC2Object SecurityGroup
    """
    for sg in connector.get_all_security_groups():
        for inst in sg.instances():
            if inst.id == instance.id:
                return sg


def auth_my_ip(connector, instance):
    """
    Temporary add a rule to allow ssh access to the instance from where the script is run. Remove rule after use.

    :param connector: Active EC2Connection
    :param instance: EC2Object Instance

    :return: ()
    """
    sgroup = get_sg_id(connector, instance)

    sgroup.add_rule(ip_protocol='tcp', from_port=22, to_port=22, cidr_ip=get_ip())
    input()
    sgroup.remove_rule(ip_protocol='tcp', from_port=22, to_port=22, cidr_ip=get_ip())


# def sigint_handler(sig, frame):
#     import signal
#     import sys
#     print("\nGraceful exit")
#     # OPERATION TO CLEANUP
#     sys.exit(1)
#
# Insert following line within main()
# signal.signal(signal.SIGINT, sigint_handler)
