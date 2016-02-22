# -*- coding: utf-8 -*-

import sys


def query_yes_no(question, default="yes"):
    """
    Ask a yes/no question via input() and return the answer.

    :param string question:
        Question to ask to the user
    :param string default:
        Default value in case of enter without input. Possible values are 'yes', 'no', or None. If None is selected,
        then the user has to type an explicit choice.
    :return: True if the answer is yes, False otherwise
    :rtype: bool
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
