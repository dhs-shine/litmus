#!/usr/bin/env python3

import os
import unittest
from litmus.core.manager import manager


class TestLitmus(unittest.TestCase):

    mgr = None

    def setUp(self):
        self.mgr = manager()

    def tearDown(self):
        self.mgr.release_dut()

    def test_acquisition(self):
        dut = dut1 = None
        try:
            dut = self.mgr.acquire_dut('xu3')
        except Exception as e:
            print(e)

        self.assertNotEqual(first=dut, second=None)

        try:
            dut1 = self.mgr.acquire_dut('hawkp')
        except Exception as e:
            print(e)

        self.assertEqual(first=dut1, second=None)

    def test_all_acquired_duts(self):
        self.mgr.release_dut()

        self.assertEqual(first=self.mgr.get_all_acquired_duts(), second=[])

        try:
            self.mgr.acquire_dut('xu3')
        except Exception as e:
            print(e)

        self.assertNotEqual(first=self.mgr.get_all_acquired_duts(), second=[])

    def test_workingdir(self):
        self.mgr.init_workingdir(workingdir='.')
        current_dir = os.path.abspath(os.path.curdir)

        self.assertEqual(first=current_dir, second=self.mgr.get_workingdir())


if __name__ == '__main__':
    unittest.main(verbosity=2)
