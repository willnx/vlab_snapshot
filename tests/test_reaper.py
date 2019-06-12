# -*- coding: UTF-8 -*-
"""A suite of unit tests for the ``reaper.py`` module"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_snapshot_api.lib.worker import reaper


class TestIsExpired(unittest.TestCase):
    """A suite of test cases for the ``is_expired`` function"""
    def test_is_expired(self):
        """``is_expired`` returns True when the current time is greater than the exp time of the snapshot"""
        snap = 'aabbcc_1234_4321'

        is_expired = reaper.is_expired(snap)

        self.assertTrue(is_expired)

    def test_is_not_expired(self):
        """``is_expired`` returns False when the snapshot is less than the exp time of the snapshot"""
        snap = 'aabbcc_1234_9999999999999999999'

        is_expired = reaper.is_expired(snap)

        self.assertFalse(is_expired)


class TestReapSnapshots(unittest.TestCase):
    """A suite of tests cases for the ``reap_snapshots`` function"""
    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.logger = MagicMock()
        cls.vcenter = MagicMock()
        fake_vm = MagicMock()
        fake_vm.snapshot = True
        fake_vms = MagicMock()
        fake_vms.childEntity = [fake_vm]
        fake_user = MagicMock()
        fake_users_folder = MagicMock()
        fake_users_folder.childEntity = [fake_user]
        cls.vcenter.get_by_name.side_effect = [fake_users_folder, fake_vms]
        cls.fake_snap = MagicMock()
        cls.fake_snap.name = 'aabbcc_1234_4321'
        cls.fake_snaps = MagicMock()
        cls.fake_snaps = [cls.fake_snap]

    @classmethod
    def tearDown(cls):
        """Runs after every test case"""
        cls.vcenter = None
        cls.logger = None

    @patch.object(reaper, 'consume_task')
    @patch.object(reaper, '_get_snapshots')
    def test_delete_exp_snapshot(self, fake_get_snapshots, fake_consume_task):
        """``reap_snapshots`` deletes expired snapshots"""
        fake_get_snapshots.return_value = self.fake_snaps
        reaper.reap_snapshots(vcenter=self.vcenter, logger=self.logger)

        self.assertTrue(fake_consume_task.called)

    @patch.object(reaper, 'consume_task')
    @patch.object(reaper, '_get_snapshots')
    def test_no_delete(self, fake_get_snapshots, fake_consume_task):
        """``reap_snapshots`` does not delete snapshots that are still valid"""
        self.fake_snap.name = 'aabbcc_1234_999999999999999999'
        fake_get_snapshots.return_value = self.fake_snaps
        reaper.reap_snapshots(vcenter=self.vcenter, logger=self.logger)

        self.assertFalse(fake_consume_task.called)


class TestMain(unittest.TestCase):
    """A suite of test cases for the ``main`` function"""
    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.logger = MagicMock()

    @classmethod
    def tearDown(cls):
        """Runs after every test case"""
        cls.logger = None

    @patch.object(reaper, 'reap_snapshots')
    @patch.object(reaper, 'vCenter')
    @patch.object(reaper, 'time')
    def test_main(self, fake_time, fake_vCenter, fake_reap_snapshots):
        """``main`` sleeps in between loops"""
        # the RuntimeError is how we break out of the while loop of the serivce
        fake_time.time.side_effect = [1, 2, RuntimeError('break from loop')]

        reaper.main(self.logger)

        self.assertEqual(fake_time.sleep.call_count, 1)

    @patch.object(reaper, 'reap_snapshots')
    @patch.object(reaper, 'vCenter')
    @patch.object(reaper, 'time')
    def test_main_error(self, fake_time, fake_vCenter, fake_reap_snapshots):
        """``main`` logs fatal errors before terminating"""
        # the RuntimeError is how we break out of the while loop of the serivce
        fake_reap_snapshots.side_effect = [Exception('testing')]

        reaper.main(self.logger)

        self.assertTrue(self.logger.exception.called)


if __name__ == '__main__':
    unittest.main()
