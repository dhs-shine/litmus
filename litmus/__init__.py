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

__version__ = '0.2.1'
_homedir_ = os.path.expanduser('~')
_confdir_ = os.path.join(_homedir_, '.litmus')
_duts_ = os.path.join(_confdir_, 'topology')
_projects_ = os.path.join(_confdir_, 'projects')
_tmpdir_ = '/tmp'
_path_for_locks_ = '/var/lock/litmus/'
_dev_types_ = ('u3', 'xu3', 'empty')
