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
from threading import Thread
from litmus.device.device import device
from litmus.core.util import find_pattern
from litmus.core.exceptions import BootError


class deviceartik10(device):
    """docstring for device"""

    _booting_time = 60
    _pattern_shellprompt = r'root.*> .*'
    _pattern_bootprompt = r'ARTIK.*# .*'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._name = kwargs['devicename']

        self._open_uart()
        self._manager = kwargs['manager']

    def _release(self):
        """docstring for _release"""
        self._close_uart()

    def _wait_uart_shell_login_prompt(self):
        """docstring for _wait_uart_shell_login_prompt"""
        super(deviceartik10, self)._wait_uart_shell_login_prompt()

    def _set_sdb_deviceid(self):
        """docstring for _set_sdb_deviceid"""
        usb0_path = b'/sys/class/usb_mode/usb0'
        pattern = '.*{0}'.format(self.get_id())

        def set_serialnumber(deviceid):
            """docstring for set_serialnumber"""
            self._write_uart(b''.join([b'echo 0 > ', usb0_path, b'/enable']))
            time.sleep(0.3)
            self._write_uart(b''.join([b'echo ',
                                       b'-n ',
                                       deviceid,
                                       b' > ', usb0_path,
                                       b'/iSerial']))
            time.sleep(0.3)
            self._write_uart(b'direct_set_debug.sh --sdb-set')
            time.sleep(0.5)

        def get_serialnumber():
            """docstring for get_serialnumber"""
            self._write_uart(b''.join([b'cat ', usb0_path, b'/enable']))
            time.sleep(0.3)
            self._write_uart(b''.join([b'cat ', usb0_path, b'/iSerial']))
            time.sleep(0.3)
            return self._read_uart(1000)

        retrycnt = 0
        while retrycnt < 10:
            set_serialnumber(deviceid=self.get_id().encode())
            serialnumber = get_serialnumber()
            if find_pattern(pattern, serialnumber):
                return
            retrycnt += 1
        else:
            raise Exception('Can\'t configure sdb deviceid')

    def _reboot(self):
        """docstring for _reboot"""
        status = self._current_uart_status()

        if status == 'LOGGED_IN':
            self._write_uart(b'reboot')
            time.sleep(3)
        elif status == 'BOOT_PROMPT':
            self._write_uart(b'reset')
            time.sleep(3)
        elif status == 'NOT_LOGGED_IN':
            self._wait_uart_shell_login_prompt()
            self._login_uart_shell()
            self._write_uart(b'reboot')
            time.sleep(3)

    def _current_uart_status(self):
        """docstring for _current_uart_status"""
        self._flush_uart_buffer()
        for loop in range(3):
            self._write_uart(b'')
        readdata = self._read_uart(500)
        if find_pattern(self._pattern_bootprompt, readdata):
            return 'BOOT_PROMPT'
        if find_pattern(self._pattern_shellprompt, readdata):
            return 'LOGGED_IN'
        else:
            return 'NOT_LOGGED_IN'

    def _enter_download_mode(self, cmd, power_cut_delay=1, thread_param=10):
        """docstring for _enter_download_mode"""
        t = Thread(target=self._thread_for_enter_download_mode,
                   args=(cmd, thread_param, ))
        status = self._current_uart_status()
        if status == 'NOT_LOGGED_IN':
            self._wait_uart_shell_login_prompt()
            self._login_uart_shell()
        t.start()
        self._reboot()
        t.join()

    def on(self, powercut_delay=3):
        """
        Turn on the device acquired.

        :param float powercut_delay: power-cut delay for cutter
        """
        logging.debug('=================Turn on device {}=================='
                      .format(self.get_name()))
        retry_cnt = 0
        time.sleep(powercut_delay)
        while retry_cnt <= self._max_attempt_boot_retry:
            try:
                self._reboot()
                self._wait_uart_shell_login_prompt()
                self._login_uart_shell()
                self._set_sdb_deviceid()
                self._attach_sdb()
                self.sdb_root_on()
                return
            except KeyboardInterrupt:
                raise Exception('Keyboard interrupt.')
            except Exception as e:
                logging.debug(e)
                retry_cnt += 1
        else:
            raise BootError('Cant\'t turn on dut.')

    def off(self, powercut_delay=2):
        """
        Trun off the device acquired.

        :param float powercut_delay: power-cut delay for cutter
        """
        logging.debug('off function is not supported for Artik device')
