#!/usr/bin/env python3
# Copyright 2015-2016 Samsung Electronics Co., Ltd
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
import logging
from litmus.core.util import copy, call
from litmus.cmds import load_project_list


def main(args):
    """docstring for main"""
    prj_list = load_project_list(args.projects)

    orig = next((prj for prj in prj_list if prj['name'] == args.orig),
                None)
    if not orig:
        raise Exception('Project {0} does not exists'.format(args.orig))

    new = next((prj for prj in prj_list if prj['name'] == args.new),
               None)
    if new:
        raise Exception('Project {0} already exists'.format(args.new))

    path = os.path.abspath(os.path.join(os.curdir, args.new))
    if not os.path.exists(path):
        logging.debug('copy project {0} to {1}'.format(args.orig, path))
        if not args.description:
            description = input('Enter descriptions for this project : ')
        else:
            description = args.description
        os.mkdir(path)
        copy(orig['path'], path)
        call(['chmod', '-R', '775', path])

        with open(args.projects, 'a') as f:
            f.write('[{0}]\n'.format(args.new))
            f.write('path={0}\n'.format(path))
            f.write('description={0}\n\n'.format(description))
    else:
        raise Exception('{0} already exists'.format(path))
