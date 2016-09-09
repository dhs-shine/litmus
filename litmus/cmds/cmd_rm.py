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

import shutil
import logging
from configparser import RawConfigParser
from litmus import _projects_


def main(args):
    """docstring for main"""
    configparser = RawConfigParser()
    configparser.read(_projects_)

    if args.project in configparser.sections():
        path = configparser.get(args.project, 'path')
        shutil.rmtree(path)

        configparser.remove_section(args.project)
        with open(_projects_, 'w') as f:
            configparser.write(f)
        logging.debug('Project {0} is removed'.format(args.project))
    else:
        raise Exception('Project {0} does not exists'.format(args.project))
