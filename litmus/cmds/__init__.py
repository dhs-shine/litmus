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

from configparser import RawConfigParser
from litmus.core.util import call


def load_project_list(projects):
    """docstring for load_project_list"""
    configparser = RawConfigParser()
    configparser.read(projects)

    project_list = []
    for section in configparser.sections():
        item = dict(configparser.items(section))
        item['name'] = section
        project_list.append(item)
    return project_list

def sdb_does_exist():
    help_url = 'https://github.com/dhs-shine/litmus#prerequisite'
    try:
        call('sdb version', shell=True, timeout=10)
    except FileNotFoundError:
        raise Exception('Please install sdb. Refer to {}'.format(help_url))
    return
