#!/usr/bin/env python3
# Copyright 2015-2016 Samsung Electronics Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import shutil
import hashlib
import logging
import fasteners

from threading import Lock
from datetime import datetime
from configparser import RawConfigParser
from litmus.device.device import device
from litmus.core.util import copy, init_logger
from litmus import _duts_, _path_for_locks_, _tmpdir_


class _singleton(object):
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class manager(_singleton):
    """
    Litmus manager class.

    This class manages litmus projects and devices.
    User can acquire/release devices and
    manage working directory from this class.
    """
    _comment = '''====================================================
Init litmus manager :
Lightweight test manager for tizen automated testing
===================================================='''
    _all_devices = []
    _duts = []
    _path_for_locks = _path_for_locks_
    _tmpdir = _tmpdir_
    _project_name = None
    _project_path = None
    _backup_cwd = None
    _workingdir = None
    _remove_workingdir_at__del__ = False

    def __init__(self, *args, **kwargs):
        super(manager, self).__init__()
        self.args = args
        self.kwargs = kwargs
        logging.debug(self._comment)

        self._load_configs(_duts_)
        if 'project_name' in self.kwargs:
            self._project_name = self.kwargs['project_name']
        if 'project_path' in self.kwargs:
            self._project_path = self.kwargs['project_path']
        else:
            self._project_path = os.getcwd()
        if 'workingdir' in self.kwargs and self.kwargs['workingdir']:
            self._workingdir = os.path.abspath(self.kwargs['workingdir'])
        if 'verbose' in self.kwargs and self.kwargs['verbose']:
            init_logger()

    def __del__(self):
        if self._backup_cwd:
            os.chdir(self._backup_cwd)
        if self._workingdir and self._remove_workingdir_at__del__:
            shutil.rmtree(self._workingdir)

    def acquire_dut(self, devicetype,
                    max_retry_times=10, retry_delay=10):
        """
        Acquire an available device for testing.

        :param str devicetype: device type
        :param int max_retry_times: max retry times for device acquisition
        :param float retry_delay: delay time for each device acquisition retry

        Example:
            >>> mgr = manager()
            >>> dut = mgr.acquire_dut('xu3')

        :returns device: acquired device instance
        """
        logging.debug('===============Acquire an available DUT===============')

        candidates = [dev for dev in self._all_devices
                      if dev['dev_type'] == devicetype]

        if candidates:
            for times in range(0, max_retry_times):
                for dev in candidates:
                    if not dev['ilock'].acquired:
                        gotten_tlock = dev['tlock'].acquire(blocking=False)
                        gotten_ilock = dev['ilock'].acquire(blocking=False)
                        try:
                            os.chmod(dev['ilock'].path, 0o664)
                        except PermissionError:
                            logging.debug('Can\'t change lock file permission')

                        # if acquire tlock and ilock, assign a device.
                        if gotten_tlock and gotten_ilock:
                            dut = device.create(manager=self, **dev)
                            self._duts.append(dut)
                            logging.debug('{} is assigned.'
                                          .format(dut.get_name()))
                            return dut
                        # if acquire tlock only then release it for next time.
                        elif gotten_tlock and not gotten_ilock:
                            dev['tlock'].release()
                else:
                    logging.debug('All {}s are busy. Wait {} seconds.'
                                  .format(devicetype, retry_delay))
                    time.sleep(retry_delay)
        raise Exception('{} device is not available.'.format(devicetype))

    def release_dut(self, dut=None):
        """
        Release acquired devices under test.

        If dut variable is None then all acquired devices will be released.

        :param device dut: device instance

        Example:
            >>> mgr.release_dut(dut)
            >>> or
            >>> mgr.release_dut()

        """
        # TODO: self._duts.remove(dev) doesn't delete device instance.
        # release all _duts if dut param is None
        if not dut:
            for dev in self._duts:
                dev.kwargs['tlock'].release()
                dev.kwargs['ilock'].release()
                dev._release()
            self._duts = []
        # if dut param is not None, release the dut
        else:
            dev = next((d for d in self._duts
                       if d.get_name() == dut.get_name()),
                       None)
            if dev:
                dev.kwargs['tlock'].release()
                dev.kwargs['ilock'].release()
                dev._release()
                self._duts.remove(dev)

    def get_all_acquired_duts(self):
        """
        Return a list of all acquired devices

        Example:
            >>> mgr.get_all_acquired_duts()
            [litmus.device.devicexu3.devicexu3 object at 0x7fb39c94ebe0>]

        :returns list: all acquired devices
        """
        return self._duts

    def get_workingdir(self):
        """
        Return a working directory of the litmus project.

        Example:
            >>> mgr.get_workingdir()
            '/home/user/Workspace/test'

        :returns str: working directory
        """
        return self._workingdir

    def init_workingdir(self, workingdir=None):
        """
        Initialize a working directory.

        If workingdir param is None, manager creates a temporary directory
        to use as a workingdir. And manager deletes this temporary directory
        when test has finished.

        If workingdir param is not None, manager uses this directory
        as a workingdir.

        And then, Manager copies all files under litmus project directory
        to working directory.

        :param str workingdir: working directory path

        Example:
            >>> mgr.init_workingdir()
            >>> mgr.get_workingdir()
            '/tmp/82a41636dd39fe6fee4ffb80a7112ee131af8946'
            >>> or
            >>> mgr.init_workingdir(workingdir='.')
            >>> mgr.get_workingdir()
            '/home/user/Workspace/test'
        """
        if workingdir:
            self._workingdir = os.path.abspath(workingdir)
        try:
            self._backup_cwd = os.getcwd()
            if self._workingdir:
                os.chdir(self._workingdir)
            else:
                workingdir_name = str((hashlib.sha1(str(datetime.now())
                                              .encode()).hexdigest()))
                workspace_path = os.path.join(self._tmpdir, workingdir_name)
                os.mkdir(workspace_path)
                os.chdir(workspace_path)
                self._workingdir = workspace_path
                self._remove_workingdir_at__del__ = True
            logging.debug('working dir: {}'.format(self._workingdir))
            logging.debug('copy all files in project path to workingdir')
            copy(self._project_path, os.curdir)
        except Exception as e:
            logging.debug(e)
            raise Exception('Can\'t init workingdir.')

    def _load_configs(self, configpath):
        """docstring for _load_configs"""
        configparser = RawConfigParser()
        configparser.read(configpath)

        for section in configparser.sections():
            items = dict(configparser.items(section))
            items['deviceid'] = section

            # Interproces Lock and Thread Lock
            ilock_filename = os.path.join(self._path_for_locks,
                                          items['deviceid'])
            items['tlock'] = Lock()
            items['ilock'] = fasteners.InterProcessLock(ilock_filename)

            # Append items
            self._all_devices.append(items)

        # Add mock device
        mock_deviceid = 'MOCK_001'
        mock_ilock_filename = os.path.join(self._path_for_locks, mock_deviceid)
        mock = {'deviceid': mock_deviceid,
                'dev_type': 'mock',
                'tlock': Lock(),
                'ilock': fasteners.InterProcessLock(mock_ilock_filename)}
        self._all_devices.append(mock)
