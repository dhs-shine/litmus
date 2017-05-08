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
import time
import queue
import logging
import subprocess
from threading import Thread
from litmus.core.util import convert_single_item_to_list


def add_test_helper(dut, testcases):
    """
    This function helps user add many tests from dict or yaml file to device.

    :param device dut: device instance
    :param dict testcases: dict for test configuration

    Example:
        >>> from litmus.core.util import load_yaml
        >>> from litmus.helper.tests import add_test_helper
        >>> testcases = load_yaml(\'tc.yaml\')
        >>> add_test_helper(dut, testcases)
        >>> dut.run_tests()

    tc.yaml example:
        >>> testcases:
              - name: verify_process_is_running
                from: litmus.helper.tests
                result_dir: result
                plan:
                  - name: dbus_is_running
                    param: dbus
                    pattern: .*/usr/bin/dbus-daemon.*
                  - name: enlightenment_is_running
                    param: enlightenment
                    pattern: .*/usr/bin/enlightenment.*
              - name: verify_dmesg
                from: litmus.helper.tests
                result_dir: result
                plan:
                  - name: panel_is_alive
                    param: panel
                    pattern: .*panel is dead.*

    """

    for loop in testcases['testcases']:
        fromstr = loop['from']
        name = loop['name']
        del loop['from']
        del loop['name']
        __import__(fromstr)
        dut.add_test(getattr(sys.modules[fromstr], name), loop)


# pre-defined tests
def verify_process_is_running(dut, plan, result_dir):
    """
    Check whether mandatory processes are running or not.
    This testcase runs \'ps\' and \'grep\' commands on device.

    :param device dut: device instance
    :param dict plan: test plan
    :param str result_dir: directory to save test result xml

    Example:
        >>> from litmus.helper.tests import verify_process_is_running
        >>> verify_wifi_is_working(dut,
                                   [{'name': 'dbus_is_running',
                                     'param': 'dbus',
                                     'pattern': '.*/usr/bin/dbus-daemon.*'},
                                    {'name': 'deviced_is_runing',
                                     'param': 'deviced',
                                     'pattern': '.*/usr/bin/deviced.*'},
                                    ],
                                   'result')

    """
    test_name = 'verify_process_is_running'
    template_report = """<report categ='SmokeTest' failures='{failure_cnt}' name='{test_name}'>
{data}</report>"""
    template_test = """    <test executed='yes' name='{tc_name}'>
        <result>
            <success passed='{tc_result}' state='{tc_state}' />
        </result>
    </test>
"""

    def _verify(item):
        """docstring for _verify"""
        cmd = ['ps', 'ax', '|', 'grep', item['param']]
        res = dut.run_cmd(cmd)
        p = re.compile(item['pattern'])
        if p.search(res):
            return True
        else:
            return False

    def _run():
        results = ''
        failure_cnt = 0
        for item in plan:
            tc_result = 'yes' if _verify(item) else 'no'
            failure_cnt = failure_cnt+1 if tc_result != 'yes' else failure_cnt
            dict_for_output = {'tc_name': item['name'],
                               'tc_result': tc_result,
                               'tc_state': 100 if tc_result == 'yes' else 0}
            results += template_test.format(**dict_for_output)
        output = template_report.format(failure_cnt=failure_cnt,
                                        test_name=test_name,
                                        data=results)
        logging.debug(output)
        return output

    def _save_result(result, result_dir):
        """docstring for _save_result"""
        with open(os.path.join(result_dir,
                               'testresult_process_is_running.xml'), 'w') as f:
            f.write(result)

    _save_result(_run(), os.path.abspath(result_dir))


def verify_dmesg(dut, plan, result_dir):
    """
    Read kernel logs and check whether error log exists or not.
    This testcase runs \'dmesg\' and \'grep\' commands on device.

    :param device dut: device instance
    :param dict plan: test plan
    :param str result_dir: directory to save test result xml

    Example:
        >>> from litmus.helper.tests import verify_dmesg
        >>> verify_dmesg(dut,
                         [{\'name\': \'panel_is_alive\',
                           \'param\': \'panel\',
                           \'pattern\': \'.*panel is dead.*\'},
                          ],
                         \'result\')

    """
    test_name = 'verify_dmesg'
    template_report = """<report categ='SmokeTest' failures='{failure_cnt}' name='{test_name}'>
{data}</report>"""
    template_test = """    <test executed='yes' name='{tc_name}'>
        <result>
            <success passed='{tc_result}' state='{tc_state}' />
        </result>
    </test>
"""

    def _verify(item):
        """docstring for _verify"""
        cmd = ['dmesg', '|', 'grep', item['param']]
        res = dut.run_cmd(cmd)
        p = re.compile(item['pattern'])
        if not p.search(res):
            return True
        else:
            return False

    def _run():
        results = ''
        failure_cnt = 0
        for item in plan:
            tc_result = 'yes' if _verify(item) else 'no'
            failure_cnt = failure_cnt+1 if tc_result != 'yes' else failure_cnt
            dict_for_output = {'tc_name': item['name'],
                               'tc_result': tc_result,
                               'tc_state': 100 if tc_result == 'yes' else 0}
            results += template_test.format(**dict_for_output)
        output = template_report.format(failure_cnt=failure_cnt,
                                        test_name=test_name,
                                        data=results)
        logging.debug(output)
        return output

    def _save_result(result, result_dir):
        """docstring for _save_result"""
        with open(os.path.join(result_dir, 'testresult_dmesg.xml'), 'w') as f:
            f.write(result)

    _save_result(_run(), os.path.abspath(result_dir))


def verify_wifi_is_working(dut, wifi_apname, wifi_password, result_dir):
    """
    Try to connect wifi ap and publish the test result as a xml file.
    This testcase runs 'wifi_test' command on device.

    :param device dut: device instance
    :param str wifi_apname: wifi ap name
    :param str wifi_password: wifi ap password
    :param str result_dir: directory to save test result xml

    Example:
        >>> from litmus.helper.tests import verify_wifi_is_working
        >>> verify_wifi_is_working(dut, 'setup', '', 'result')

    """
    test_name = 'wifi_is_working'
    template_report = """<report categ='SmokeTest' failures='{failure_cnt}' name='{test_name}'>
{data}</report>"""
    template_test = """    <test executed='yes' name='{tc_name}'>
        <result>
            <success passed='{tc_result}' state='{tc_state}' />
        </result>
    </test>
"""

    def _enqueue_output(out, queue):
        for line in iter(out.readline, b''):
            queue.put(line.strip().decode())
        out.close()

    def _write_cmd(cmd, status_pass, status_fail, timeout=10):
        """docstring for _write_cmd"""
        status_pass = convert_single_item_to_list(status_pass)
        status_fail = convert_single_item_to_list(status_fail)

        logging.debug('===== cmd : {} ====='.format(cmd))
        cmd = cmd + '\r'
        start_time = time.perf_counter()
        sdbshell.stdin.write(cmd.encode())
        sdbshell.stdin.flush()
        time.sleep(0.5)
        logging.debug('response:')
        while True:
            try:
                line = q.get(timeout=0.1)
                logging.debug(line)
            except queue.Empty:
                wait_time = time.perf_counter() - start_time
                if wait_time > timeout:
                    raise Exception('timeout')
                elif wait_time > (timeout / 2):
                    sdbshell.stdin.write('\r'.encode())
                    sdbshell.stdin.flush()
                    time.sleep(1)
            else:
                if line in status_pass:
                    break
                elif line in status_fail:
                    raise Exception('wifi test return fail : {}'.format(line))

    def _run():
        """docstring for _run"""

        try:
            _write_cmd('wifi_test; exit', 'Test Thread created...', None)
            _write_cmd('1', 'Operation succeeded!', 'Operation failed!')
            _write_cmd('3',
                       ['Success to activate Wi-Fi device',
                        'Wi-Fi Activation Succeeded',
                        'Fail to activate Wi-Fi device [ALREADY_EXISTS]'],
                       None)
            time.sleep(7)
            _write_cmd('9', 'Operation succeeded!', 'Operation failed!')
            time.sleep(3)
            for loop in range(3):
                _write_cmd('b', 'Get AP list finished', None)
                time.sleep(3)
            _write_cmd('c',
                       'Input a part of AP name to connect :',
                       ['Wi-Fi Activation Failed! error : OPERATION_FAILED',
                        'Device state changed callback, state : Deactivated',
                        'Operation failed!'])
            _write_cmd(wifi_apname,
                       ['Passphrase required : TRUE',
                        'Passphrase required : FALSE'],
                       ['Wi-Fi Activation Failed! error : OPERATION_FAILED',
                        'Device state changed callback, state : Deactivated',
                        'Operation failed!'])
            if wifi_password and wifi_password != '':
                _write_cmd(wifi_password,
                           'Connection step finished',
                           ['Wi-Fi Activation Failed! error : '
                            'OPERATION_FAILED',
                            'Device state changed callback, state : '
                            'Deactivated',
                            'Operation failed!'])
            _write_cmd('6',
                       ['Success to get connection state : Connected',
                        'Wi-Fi Connection Succeeded'],
                       ['Wi-Fi Activation Failed! error : OPERATION_FAILED',
                        'Wi-Fi Connection Failed! error : INVALID_KEY',
                        'Device state changed callback, state : Deactivated',
                        'Operation failed!',
                        'Success to get connection state : Disconnected',
                        'Connection state changed callback, state : '
                        'Disconnected, AP name : {}'.format(wifi_apname)])
            _write_cmd('0', 'exit', None)

            dict_for_output = {'tc_name': test_name,
                               'tc_result': 'yes',
                               'tc_state': 100}
            results = template_test.format(**dict_for_output)
            output = template_report.format(failure_cnt=0,
                                            test_name=test_name,
                                            data=results)
        except Exception:
            dict_for_output = {'tc_name': test_name,
                               'tc_result': 'no',
                               'tc_state': 0}
            results = template_test.format(**dict_for_output)
            output = template_report.format(failure_cnt=1,
                                            test_name=test_name,
                                            data=results)
        finally:
            sdbshell.terminate()
            return output

    def _save_result(result, result_dir):
        """docstring for _save_result"""
        logging.debug(result)
        with open(os.path.join(result_dir, 'testresult_wifi.xml'), 'w') as f:
            f.write(result)

    sdbshell = subprocess.Popen(['sdb', '-s', dut.get_id(), 'shell'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    q = queue.Queue()
    t = Thread(target=_enqueue_output, args=(sdbshell.stdout, q))
    t.daemon = True
    t.start()
    _save_result(_run(), os.path.abspath(result_dir))
