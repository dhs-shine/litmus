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
import time
import serial
import logging
import fasteners
from threading import Thread, Lock
from litmus.core.util import call, check_output
from litmus.core.util import convert_single_item_to_list
from litmus.core.util import find_pattern
from litmus.core.util import decode
from litmus.core.util import create_instance
from litmus.core.util import find_all_pattern
from litmus.core.exceptions import BootError
from litmus.device.cutter import cutter
from litmus import _path_for_locks_


class device(object):
    """
    Litmus device class.
    User can control device in topology by this class methods.
    """

    _baudrate = 115200
    _readtimeout = 0.5
    _enterkey = b'\r'
    _dnmode_cmd = b'thordown'
    _username = b'root'
    _password = b'tizen'
    _vid = '04e8'
    _pid = '685d'
    _pattern_loginprompt = r'.*login: $'
    _pattern_shellprompt = r'.*# .*'
    _max_attempt_login_uart_shell = 5
    _max_attempt_attach_sdb = 10
    _retrycnt_at_a_time_sdb = 20
    _max_attempt_boot_retry = 3
    _boot_timeout = 50.0
    _path_for_locks = _path_for_locks_

    _cutter = None
    _uart = None
    _manager = None
    _global_tlock = Lock()
    _global_ilock_path = os.path.join(_path_for_locks_, 'globallock')
    _global_ilock = fasteners.InterProcessLock(_global_ilock_path)

    _name = None
    _tests = None

    def __init__(self, *args, **kwargs):
        super(device, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self._name = kwargs['devicename']

        # init a cutter instance.
        self._cutter = cutter.create(*args, **kwargs)
        # open uart
        self._open_uart()
        self._manager = kwargs['manager']

    def __del__(self):
        """docstring for __del__"""
        self._release()

    def _release(self):
        """docstring for _release"""
        self._cutter.off(delay=1)
        self._close_uart()

    # public methods.

    @classmethod
    def create(self, *args, **kwargs):
        """
        Create a device instance.
        """
        clsname = 'device' + kwargs['dev_type']
        return create_instance(clsname,
                               'litmus.device',
                               *args,
                               **kwargs)

    def get_name(self):
        """
        Return the name of acquired device.

        Example:
            >>> dut = mgr.acquire_dut('xu3')
            >>> dut.get_name()
            'XU3_001'

        :returns str: device name
        """
        return self._name

    def get_id(self):
        """
        Return the id of acquired device.
        Device instance uses this id for sdb connection.

        Example:
            >>> dut = mgr.acquire_dut('xu3')
            >>> dut.get_id()
            'XU3_001'

        :returns str: device id
        """
        return self.get_name()

    def on(self, powercut_delay=1):
        """
        Turn on the device acquired.

        :param float powercut_delay: power-cut delay for cutter
        """
        logging.debug('=================Turn on device {}=================='
                      .format(self.get_name()))
        retry_cnt = 0
        while retry_cnt <= self._max_attempt_boot_retry:
            try:
                self.off(1)
                self._cutter.on(powercut_delay)
                self._wait_uart_shell_login_prompt()
                self._login_uart_shell()
                self._set_sdb_deviceid()
                self._attach_sdb()
                self._sdb_root_on()
                return
            except KeyboardInterrupt:
                self.off(1)
                raise Exception('Keyboard interrupt.')
            except Exception as e:
                logging.debug(e)
                retry_cnt += 1
        else:
            self.off(1)
            raise BootError('Can\'t turn on dut.')

    def off(self, powercut_delay=1):
        """
        Trun off the device acquired.

        :param float powercut_delay: power-cut delay for cutter
        """
        logging.debug('=================Turn off device {}================='
                      .format(self.get_name()))
        self._detach_sdb()
        self._cutter.off(powercut_delay)

    def is_on(self):
        """
        Return whether device is turned on or not.

        Example:
            >>> dut.on()
            >>> dut.is_on()
            True
            >>> dut.off()
            >>> dut.is_on()
            False

        :returns boolean: true if device is turned on, false otherwise.
        """
        pattern = '.*{}'.format(self.get_id())
        outs = check_output('sdb devices'.split(), timeout=10)
        if find_pattern(pattern, outs):
            return True
        else:
            return False

    def flash(self, filenames, flasher='lthor', waiting=5):
        """
        Flash binaries to device.
        This function turn on device and turn off device automatically.

        :param dict filenames: filename string or dict
        :param sting flasher: external flashing tool name
        :param float waiting: waiting time to acquire cdc_acm device

        Example:
            >>> dut.flash(['boot.tar.gz','platform.tar.gz'])
            >>> or
            >>> dut.flash('platform.tar.gz')

        """
        logging.debug('================Flash binaries to device============')
        logging.debug(filenames)

        if not filenames:
            raise Exception('There\'s no file to flash.')
        try:
            self._acquire_global_lock()
            time.sleep(waiting)
            self._enter_download_mode(self._dnmode_cmd)
            time.sleep(waiting)
            busid = self._find_usb_busid()
            self._release_global_lock()
            self._lthor(filenames=filenames, busid=busid)
            self._cutter.off()
        except (Exception, KeyboardInterrupt) as e:
            self._release_global_lock()
            logging.debug(e)
            raise Exception('Can\'t flash files : {}.'.format(filenames))

    def run_cmd(self, command, timeout=None):
        """
        Run a command on device.

        :param str command: command to run on device
        :param float timeout: timeout

        Example:
            >>> dut.on()
            >>> dut.run_cmd('ls -alF / | grep usr')
            \'drwxr-xr-x  15 root root     4096 Apr 29  2016 usr/\\r\\n\'

        :returns str: stdout of sdb shell command

        """
        logging.debug('================Run a command on device=============')
        c = ['sdb', '-s', self.get_id(), 'shell']
        c.extend(convert_single_item_to_list(command))
        logging.debug(c)
        result = check_output(c, timeout=timeout)
        return result

    def push_file(self, src, dest, timeout=None):
        """
        Push a file from host to destination path of device.

        :param str src: file path from host pc
        :param str dest: destination path of device
        :param float timeout: timeout

        Example:
            >>> dut.push_file('test.png', '/tmp')

        :returns str: stdout of sdb push command
        """
        logging.debug('================Push a file to device===============')
        c = ['sdb', '-s', self.get_id(), 'push', src, dest]
        result = check_output(c, timeout=timeout)
        return result

    def pull_file(self, src, dest, timeout=None):
        """
        Pull a file from device to destination path of host.

        :param str src: file path from device
        :param str dest: destination path of host pc
        :param float timeout: timeout

        Example:
            >>> dut.pull_file('/tmp/test.png','.')

        :returns str: stdout of sdb push command
        """
        logging.debug('================Pull a file from device=============')
        c = ['sdb', '-s', self.get_id(), 'pull', src, dest]
        result = check_output(c, timeout=timeout)
        return result

    def _read_uart(self, bufsize=100):
        """docstring for read_uart"""
        readdata = decode(self._uart.read(bufsize))
        logging.debug(readdata)
        return readdata

    def _write_uart(self, cmd, returnkey=b'\r'):
        """docstring for write_uart"""
        self._uart.write(cmd)
        time.sleep(0.1)
        if returnkey:
            self._uart.write(returnkey)

    def add_test(self, func, args):
        """
        Add a testcase to device class instance.

        :param func func: function object for test
        :param dict args: arguments for test function

        Example:
            >>> from litmus.helper.helper import verify_wifi_is_working
            >>> dut.add_test(verify_wifi_is_working,
                             {'wifi_apname': 'setup',
                              'wifi_password': '',
                              'result_dir': 'result'})

        """
        if not self._tests:
            self._tests = []

        self._tests.append({'func': func, 'args': args})

    def del_test(self, func):
        """
        Delete a testcase from device class instance.

        :param func func: function object for test

        Example:
            >>> from litmus.helper.helper import verify_wifi_is_working
            >>> dut.del_test(verify_wifi_is_working)
        """
        self._tests = [l for l in self._tests if l['func'] != func]

    def run_tests(self):
        """
        Run all testcases.

        Example:
            >>> from litmus.helper.helper import verify_wifi_is_working
            >>> dut.add_test(verify_wifi_is_working,
                             {'wifi_apname': 'setup',
                              'wifi_password': '',
                              'result_dir': 'result'})
            >>> dut.run_tests()

        """
        for l in self._tests:
            if isinstance(l['args'], dict):
                l['func'](self, **l['args'])
            elif isinstance(l['args'], tuple):
                l['func'](self, *l['args'])

    # private methods.

    def _flush_uart_buffer(self):
        """docstring for flush_uart_buffer"""
        self._uart.flushInput()
        self._uart.flushOutput()
        self._uart.flush()

    def _open_uart(self):
        """docstring for open_uart"""
        try:
            self._uart = serial.Serial(port=self.kwargs['uart_port'],
                                       baudrate=self._baudrate,
                                       timeout=self._readtimeout)
        except serial.SerialException as err:
            logging.debug(err)
            return None
        return self._uart

    def _close_uart(self):
        """docstring for close_uart"""
        if self._uart.isOpen():
            self._uart.close()

    def _thread_for_enter_download_mode(self, cmd, count):
        """docstring for thread_for_enter_download_mode"""
        for loop in range(count*20):
            self._uart.write(self._enterkey)
            time.sleep(0.05)
        self._uart.write(cmd)
        for loop in range(2):
            time.sleep(0.1)
            self._uart.write(self._enterkey)

    def _enter_download_mode(self, cmd, powercut_delay=1, thread_param=10):
        """docstring for _enter_download_mode"""
        t = Thread(target=self._thread_for_enter_download_mode,
                   args=(cmd, thread_param, ))
        t.start()
        self._cutter.off(delay=powercut_delay)
        self._cutter.on(delay=powercut_delay)
        t.join()

    def _find_usb_busid(self):
        """docstring for find_usb_busid"""
        pattern = 'usb (.*):.*idVendor={0}, idProduct={1}'.format(self._vid,
                                                                  self._pid)
        kernlog = 'cat /var/log/kern.log | grep usb | tail -n 20'
        outs = check_output(kernlog, shell=True, timeout=10)
        result = find_all_pattern(pattern=pattern, data=outs)
        if result:
            busid = result[-1]
            logging.debug('usb busid : {}'.format(busid))
        else:
            raise Exception('Can\'t find usb busid')

        return busid

    def _lthor(self, filenames, busid):
        """docstring for _lthor"""
        cmd = 'lthor --busid={0}'.format(busid)
        filenames = convert_single_item_to_list(filenames)
        for l in filenames:
            cmd += ' {}'.format(l)
        logging.debug(cmd)
        ret = call(cmd.split(), timeout=600)
        if ret:
            raise Exception('Thor error.')

    def _find_usb_bus_and_device_address(self):
        """docstring for _find_usb_bus_and_device_address"""
        pattern = 'usb (.*):.*idVendor={0}, idProduct={1}'.format(self._vid,
                                                                  self._pid)
        kernlog = 'cat /var/log/kern.log | grep usb | tail -n 20'
        outs = check_output(kernlog, shell=True, timeout=10)
        result = find_all_pattern(pattern=pattern, data=outs)
        if result:
            bid = result[-1]
            busaddr_cmd = 'cat /sys/bus/usb/devices/{0}/busnum'.format(bid)
            busaddr = check_output(busaddr_cmd, shell=True).rstrip().zfill(3)
            logging.debug('usb_bus_addr : {}'.format(busaddr))
            devaddr_cmd = 'cat /sys/bus/usb/devices/{0}/devnum'.format(bid)
            devaddr = check_output(devaddr_cmd, shell=True).rstrip().zfill(3)
            logging.debug('usb_dev_addr : {}'.format(devaddr))
        else:
            raise Exception('Can\'t find usb bus and dev addr')

        return (busaddr, devaddr)

    def _heimdall(self, filenames, busaddr, devaddr, partition_bin_mappings):
        """docstring for _heimdall"""
        filenames = convert_single_item_to_list(filenames)
        tar_cmd = ['tar', 'xvfz']
        for l in filenames:
            tar_cmd.append(l)
        logging.debug(tar_cmd)
        call(tar_cmd, timeout=30)

        heimdall_cmd = ['heimdall', 'flash', '--usbbus', busaddr,
                        '--usbdevaddr', devaddr]
        for key, elem in partition_bin_mappings.items():
            heimdall_cmd.append('--{}'.format(key))
            heimdall_cmd.append(elem)
        logging.debug(heimdall_cmd)

        ret = call(heimdall_cmd, timeout=600)
        if ret:
            raise Exception('Heimdall error.')

    def _wait_uart_shell_login_prompt(self):
        """docstring for _wait_uart_shell_login_prompt"""
        logging.debug('===============Print boot logs===============')

        start_time = time.perf_counter()
        wait_time = 0
        while wait_time < self._boot_timeout:
            if self._uart.inWaiting:
                buf = self._read_uart(1000)
                if find_pattern(self._pattern_loginprompt, data=buf):
                    logging.debug('Found login shell pattern from uart log')
                    logging.debug('wait_time : {}'.format(wait_time))
                    return
                elif len(buf) == 0:
                    self._write_uart(b'')
            time.sleep(0.01)
            wait_time = time.perf_counter() - start_time
        else:
            raise Exception('Boot timeout : {}s'.format(wait_time))

    def _login_uart_shell(self):
        """docstring for _login_uart_shell"""
        logging.debug('===============Login UART shell===============')
        retrycnt = 0
        while retrycnt < self._max_attempt_login_uart_shell:
            if self._username:
                self._write_uart(self._username)
                time.sleep(0.5)
            if self._password:
                self._write_uart(self._password)
                time.sleep(1.5)
            self._flush_uart_buffer()
            self._write_uart(b'dmesg -n 1')
            time.sleep(0.5)
            readdata = self._read_uart(2000)
            if find_pattern(self._pattern_shellprompt, readdata):
                return
            else:
                logging.debug('Login failed. retry.')
                self._write_uart(b'')
                time.sleep(2)
            retrycnt += 1
        else:
            raise Exception('Can\'t login uart shell.')

    def _set_sdb_deviceid(self):
        """docstring for _set_sdb_deviceid"""
        usb0_path = b'/sys/class/usb_mode/usb0'
        pattern = '.*{0}'.format(self.get_id())

        def set_serialnumber(deviceid):
            """docstring for set_serialnumber"""
            self._write_uart(b''.join([b'echo 0 > ', usb0_path, b'/enable']))
            time.sleep(0.3)
            self._write_uart(b''.join([b'echo ',
                                       b'-n ',
                                       deviceid,
                                       b' > ', usb0_path,
                                       b'/iSerial']))
            time.sleep(0.3)
            self._write_uart(b''.join([b'echo 1 > ', usb0_path, b'/enable']))
            time.sleep(0.3)

        def check_funcs_sconf():
            """docstring for check_funcs_sconf"""
            self._write_uart(b''.join([b'cat ', usb0_path, b'/funcs_sconf']))
            time.sleep(0.3)
            self._write_uart(b''.join([b'cat ', usb0_path, b'/enable']))
            time.sleep(0.3)
            self._read_uart(bufsize=1000)

        def get_serialnumber():
            """docstring for get_serialnumber"""
            self._write_uart(b''.join([b'cat ', usb0_path, b'/iSerial']))
            time.sleep(0.3)
            return self._read_uart(1000)

        retrycnt = 0
        while retrycnt < 10:
            set_serialnumber(deviceid=self.get_id().encode())
            check_funcs_sconf()
            serialnumber = get_serialnumber()
            if find_pattern(pattern, serialnumber):
                return
            retrycnt += 1
        else:
            raise Exception('Can\'t configure sdb deviceid')

    def _attach_sdb(self):
        """docstring for _attach_sdb"""
        # start sdb server if it is not started.
        call('sdb start-server'.split(), timeout=10)

        retry_attempt = 0
        pattern = r'{}.*device.*\t.*'.format(self.get_id())

        while retry_attempt < self._max_attempt_attach_sdb:
            for l in range(self._retrycnt_at_a_time_sdb):
                outs = check_output('sdb devices'.split(), timeout=10)
                logging.debug(outs)
                if find_pattern(pattern, outs):
                    logging.debug('found {}.'.format(self.get_id()))
                    return
                time.sleep(0.2)
            retry_attempt += 1
        else:
            raise Exception('Can\'t find device.')

    def _detach_sdb(self):
        """docstring for _detach_sdb"""
        pass

    def _sdb_root_on(self):
        """docstring for _sdb_root_on"""
        call('sdb -s {} root on'.format(self.get_id()).split(), timeout=10)
        time.sleep(0.5)

    def _acquire_global_lock(self):
        """docstring for _acquire_global_lock"""
        logging.debug('Try to acquire global lock...')
        self._global_tlock.acquire()
        self._global_ilock.acquire()
        # set gid of ilock file
        try:
            os.chmod(self._global_ilock.path, 0o664)
        except PermissionError:
            logging.debug('Can\'t change lock file permission')

        if self._global_tlock.locked() and self._global_ilock.acquired:
            logging.debug('global lock acquired for {}'
                          .format(self.get_id()))

    def _release_global_lock(self):
        """docstring for _release_global_lock"""
        if self._global_tlock.locked():
            self._global_tlock.release()
        if self._global_ilock.acquired:
            self._global_ilock.release()
        logging.debug('global lock released')
