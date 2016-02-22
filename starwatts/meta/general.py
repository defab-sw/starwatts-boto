# -*- coding: utf-8 -*-

import time
import datetime


def wait_for(self, state, seconds=1, timeout=300):
    """
    Waits until the object is in the desired state.

    :param self:
        Any Object that has the 'update' method
    :param string state:
        The state in which the instance should be before returning (example : 'running', 'stopped', etc...)
    :param int seconds:
        Number of seconds to wait between each calls to the update method. Default : 1.
    :param int timeout:
        Number of seconds before the functions throws an exception. Default : 300.
    """
    limit = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    print("Waiting for {} to be in {} state... ".format(self, state), end="")
    while self.update() != state:
        time.sleep(seconds)
        if datetime.datetime.now() > limit:
            raise TimeoutError("Operation took too long to finish. Last known state was {}.".format(self.update()))
    print("Done.")
