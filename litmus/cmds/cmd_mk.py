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
import litmus
import logging
from litmus.core.util import copy, call
from litmus import _projects_, _dev_types_
from litmus.cmds import load_project_list


def main(args):
    """docstring for main"""
    prj_list = load_project_list()

    project = next((prj for prj in prj_list if prj['name'] == args.project),
                   None)
    if project:
        raise Exception('Project {0} already exists'.format(args.project))

    if not args.type:
        dev_type = input('Enter the device type ({}): '
                         .format('/'.join(_dev_types_)))
    else:
        dev_type = args.type

    if dev_type not in _dev_types_:
        raise Exception('Incorrect device type')

    path = os.path.abspath(os.path.join(os.curdir, args.project))
    if not os.path.exists(path):
        if not args.description:
            description = input('Enter descriptions for this project : ')
        else:
            description = args.description
        logging.debug('make a new project : {0}'.format(args.project))
        logging.debug('new project path : {0}'.format(path))
        os.mkdir(path)
        src = os.path.join(os.path.join(litmus.__path__[0], 'templates'),
                           dev_type)
        copy(src, path)
        call(['chmod', '-R', '775', path])

        with open(_projects_, 'a') as f:
            f.write('[{0}]\n'.format(args.project))
            f.write('path={0}\n'.format(path))
            f.write('description={0}\n\n'.format(description))
    else:
        raise Exception('{0} already exists'.format(path))
