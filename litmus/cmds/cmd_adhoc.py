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
import sys
from litmus.core.util import call
from litmus.cmds import sdb_exist


def main(args):
    """docstring for main"""
    sdb_exist()
    project_path = os.path.abspath(args.project_path)
    sys.path.append(project_path)

    call(['chmod', '-R', '775', project_path])

    import userscript
    userscript.main(project_name='adhoc project',
                    project_path=project_path,
                    param=args.param,
                    workingdir=args.workingdir)
