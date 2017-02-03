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
from litmus.core.util import call


class devicestandalone(device):
    """
    Litmus device class.
    User can control device in topology by this class methods.
    """

    _booting_time = 60

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._name = kwargs['devicename']
        if 'serialno' in kwargs:
            self._id = kwargs['serialno']
        else:
            self._id = self._find_device_id()

        if 'usbid' in kwargs:
            self._usbid = kwargs['usbid']
        else:
            self._usbid = None

        self._manager = kwargs['manager']

    def _release(self):
        """docstring for _release"""
        pass

    def _find_device_id(self):
        """docstring for _find_device_id"""
        self.start_sdb_server()
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

    def on(self, booting_time=None):
        """
        Turn on the device acquired.

        :param float powercut_delay: power-cut delay for cutter
        """
        logging.debug('=================Turn on device {}=================='
                      .format(self.get_name()))

        self.start_sdb_server()
        if self.is_on():
            self.sdb_root_on()
            self.run_cmd('reboot -f', timeout=20)
        wait_for_boot = booting_time if booting_time else self._booting_time
        for loop in range(wait_for_boot):
            logging.debug('Wait {} seconds......'
                          .format(wait_for_boot - loop))
            time.sleep(1)
        self.start_sdb_server()
        self.sdb_root_on()

    def off(self, powercut_delay=2):
        """
        Trun off the device acquired.

        :param float powercut_delay: power-cut delay for cutter
        """
        logging.debug('off function is not supported for standalone device')

    def flash(self, filenames, flasher='lthor', waiting=5,
              partition_bin_mappings={'BOOT': 'zImage',
                                      'ROOTFS': 'rootfs.img',
                                      'USER': 'user.img',
                                      'SYSTEM-DATA': 'system-data.img'}):
        """
        Flash binaries to device.
        This function turn on device and turn off device automatically.

        :param dict filenames: filename string or dict
        :param string flasher: external flashing tool name
        :param float waiting: waiting time to acquire cdc_acm device
        :param dict partition_bin_mappings: partition table for device which use heimdall flasher

        Example:
            >>> dut.flash(['boot.tar.gz','platform.tar.gz'])
            >>> or
            >>> dut.flash('platform.tar.gz')

        """
        logging.debug('================Flash binaries to device============')
        logging.debug(filenames)

        self.start_sdb_server()

        if not filenames:
            raise Exception('There\'s no file to flash.')
        try:
            self.sdb_root_on()
            self._acquire_global_lock()
            self.run_cmd('reboot -f download', timeout=20)
            time.sleep(waiting)
            if flasher == 'lthor':
                if self._usbid == None:
                busid = self._find_usb_busid()
                else:
                    busid = self._usbid
                self._release_global_lock()
                self._lthor(filenames=filenames, busid=busid)
            elif flasher == 'heimdall':
                (busaddr, devaddr) = self._find_usb_bus_and_device_address()
                self._release_global_lock()
                self._heimdall(filenames=filenames,
                               busaddr=busaddr,
                               devaddr=devaddr,
                               partition_bin_mappings=partition_bin_mappings)
        except (Exception, KeyboardInterrupt) as e:
            self._release_global_lock()
            logging.debug(e)
            raise Exception('Can\'t flash files : {}.'.format(filenames))

    def refresh_sdb_server(self):
        """docstring for refresh_sdb_server"""
        call('sdb kill-server; sdb start-server', shell=True, timeout=10)
        time.sleep(1)

    def start_sdb_server(self):
        """docstring for start_sdb_server"""
        call('sdb start-server', shell=True, timeout=10)
        time.sleep(1)
