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

import time
import logging
from litmus.device.device import device
from litmus.core.util import check_output, find_pattern
from litmus.core.util import convert_single_item_to_list
from litmus.core.util import call


class devicemock(device):
    """
    Litmus device class.
    User can control device in topology by this class methods.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._name = kwargs['deviceid']
        self._id = self._find_device_id()

        # init a cutter instance.
        self._manager = kwargs['manager']

    def _release(self):
        """docstring for _release"""
        pass

    def _find_device_id(self):
        """docstring for _find_device_id"""
        self.refresh_sdb_server()
        outs = check_output(['sdb', 'devices'], timeout=10)
        pattern = '.*List of devices attached \n([a-zA-Z0-9]*).*device.*'
        found = find_pattern(pattern, outs, groupindex=1)
        if found:
            return found

    # public methods.
    def get_id(self):
        """
        Return the id of acquired device.
        Device instance uses this id for sdb connection.

        Example:
            >>> dut = mgr.acquire_dut('xu3')
            >>> dut.get_id()
            'XU3_001'

        :returns str: device id
        """
        return self._id

    def on(self, powercut_delay=2):
        """
        Turn on the device acquired.

        :param float powercut_delay: power-cut delay for cutter
        """
        logging.debug('turn on device {}'.format(self.get_name()))

        self.refresh_sdb_server()
        if self._find_device_id() == self.get_id():
            self._sdb_root_on()
            self.run_cmd('reboot -f')
        time.sleep(60)
        self.refresh_sdb_server()
        self._sdb_root_on()

    def off(self, powercut_delay=2):
        """
        Trun off the device acquired.

        :param float powercut_delay: power-cut delay for cutter
        """
        logging.debug('turn off device {}'.format(self.get_name()))

    def thor(self, filenames):
        """docstring for thor"""
        cmd = 'lthor'
        filenames = convert_single_item_to_list(filenames)
        for l in filenames:
            cmd += ' {}'.format(l)
        logging.debug(cmd)
        ret = call(cmd.split(), timeout=600)
        if ret:
            raise Exception('Thor error.')

    def heimdall(self, filenames,
                 partition_bin_mappings={'BOOT': 'zImage',
                                         'ROOTFS': 'rootfs.img',
                                         'USER': 'user.img',
                                         'SYSTEM-DATA': 'system-data.img'}):
        """docstring for heimdall"""
        filenames = convert_single_item_to_list(filenames)
        tar_cmd = ['tar', 'xvfz']
        for l in filenames:
            tar_cmd.append(l)
        logging.debug(tar_cmd)
        call(tar_cmd, timeout=30)

        heimdall_cmd = ['heimdall', 'flash']
        for key, elem in partition_bin_mappings.items():
            heimdall_cmd.append('--{}'.format(key))
            heimdall_cmd.append(elem)
        logging.debug(heimdall_cmd)

        ret = call(heimdall_cmd, timeout=600)
        if ret:
            raise Exception('Heimdall error.')

    def flash(self, filenames, flasher='lthor', waiting=5,
              partition_bin_mappings={'BOOT': 'zImage',
                                      'ROOTFS': 'rootfs.img',
                                      'USER': 'user.img',
                                      'SYSTEM-DATA': 'system-data.img'}):
        """
        Flash binaries to device.
        This function turn on device and turn off device automatically.

        :param dict filenames: filename string or dict
        :param func flasher: wrapper function of external flashing tool
        :param float waiting: waiting time to acquire cdc_acm device
        :param dict partition_bin_mappings: partition table for device which use heimdall flasher

        Example:
            >>> dut.flash(['boot.tar.gz','platform.tar.gz'])
            >>> or
            >>> dut.flash('platform.tar.gz')

        """
        logging.debug('flash binaries to device : {}'.format(filenames))

        self.refresh_sdb_server()

        if not filenames:
            raise Exception('There\'s no file to flash.')
        try:
            self._sdb_root_on()
            self.run_cmd('reboot -f download', timeout=10)
            time.sleep(5)
            if flasher == 'lthor':
                self.thor(filenames=filenames)
            elif flasher == 'heimdall':
                self.heimdall(filenames=filenames,
                              partition_bin_mappings=partition_bin_mappings)
        except (Exception, KeyboardInterrupt) as e:
            logging.debug(e)
            raise Exception('Can\'t flash files : {}.'.format(filenames))

    def refresh_sdb_server(self):
        """docstring for refresh_sdb_server"""
        call('sdb kill-server; sdb start-server', shell=True, timeout=10)
        time.sleep(1)
