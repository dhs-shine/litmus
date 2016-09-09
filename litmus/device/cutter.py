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

import abc
from litmus.core.util import create_instance


class cutter(object):
    """docstring for cutter"""

    __metaclass__ = abc.ABCMeta
    _ctype = None
    _cport = None

    def __init__(self, *args, **kwargs):
        super(cutter, self).__init__()
        self._ctype = kwargs['cutter_type']
        self._cport = kwargs['cutter_port']

    @classmethod
    def create(self, *args, **kwargs):
        """
        Create a cutter instance.
        """
        clsname = 'cutter' + kwargs['cutter_type']
        return create_instance(clsname,
                               'litmus.device',
                               *args,
                               **kwargs)

    @abc.abstractmethod
    def on(self, delay=0):
        """
        Turn on the power cutter.
        """

    @abc.abstractmethod
    def off(self, delay=0):
        """
        Turn off the power cutter.
        """

    @abc.abstractmethod
    def is_on(self):
        """
        Return whether cutter is turned on or not.
        """
