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

import logging
from litmus.cmds import load_project_list


def main(args):
    """docstring for main"""
    prj_list = load_project_list()
    logging.debug('=====list of all litmus projects=====')
    for loop in prj_list:
        logging.debug('{0:10s} ({1} : {2})'.format(loop['name'],
                                                   loop['description'],
                                                   loop['path']))
