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

import time
import serial
import logging
from threading import Thread
from configparser import RawConfigParser
from litmus import _duts_
from litmus.core.util import check_output, find_pattern, decode
from litmus.device.cuttercleware4 import cuttercleware4
from litmus.device.cuttersmartpower import cuttersmartpower


class generate_topology_sdb_device(object):
    """docstring for generate_topology_sdb_device"""

    devcatalog = [
        {'dev_type': 'u3',
         'cmd': 'printenv boardname',
         'pattern': r'.*odroidu3.*',
         'index': 1
         },
        {'dev_type': 'xu3',
         'cmd': 'printenv fdtfile',
         'pattern': r'.*odroidxu3.*',
         'index': 1
         },
        ]

    uarts = None
    smartpowers = None
    cleware4s = None
    topology_path = _duts_
    open_mode = 'w+'

    def __init__(self, *args, **kwargs):
        super(generate_topology_sdb_device, self).__init__()
        if 'append' in kwargs and kwargs['append']:
            self.open_mode = 'a+'
        if 'topology' in kwargs and kwargs['topology']:
            self.topology_path = kwargs['topology']

    def init_smartpowers(self):
        """docstring for init_smartpowers"""
        def find_smartpower_names():
            """docstring for find_smartpowers"""
            p = '.*Microchip Technology.*'
            try:
                smartpower_names = ['/dev/{}'.format(s)
                                    for s in check_output('ls /dev | grep hidraw',
                                                          shell=True).split()
                                    if find_pattern(p, check_output(['cat',
                                                                     '/sys/class/hidraw/{}/device/uevent'.format(s)]))]
            except AttributeError:
                smartpower_names = []
            logging.debug('smart powers : {0}'.format(smartpower_names))
            return smartpower_names

        smartpower_names = find_smartpower_names()
        self.smartpowers = []
        for l in smartpower_names:
            obj = {'dev_id': '',
                   'cutter_type': 'smartpower',
                   'cutter_port': l
                   }
            self.smartpowers.append(cuttersmartpower(**obj))

    def init_cleware4s(self):
        """docstring for init_cleware4s"""
        def find_cleware4_names():
            """docstring for find_cleware4s"""
            p = '.*Switch1.*version:.(29|512),.*serial number:.([0-9]{6,7})'
            cleware4s = [find_pattern(p, s, groupindex=2)
                         for s in check_output('clewarecontrol -l',
                                               shell=True).split('\n')
                         if find_pattern(p, s)]
            logging.debug('cleware4 cutters : {0}'.format(cleware4s))
            return cleware4s

        cleware4_names = find_cleware4_names()
        self.cleware4s = []
        for l in cleware4_names:
            for idx in range(0, 4):
                obj = {'dev_id': '',
                       'cutter_type': 'cleware4',
                       'cutter_port': l,
                       'cleware_index': idx
                       }
                self.cleware4s.append(cuttercleware4(**obj))

    def open_uarts(self):
        """docstring for open_uarts"""

        def init_jig(uart):
            """docstring for init_jig"""
            pass

        def get_items():
            """docstring for splitter"""
            out = check_output('ls /dev | egrep "(ttyUSB|ttyS0)"', shell=True)
            if out:
                return out.split()
            else:
                raise Exception('There\'s no /dev/ttyUSB for duts.')

        def find_uart_names():
            """docstring for find_uarts"""
            uarts = None
            uarts = ['/dev/{}'.format(s)
                     for s in get_items()]
            logging.debug('uarts : {0}'.format(uarts))
            return uarts

        self.uarts = []
        uart_names = find_uart_names()
        for l in uart_names:
            uart = serial.Serial(port=l, baudrate=115200, timeout=0.5)
            init_jig(uart)
            self.uarts.append(uart)

    def close_uarts(self):
        """docstring for close_uarts"""
        for l in self.uarts:
            l.close()

    def enter_boot_prompt(self, uart, cnt):
        """docstring for enter_boot_command"""
        for l in range(cnt):
            uart.write(b'\r')
            time.sleep(0.025)

    def enter_bootloader_prompt_mode(self):
        """docstring for enter_bootloader_prompt"""

        # create threads for entering bootloader prompt
        delay = (5 + (len(self.cleware4s) * 2 * 4 + len(self.smartpowers) * 2 * 2)) * 30

        threads = []
        for l in self.uarts:

            t = Thread(target=self.enter_boot_prompt, args=(l, delay))
            t.start()
            threads.append(t)

        # turn on duts
        self.turn_on_smartpowers()
        self.turn_on_cleware4s()

        # join all threads
        for l in threads:
            l.join()
        time.sleep(1)

    def turn_on(self, cutters):
        """docstring for turn_on"""
        for l in cutters:
            l.off(0.5)
            l.on(0.5)

    def turn_off(self, cutters):
        """docstring for turn_off"""
        for l in cutters:
            l.off(0.5)

    def turn_on_smartpowers(self):
        """docstring for turn_on_smartpowers"""
        self.turn_on(self.smartpowers)

    def turn_off_smartpowers(self):
        """docstring for turn_off_smartpowers"""
        self.turn_off(self.smartpowers)

    def turn_on_cleware4s(self):
        """docstring for turn_on_cleware4"""
        self.turn_on(self.cleware4s)

    def turn_off_cleware4s(self):
        """docstring for turn_off_cleware4"""
        self.turn_off(self.cleware4s)

    def recognize_device(self, config, uart):
        """docstring for recognize_device"""
        for l in self.devcatalog:
            logging.debug('Is {}'.format(l['dev_type'].upper()))
            uart.flushInput()
            time.sleep(0.1)
            uart.flushOutput()
            time.sleep(0.5)
            uart.flush()
            time.sleep(0.1)

            uart.write(l['cmd'].encode() + b'\r')
            time.sleep(0.5)

            buf = uart.read(5000)
            if find_pattern(l['pattern'], decode(buf)):
                logging.debug('Yes')
                name = '{0}_{1:0>3}'.format(l['dev_type'].upper(),
                                            l['index'])
                cfg = {'name': name,
                       'dev_type': l['dev_type'],
                       'uart_port': uart.name
                       }
                l['index'] += 1
                return cfg

    def is_on(self, uart):
        """docstring for is_on"""
        p = r'.*echo.*'
        uart.flushInput()
        time.sleep(0.1)
        uart.flushOutput()
        time.sleep(0.1)
        uart.flush()
        time.sleep(0.1)
        uart.write(b'echo\r')
        time.sleep(0.1)
        data = decode(b' '.join(uart.readlines(500)))
        return find_pattern(p, data)

    def generate_device_topology(self):
        """docstring for generate_device_topology"""

        # open config parser
        config = RawConfigParser()
        cfgs = []

        # recognize device type
        for l in self.uarts:
            logging.debug('[Recognize device type for uart : {}]'.format(l.name))
            cfg = self.recognize_device(config, l)
            if cfg:
                cfgs.append(cfg)
            else:
                l.close()

        # remove closed uart obj
        self.uarts = [m for m in self.uarts if m.isOpen()]

        logging.debug('[Generate topology configurations]')
        for l in self.smartpowers:
            l.off()
            for l_uart in self.uarts:
                if not self.is_on(l_uart):
                    dev = [m for m in cfgs if m['uart_port'] == l_uart.name][0]
                    dev['cutter_type'] = 'smartpower'
                    dev['cutter_port'] = l._cport
                    l_uart.close()
                    self.uarts.remove(l_uart)
                    logging.debug(dev)
                    break

        for l in self.cleware4s:
            l.off()
            for l_uart in self.uarts:
                if not self.is_on(l_uart):
                    dev = [m for m in cfgs if m['uart_port'] == l_uart.name][0]
                    dev['cutter_type'] = 'cleware4'
                    dev['cutter_port'] = l._cport
                    dev['cleware_index'] = l._cindex
                    l_uart.close()
                    self.uarts.remove(l_uart)
                    logging.debug(dev)
                    break

        for l in self.uarts:
            l.close()

        for l in cfgs:
            section_name = l['name']
            l.pop('name')
            config.add_section(section_name)
            for key in sorted(l.keys()):
                config.set(section_name, key, str(l[key]))

        with open(self.topology_path, self.open_mode) as f:
            config.write(f)
        logging.debug('Done.')

    def run(self):
        """docstring for run"""
        # init peripherals
        self.init_smartpowers()
        self.init_cleware4s()
        self.open_uarts()

        # enter bootloader prompt
        self.enter_bootloader_prompt_mode()

        # generate cfg
        self.generate_device_topology()

        # turn off duts
        self.turn_off_smartpowers()
        self.turn_off_cleware4s()

        # close uarts
        self.close_uarts()


def main(topology):
    """docstring for main"""
    try:

        logging.debug('# phase 1 : detect all devices which use sdb')
        phase_sdb = generate_topology_sdb_device(topology=topology)
        phase_sdb.run()

    except KeyboardInterrupt:
        raise Exception('Keyboard Interrupt')
    except Exception as e:
        logging.debug(e)
        raise Exception('Failed to generate topology')
