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

from litmus.device.cutter import cutter
from litmus.core.util import call, check_output, find_pattern
import time


class cuttercleware4(cutter):
    """docstring for cuttercleware4"""

    _cindex = None
    _cmd = 'clewarecontrol -d {cport} -c 1'
    _controlcmd = _cmd + ' -as {cindex} {on_off}'
    _getstatuscmd = _cmd + ' -rs {cindex}'

    def __init__(self, *args, **kwargs):
        super(cuttercleware4, self).__init__(*args, **kwargs)
        self._cindex = kwargs['cleware_index']

    def on(self, delay=1):
        """docstring for on"""
        super(cuttercleware4, self).on()

        c = self._controlcmd.format(cport=self._cport,
                                    cindex=self._cindex,
                                    on_off=1)
        out = call(c, shell=True, timeout=10)
        time.sleep(delay)
        return not out

    def off(self, delay=4):
        """docstring for off"""
        super(cuttercleware4, self).off()
        c = self._controlcmd.format(cport=self._cport,
                                    cindex=self._cindex,
                                    on_off=0)
        out = call(c, shell=True, timeout=10)
        time.sleep(delay)
        return not out

    def is_on(self):
        """docstring for is_on"""
        super(cuttercleware4, self).is_on()
        c = self._getstatuscmd.format(cport=self._cport, cindex=self._cindex)
        out = check_output(c, shell=True, timeout=10)

        if find_pattern(pattern=r'On', data=out):
            return True
        else:
            return False
