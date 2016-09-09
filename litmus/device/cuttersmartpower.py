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
import subprocess
from litmus.device.cutter import cutter
from litmus.core.util import call, check_output, find_pattern


class cuttersmartpower(cutter):
    """docstring for cuttersmartpower"""

    _cmd = 'smartpower -d {cport}'
    _controlcmd = _cmd + ' -p'
    _getstatuscmd = _cmd + ' -s 5'
    _max_retry_cnt = 50

    def __init__(self, *args, **kwargs):
        super(cuttersmartpower, self).__init__(*args, **kwargs)

    def on(self, delay=1):
        """docstring for on"""
        super(cuttersmartpower, self).on()

        retry_cnt = 0
        while retry_cnt < self._max_retry_cnt:

            if not self.is_on():
                c = self._controlcmd.format(cport=self._cport)
                call(c, shell=True, stderr=subprocess.DEVNULL, timeout=10)

            if self.is_on():
                time.sleep(delay)
                return True
            else:
                logging.debug('Power on failed. Retry')
                retry_cnt += 1
        else:
                logging.debug('Critical issue on smartpower.')
                time.sleep(delay)
                return False

    def off(self, delay=4):
        """docstring for off"""
        super(cuttersmartpower, self).off()

        retry_cnt = 0
        while retry_cnt < self._max_retry_cnt:

            if self.is_on():
                c = self._controlcmd.format(cport=self._cport)
                call(c, shell=True, stderr=subprocess.DEVNULL, timeout=10)

            if not self.is_on():
                time.sleep(delay)
                return True
            else:
                logging.debug('Power off failed. Retry')
                retry_cnt += 1
        else:
                logging.debug('Critical issue on smartpower.')
                time.sleep(delay)
                return False

    def is_on(self):
        """docstring for is_on"""
        super(cuttersmartpower, self).is_on()
        c = self._getstatuscmd.format(cport=self._cport)
        out = check_output(c, shell=True,
                           stderr=subprocess.DEVNULL, timeout=10)

        if find_pattern(pattern=r'[0-9].[0-9]{3}W', data=out):
            return True
        else:
            return False
