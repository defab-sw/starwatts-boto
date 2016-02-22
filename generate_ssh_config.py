#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
from starwatts import StarWatts


@click.command()
@click.argument('output', type=click.File('w'))
@click.option('--local', is_flag=True)
def cli(output, local):
    s = StarWatts('conf.yml')
    output.write(s.generate_ssh_config(local=local))
    output.flush()

if __name__ == '__main__':
    cli()
