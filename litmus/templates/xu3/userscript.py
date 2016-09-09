#!/usr/bin/env python3
import os
from litmus.core.util import load_yaml
from litmus.core.manager import manager
from litmus.helper.helper import tizen_snapshot_downloader as downloader
from litmus.helper.tests import add_test_helper


def main(*args, **kwargs):

    # init manager instance
    mgr = manager(*args, **kwargs)

    # init working directory
    mgr.init_workingdir()

    # get projectinfo
    project_info = load_yaml('conf.yaml')

    username = project_info['username']
    password = project_info['password']
    binary_urls = project_info['binary_urls']

    # get version from parameter
    try:
        version = kwargs['param'][0]
    except (IndexError, TypeError):
        version = None

    # download binaries from snapshot download server
    filenames = []
    for url in binary_urls:
        filenames.extend(downloader(url=url,
                                    username=username,
                                    password=password,
                                    version=version))

    # get an available device for testing.
    dut = mgr.acquire_dut('xu3', max_retry_times=180)

    # flashing binaries to device.
    dut.flash(filenames)

    # turn on dut.
    dut.on()

    # run helper functions for testing.
    if not os.path.exists('result'):
        os.mkdir('result')

    testcases = load_yaml('tc.yaml')
    add_test_helper(dut, testcases)
    dut.run_tests()

    # turn off dut.
    dut.off()

    # release a device
    mgr.release_dut(dut)
