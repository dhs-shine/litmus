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

import re
import os
from setuptools import setup, find_packages

PROJECT_NAME = 'litmus'
ETC_PATH = os.path.join('/etc', PROJECT_NAME)

version = re.search("__version__.*'(.+)'",
                    open(os.path.join(PROJECT_NAME, '__init__.py'))
                    .read()).group(1)

setup(name=PROJECT_NAME,
      description='Lightweight test manager',
      long_description='Lightweight test manager for tizen automated testing',
      version=version,
      author="Donghoon Shin",
      author_email="dhs.shin@samsung.com",
      url="http://www.tizen.org",
      package_dir={PROJECT_NAME: 'litmus'},
      packages=find_packages(exclude=['litmus.templates']),
      data_files=[(ETC_PATH, ['tools/projects', 'tools/topology'])],
      include_package_data=True,
      license="Apache",
      platforms='any',
      scripts=['tools/litmus'],
      )
