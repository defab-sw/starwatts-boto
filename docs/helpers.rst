Helpers Applied to the EC2 Boto Library
=======================================

This page presents the various methods we apply to the standard EC2 objects of the Boto library when importing the
StarWatts object (or anything that comes from the starwatts package). **You have to import something from the starwatts
package to use those helpers**.

Applied on boto.ec2.instance.Instance
-------------------------------------

.. automodule:: starwatts.meta.instance
    :members:

Applied on boto.ec2.EC2Connection
---------------------------------

.. automodule:: starwatts.meta.connection
    :members:

Applied on boto.ec2.volume.Volume
---------------------------------

.. automodule:: starwatts.meta.volume
    :members:

Applied on multiple types
-------------------------
These functions are applied to many types in the boto library.

.. automodule:: starwatts.meta.general
    :members:
