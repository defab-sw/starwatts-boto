.. StarWatts documentation master file, created by
   sphinx-quickstart on Thu Feb  4 14:15:42 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to StarWatts's documentation!
=====================================

.. toctree::
   :maxdepth: 4

   StarWatts <starwatts>
   CloudApp <cloudapp>
   EC2 Helpers <helpers>

This is the documentation of the StarWatts library. The main goal of this documentation is to have an always up-to-date
API reference for this lib as well as use cases and examples.

The following code block is an example of how to use this library to interact with the API. It uses the StarWatts class,
as well as the helper functions that are applied to the boto objects.

`See Coverage <htmlcov/index.html>`_

.. code-block:: pycon

   >>> from starwatts import StarWatts
   >>> s = StarWatts('conf.yml')
   >>> c = s.get_connection()
   >>> new = c.quick_instance('test', 'ami-6f800eea', 't1.micro')
   Using AMI ami-6f800eea : Debian 8 Python Proxy
   Tags : {'privacy': 'true', 'os': 'debian', 'name': 'test', 'env': 'dev', 'zone': 'defab'}
   >>> new.wait_for('running')
   Waiting for Instance:i-xxxxxxxx to be in running state... Done.
   >>> s.pretty_report(name='test')
   VM :           test
   OS :           debian
   Env :          dev
   Zone :         defab
   Private IP :   xx.xx.xx.xx
   Private Only : true
   Type :         t1.micro - 1 Core(s), 0.6GB of RAM
   State :        running

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
