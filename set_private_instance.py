#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import click
from boto.exception import EC2ResponseError
from starwatts import StarWatts


@click.command()
@click.option('--instance_id', type=click.STRING, prompt="Instance ID")
def cli(instance_id):
    s = StarWatts('conf.yml')
    c = s.get_connection()
    try:
        inst_list = c.get_only_instances([instance_id])
    except EC2ResponseError:
        click.secho("This instance could not be found.", fg='red')
        sys.exit(1)
    if len(inst_list) > 0:
        inst = inst_list[0]
    else:
        click.secho("This instance could not be found.", fg='red')
        sys.exit(1)
    click.secho("Instance found, now working...", fg='green')
    log = inst.set_private()
    click.secho("The instance was set to private.", fg='green')
    for t in log:
        click.secho("{} => {}".format(t[0], t[1]), fg='green')

if __name__ == '__main__':
    cli()
