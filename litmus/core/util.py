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
import re
import sys
import logging
import yaml
import subprocess
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file


def init_logger():
    """
    Add logging.StreamHandler() to print logs on debug screen.
    """
    root_logger = logging.getLogger()
    console_handler = logging.StreamHandler()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)


def copy(src, dest):
    """
    Copy all files under src to dest.

    :param str src: source directory
    :param str dest: destination directory
    """
    filenames = convert_single_item_to_list(src)
    for l in filenames:
        if os.path.isdir(l):
            copy_tree(src, dest)
        else:
            copy_file(src, dest)


def decode(byte, encoding='ISO-8859-1'):
    """
    decode byte string to unicode string.

    :param str byte: byte string
    :param str encoding: encoding
    """
    unicodestr = byte.decode(encoding) if isinstance(byte, bytes) else byte
    return unicodestr


def create_instance(clsname, fromstr, *args, **kwargs):
    """
    import a module dynamically and create an instance.

    :param str clsname: module name which you want to create an instance
    :param str fromstr: location of the module

    :returns module instance: created instance
    """
    fromstr = '{}.{}'.format(fromstr, clsname)
    __import__(fromstr)
    return getattr(sys.modules[fromstr], clsname)(*args, **kwargs)


def check_output(cmd, timeout=None, encoding='ISO-8859-1', shell=False,
                 stderr=None):
    """
    Run command with arguments and return its output.
    This is a wrapper of subprocess.check_output().

    Example:
        >>> litmus.core.util.check_output(["echo", "Hello World"])
        b'Hello World!\\n'
    """
    outs = None
    try:
        outs = subprocess.check_output(cmd, timeout=timeout, shell=shell,
                                       stderr=stderr)
        if outs:
            outs = decode(outs, encoding=encoding)
    except subprocess.TimeoutExpired as e:
        logging.debug('command {} timed out : {}'.format(e.cmd, e.output))
        exc = sys.exc_info()
        raise exc[1].with_traceback(exc[2])
    except subprocess.CalledProcessError as e:
        logging.debug('command {} return non-zero : {}'.format(e.cmd,
                                                               e.output))
    except Exception:
        exc = sys.exc_info()
        raise exc[1].with_traceback(exc[2])

    return outs


def call(cmd, timeout=None, shell=False,
         stdout=None, stderr=None):
    """
    Run the command described by args.
    Wait for command to complete, then return the returncode attribute.
    This is a wrapper of subprocess.call().

    Example:
        >>> litmus.core.util.call(["ls", "-l"])
        0
    """
    ret = None
    try:
        ret = subprocess.call(cmd, timeout=timeout, shell=shell,
                              stdout=stdout, stderr=stderr)
    except subprocess.TimeoutExpired:
        logging.debug('command {} timed out'.format(cmd))
        exc = sys.exc_info()
        raise exc[1].with_traceback(exc[2])
    except Exception:
        exc = sys.exc_info()
        raise exc[1].with_traceback(exc[2])

    return ret


def convert_single_item_to_list(item):
    """
    Convert a item to list and return it.
    If item is already list then return the item without change.
    """
    return [item] if type(item) is not list else item


def find_pattern(pattern, data, groupindex=0):
    """
    Find a first match to a regular expression from data buffer.
    This also supports groupindex.

    :param str pattern: regular expression
    :param str data: data buffer
    :param int groupindex: group index

    :returns str: found string from data
    """
    if not data:
        data = ' '

    p = re.compile(pattern)
    result = p.search(data)
    if result:
        result = result.group(groupindex)
    return result


def find_all_pattern(pattern, data):
    """
    Find all matches to a regular expression from data buffer.

    :param str pattern: regular expression
    :param str data: data buffer

    :returns str: found string from data
    """
    if not data:
        data = ' '
    p = re.compile(pattern)
    result = p.findall(data)
    return result


def load_yaml(filename):
    """
    load a yaml file.

    :param str filename: a yaml filename

    :returns dict: parsed yaml data
    """
    with open(os.path.expanduser(filename), 'r') as stream:
        data = yaml.load(stream)
    return data
