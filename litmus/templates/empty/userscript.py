#!/usr/bin/env python3
from litmus.core.manager import manager


def main(*args, **kwargs):
    """docstring for main"""

    # init manager instance
    mgr = manager(*args, **kwargs)

    # init working directory
    mgr.init_workingdir()
