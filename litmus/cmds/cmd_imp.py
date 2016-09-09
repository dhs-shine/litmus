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
from litmus import _projects_
from litmus.cmds import load_project_list
from litmus.core.util import call


def main(args):
    """docstring for main"""
    prj_list = load_project_list()

    project = next((prj for prj in prj_list
                    if prj['name'] == args.project),
                   None)
    if project:
        raise Exception('Project {0} already exists'.format(project['name']))

    if not args.description:
        prj_description = input('Enter project descriptions : ')
    else:
        prj_description = args.description

    if not args.path:
        prj_path = input('Enter Project path : ')
    else:
        prj_path = args.path

    if not prj_path:
        raise Exception('Incorrect path!')

    prj_path = os.path.expanduser(prj_path)

    project = next((prj for prj in prj_list
                    if prj['path'] == prj_path),
                   None)

    if project:
        raise Exception('Project {0} already use this path'
                        .format(project['name']))

    if not os.path.exists(os.path.abspath(prj_path)) and\
            not os.path.exists(os.path.abspath(os.path.join(prj_path+'/',
                                                            'userscript.py'))):
        raise Exception('There\'s no litmus project scripts at {0}'
                        .format(prj_path))

    call(['chmod', '-R', '775', prj_path])

    with open(_projects_, 'a') as f:
        f.write('[{0}]\n'.format(args.project))
        f.write('path={0}\n'.format(os.path.abspath(prj_path)))
        f.write('description={0}\n\n'.format(prj_description))
