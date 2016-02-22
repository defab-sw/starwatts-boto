# Starwatts-boto

This document is a very basic tutorial on how to get started with this library.
Please refer to the docs folder and generate the said documentation using
`cd docs && make html`. This file won't cover all the use cases
you may encounter.

This repository is a set of helper tools to use the Outscale cloud.
As for now it mainly feature small helper functions that allows us to do
operations that can't be done via the web interface.

As a starter you'll need API credentials for the Outscale Cloud (Access Key and
Secret Key). It is advised to put those inside a file named `conf.yml` at the
root of this repository. Never version this file.

```yml
access_key: "..."
secret_key: "..."
```

Then you need to setup a virtual environment as it will greatly simplify the
following steps.

```bash
$ pyvenv-3.5 env
$ source env/bin/activate # or activate.fish if you're running fish
(env) $ pip install -r requirements.txt
```

Here is an example of getting a list of all the VMs with and without filtering.

```python
>>> from starwatts import StarWatts
>>> s = StarWatts('conf.yml')
>>> s.pretty_report()
...
>>> s.pretty_report(zone='starwatts')
...
>>> s.pretty_report(name='files')
```

When you import the StarWatts object (or anything from the starwatts package),
methods will be added to the EC2Objects related to operations we do often.
Here are a few examples :

```python
>>> from starwatts import StarWatts
>>> s = StarWatts('conf.yml')
>>> c = s.get_connection()  # Alternatively : c = s.conn
>>> test_instance = c.get_vm_by_tags({'name': 'test_vm'})[0]
>>> test_instance.stop()
>>> test_instance.wait_for('stopped')
Waiting for Instance:i-xxxxxxxx to be in stopped state... Done.
>>> test_instance.start()
>>> test_instance.wait_for('running')
Waiting for Instance:i-xxxxxxxxx to be in running state... Done.
>>> test_instance.get_all_attached_volumes()
[Volume:vol-xxxxxxxx]
>>> test_instance.get_all_security_groups()
[SecurityGroup:xxx]
>>> test_instance.set_private()
Waiting for Instance:i-xxxxxxxx to be in stopped state... Done.
Fetching security groups... Done.
Creating image... Done.
Waiting for Image:ami-xxxxxxxxxx to be in available state... Done.
Creating new private instance... Done.
Removing image... Done.
[('old_ip', 'new_ip')]
```
