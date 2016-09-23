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
import sys
import time
import logging
import requests
import urllib.parse
from bs4 import BeautifulSoup
from litmus.core.util import find_pattern, find_all_pattern
from litmus.core.util import call


def tizen_snapshot_downloader(url, pattern_bin='tar.gz$',
                              username='', password='',
                              pattern_version='tizen[a-zA-Z0-9-_.^/]*[0-9]{8}.[0-9]{1,2}',
                              version=None,
                              timeout=10,
                              maxretry=20,
                              waiting_for_retry=10):
    """
    Download snapshot images from web server.

    :param str url: url for downloading binaries. This has to include 'latest' string
    :param str pattern_bin: filename pattern to find correct binary under the url
    :param str username: username to access http server
    :param str password: password to access http server
    :param str pattern_version: pattern of tizen snapshot version string
    :param str version: specific version string of tizen snapshot what you want to download
    :param float timeout: timeout
    :param int maxretry: max retry count to attempt the url for downloading
    :param float waiting_for_retry: delay for each retry

    Example:
        >>> from litmus.helper.helper import tizen_snapshot_downloader
        >>> tizen_snapshot_downloader(url=\'http://download.tizen.org/snapshots/tizen/tv/latest/images/arm-wayland/tv-wayland-armv7l-odroidu3/\')
        [\'tizen-tv_20160516.2_tv-wayland-armv7l-odroidu3.tar.gz\']

    :returns list: filenames of downloaded binaries

    """
    logging.debug('============Download binaries from server===========')
    # convert latest url to actual url
    url_to_find_latest_version_number = url.split('latest')[0]

    for loop in range(maxretry):
        try:
            f = requests.get(url_to_find_latest_version_number,
                             auth=(username, password), timeout=timeout)
            if f.status_code == 200:
                break
            time.sleep(waiting_for_retry)
        except requests.exceptions.Timeout as e:
            logging.debug(e)
            continue
        except requests.exceptions.ConnectionError as e:
            logging.debug(e)
            continue
        except Exception as e:
            logging.debug(e)
            raise Exception('Can\'t open url {0}'.format(url))
    else:
        raise Exception('Can\'t open url {0}'.format(url))

    latest_version = find_all_pattern(pattern_version, f.text)[-1]
    url = url.replace('latest', latest_version)

    if version:
        pattern_version_number = '[0-9]{8}.[0-9]{1,2}'
        found = find_pattern(pattern_version_number, url)
        url = url.replace(found, version)

    # get data from actual url and download binaries
    for loop in range(maxretry):
        try:
            f = requests.get(url, auth=(username, password), timeout=timeout)
            if f.status_code != 200:
                continue
            soup = BeautifulSoup(f.text, 'html.parser')
            filenames = []

            for l in soup.findAll('a', attrs={'href': re.compile(pattern_bin)}):
                filename = l['href']
                fileurl = urllib.parse.urljoin(url, filename)
                logging.debug(fileurl)

                with open(filename, 'wb') as f:
                    logging.debug('Downloading {}'.format(filename))
                    resp = requests.get(fileurl,
                                        auth=(username, password),
                                        stream=True)

                    total_length = resp.headers.get('Content-Length')

                    if total_length is None:
                        f.write(resp.content)
                    else:
                        downloaded_data = 0
                        total_length = int(total_length)
                        for download_data in resp.iter_content(chunk_size=1024 * 1024):
                            downloaded_data += len(download_data)
                            f.write(download_data)
                            done = int(50 * downloaded_data / total_length)
                            sys.stdout.write('\r[{0}{1}]'.format('#'*done,
                                                                 ' '*(50-done)))
                            sys.stdout.flush()
                logging.debug('')
                filenames.append(filename)

            if filenames:
                break
            else:
                logging.debug('There\'s no binary for downloading. Retry.')
                time.sleep(waiting_for_retry)

        except requests.exceptions.Timeout as e:
            logging.debug(e)
            continue
        except requests.exceptions.ConnectionError as e:
            logging.debug(e)
            continue
        except Exception as e:
            logging.debug(e)
            raise Exception('Can\'t open url {0}'.format(url))
    else:
        raise Exception('Can\'t open url {0}'.format(url))

    return filenames


def install_plugin(dut, script, waiting=5, timeout=180):
    """
    Install tizen plugins on device.
    This helper function turn on device and turn off device automatically.

    :param device dut: device instance
    :param str script: script path to install plugins on device
    :param float waiting: wait time before installing plugins
    :param float timeout: timeout

    Example:
        >>> from litmus.helper.helper import install_plugin
        >>> install_plugin(dut,
                           script='install-set/setup')
    """
    logging.debug('================Install plugins=================')
    dut.on()

    script_path = '/'.join(script.split('/')[:-1])
    script_name = script.split('/')[-1]

    call('cp -R {0}/* .'.format(script_path), shell=True)

    time.sleep(waiting)

    call('sh {0} {1}'.format(script_name, dut.get_id()).split(),
         timeout=timeout)

    dut.off()


import os
import shutil
from subprocess import DEVNULL

def install_plugin_from_git(dut, url, branch, script, tmpdir='repo',
                            waiting=5, timeout=180, commitid=None):
    """
    Clone a git project which include tizen plugins and install the plugins on device.
    This helper function turn on device and turn off device automatically.

    :param device dut: device instance
    :param str url: url for git project
    :param str branch: branch name of the git project
    :param str script: script path to install plugins on device
    :param str tmpdir: temporary directory to clone the git project
    :param float waiting: wait time before installing plugins
    :param float timeout: timeout
    :param str commitid: commitid which you want to clone

    .. note:: You have to configure your open-ssh key if you want to use ssh protocol to clone the git project.

    Example:
        >>> from litmus.helper.helper import install_plugin_from_git
        >>> install_plugin_from_git(dut,
                                    url='ssh://{username}@localhost:29418/platform/adaptation/opengl-es-mali-t628'
                                    branch='tizen_3.0'
                                    script='install-set/setup')


    """
    logging.debug('=============Install plugins from git===============')
    logging.debug('plugin git path : {}'.format(url))
    logging.debug('plugin git branch : {}'.format(branch))
    logging.debug('plugin git commitid : {}'
                  .format(commitid if commitid else 'latest'))
    logging.debug('plugin install script : {}'.format(script))
    dut.on()

    call('git clone {0} {1} --branch {2}'.format(url, tmpdir, branch),
         shell=True)

    if commitid:
        call('git --git-dir={0}/.git checkout {1}'.format(tmpdir, commitid),
             shell=True)

    call('find ./{0} -exec perl -pi -e "s/sdb\s+(-d\s+)*(root|shell|push|pull)/sdb -s {1} \\2/g" {{}} \;'.format(tmpdir, dut.get_id()), stderr=DEVNULL, shell=True)
    call('find ./{0} -exec perl -pi -e "s/sdb\s+.*reboot.*//g" {{}} \;'.format(tmpdir), stderr=DEVNULL, shell=True)

    script = os.path.join(tmpdir, script)

    script_path = '/'.join(script.split('/')[:-1])
    script_name = script.split('/')[-1]
    call('cp -R {0}/* .'.format(script_path), shell=True)

    time.sleep(waiting)

    call('sh {0}'.format(script_name).split(), timeout=timeout)
    shutil.rmtree(tmpdir)

    dut.off()
