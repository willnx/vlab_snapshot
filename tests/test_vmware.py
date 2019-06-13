# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in vmware.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_snapshot_api.lib.worker import vmware

class FakeSnapshot:
    def __init__(self, snap_id, snap_created, snap_expires):
        self.name = '{}_{}_{}'.format(snap_id, snap_created, snap_expires)
        self.snapshot = MagicMock()

class TestVMware(unittest.TestCase):
    """A set of test cases for the vmware.py module"""

    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_show_snapshot(self, fake_vCenter, fake_get_snapshots):
        """``snapshot`` returns a dictionary when everything works as expected"""
        fake_get_snapshots.return_value = [FakeSnapshot('asdf', 1234, 4321)]
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        output = vmware.show_snapshot(username='alice')
        expected = {'SomeVM': [{'id': 'asdf', 'created': 1234, 'expires': 4321}]}

        self.assertEqual(output, expected)

    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_snapshot(self, fake_vCenter, fake_consume_task, fake_get_snapshots):
        """``delete_snapshot`` returns None when everything works as expected"""
        fake_get_snapshots.return_value = [FakeSnapshot('asdf', 1234, 4321)]
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        output = vmware.delete_snapshot(username='bob', machine_name='SomeVM', snap_id='asdf', logger=fake_logger)
        expected = None

        self.assertEqual(output, expected)

    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_snapshot_value_error(self, fake_vCenter, fake_consume_task, fake_get_snapshots):
        """``delete_snapshot`` raises ValueError when unable to find requested vm for snapshot deletion"""
        fake_get_snapshots.return_value = [FakeSnapshot('asdf', 1234, 4321)]
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        with self.assertRaises(ValueError):
            vmware.delete_snapshot(username='bob', machine_name='SomeOtherVM', snap_id='asdf', logger=fake_logger)

    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_snapshot_no_exists(self, fake_vCenter, fake_consume_task, fake_get_snapshots):
        """``delete_snapshot`` raises ValueError when the requested snapshot does not exists"""
        fake_get_snapshots.return_value = [FakeSnapshot('asdf', 1234, 4321)]
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        with self.assertRaises(ValueError):
            vmware.delete_snapshot(username='bob', machine_name='SomeVM', snap_id='qwerty', logger=fake_logger)

    @patch.object(vmware, '_take_snapshot')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_create_snapshot(self, fake_vCenter, fake_get_snapshots, fake_take_snapshot):
        """``create_snapshot`` Returns snapshot details after successfully taking the snapshot"""
        fake_get_snapshots.return_value = []
        fake_take_snapshot.return_value = ('aabbcc', 1234, 2345)
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        snap_info = vmware.create_snapshot(username='sam',
                                           machine_name='SomeVM',
                                           shift=False,
                                           logger=fake_logger)
        expected = {'SomeVM': [{'id': 'aabbcc', 'created': 1234, 'expires': 2345}]}

        self.assertEqual(snap_info, expected)

    @patch.object(vmware, '_take_snapshot')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_create_snapshot_attr_error(self, fake_vCenter, fake_get_snapshots, fake_take_snapshot):
        """``create_snapshot`` handles the AttributeError that occurs when a VM has no snapshots"""
        fake_get_snapshots.side_effect = [AttributeError('fuck pyvmomi')]
        fake_take_snapshot.return_value = ('aabbcc', 1234, 2345)
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        snap_info = vmware.create_snapshot(username='sam',
                                           machine_name='SomeVM',
                                           shift=False,
                                           logger=fake_logger)
        expected = {'SomeVM': [{'id': 'aabbcc', 'created': 1234, 'expires': 2345}]}

        self.assertEqual(snap_info, expected)

    @patch.object(vmware, '_deleted_old_snaps')
    @patch.object(vmware, '_take_snapshot')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_create_snapshot_shift(self, fake_vCenter, fake_get_snapshots, fake_take_snapshot, fake_deleted_old_snaps):
        """``create_snapshot`` param 'shift' works"""
        fake_get_snapshots.return_value = [x for x in range(vmware.const.VLAB_MAX_SNAPSHOTS)]
        fake_take_snapshot.return_value = ('aabbcc', 1234, 2345)
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        snap_info = vmware.create_snapshot(username='sam',
                                           machine_name='SomeVM',
                                           shift=True,
                                           logger=fake_logger)
        expected = {'SomeVM': [{'id': 'aabbcc', 'created': 1234, 'expires': 2345}]}

        self.assertEqual(snap_info, expected)

    @patch.object(vmware, '_take_snapshot')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_create_snapshot_no_shift(self, fake_vCenter, fake_get_snapshots, fake_take_snapshot):
        """``create_snapshot`` Raises ValueError when VM has already exceed max snaps allowed and param 'shift' not supplied"""
        fake_get_snapshots.return_value = [x for x in range(vmware.const.VLAB_MAX_SNAPSHOTS)]
        fake_take_snapshot.return_value = ('aabbcc', 1234, 2345)
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        with self.assertRaises(ValueError):
            vmware.create_snapshot(username='sam',
                                   machine_name='SomeVM',
                                   shift=False,
                                   logger=fake_logger)

    @patch.object(vmware, '_take_snapshot')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_create_snapshot_no_vm(self, fake_vCenter, fake_get_snapshots, fake_take_snapshot):
        """``create_snapshot`` Raises ValueError if the VM requested to be snapshoted does not exist"""
        fake_get_snapshots.return_value = []
        fake_take_snapshot.return_value = ('aabbcc', 1234, 2345)
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        with self.assertRaises(ValueError):
            vmware.create_snapshot(username='sam',
                                   machine_name='SomeOtherVM',
                                   shift=False,
                                   logger=fake_logger)

    @patch.object(vmware, '_take_snapshot')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_create_snapshot_not_first_vm(self, fake_vCenter, fake_get_snapshots, fake_take_snapshot):
        """``create_snapshot`` Does not raise ValueError if the first VM found is not the correct one"""
        fake_get_snapshots.return_value = []
        fake_take_snapshot.return_value = ('aabbcc', 1234, 2345)
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_vm2 = MagicMock()
        fake_vm2.name = 'SomeOtherVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm2, fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        snap_info = vmware.create_snapshot(username='sam',
                                           machine_name='SomeVM',
                                           shift=False,
                                           logger=fake_logger)
        expected = {'SomeVM': [{'id': 'aabbcc', 'created': 1234, 'expires': 2345}]}

        self.assertEqual(snap_info, expected)

    @patch.object(vmware.uuid, 'uuid4')
    @patch.object(vmware.time, 'time')
    @patch.object(vmware, 'consume_task')
    def test_take_snapshot(self, fake_consume_task, fake_time, fake_uuid4):
        """``_take_snapshot`` Returns new snapshot metadata as a tuple"""
        fake_vm = MagicMock()
        fake_create_time = 1234
        fake_expire_time = fake_create_time + vmware.const.VLAB_SNAPSHOT_EXPIRES_AFTER
        fake_time.return_value = 1234
        fake_uuid4.return_value = 'aabbccddeeff'

        meta_data = vmware._take_snapshot(fake_vm)
        expected_meta_data = ('aabbcc', fake_create_time, fake_expire_time)

        self.assertEqual(meta_data, expected_meta_data)

    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, '_get_snapshots')
    def test_delete_old_snaps(self, fake_get_snapshots, fake_consume_task):
        """``_delete_old_snaps`` Returns how many snapshots were deleted"""
        fake_vm = MagicMock()
        fake_logger = MagicMock()
        total_snaps = 5
        fake_snap = MagicMock()
        fake_snap.name = 'aabbcc_1234_4321'
        fake_get_snapshots.return_value = [fake_snap for x in range(total_snaps)]

        deleted_snap_count = vmware._deleted_old_snaps(fake_vm, fake_logger)
        expected_count = total_snaps - vmware.const.VLAB_MAX_SNAPSHOTS

        self.assertEqual(deleted_snap_count, expected_count)

    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_apply_snapshot(self, fake_vCenter, fake_get_snapshots, fake_consume_task):
        """``apply_snapshot`` Returns None when successful"""
        fake_snap = MagicMock()
        fake_snap.name = 'asdf_1234_4321'
        fake_get_snapshots.return_value = [fake_snap]
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        output = vmware.apply_snapshot(username='alice',
                                       snap_id='asdf',
                                       machine_name='SomeVM',
                                       logger=MagicMock())
        expected = None

        self.assertEqual(output, expected)
        self.assertTrue(fake_snap.snapshot.RevertToSnapshot_Task.called)

    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_apply_snapshot_no_snap(self, fake_vCenter, fake_get_snapshots, fake_consume_task):
        """``apply_snapshot`` Raises ValueError if the VM does not have a snap by the supplied ID"""
        fake_snap = MagicMock()
        fake_snap.name = 'asdf_1234_4321'
        fake_get_snapshots.return_value = [fake_snap]
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        with self.assertRaises(ValueError):
            vmware.apply_snapshot(username='alice',
                                  snap_id='qwerty',
                                  machine_name='SomeVM',
                                  logger=MagicMock())

    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, '_get_snapshots')
    @patch.object(vmware, 'vCenter')
    def test_apply_snapshot_no_vm(self, fake_vCenter, fake_get_snapshots, fake_consume_task):
        """``apply_snapshot`` Raises ValueError if the VM does not exist"""
        fake_snap = MagicMock()
        fake_snap.name = 'asdf_1234_4321'
        fake_get_snapshots.return_value = [fake_snap]
        fake_vm = MagicMock()
        fake_vm.name = 'SomeVM'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        with self.assertRaises(ValueError):
            vmware.apply_snapshot(username='alice',
                                  snap_id='asdf',
                                  machine_name='SomeOtherVM',
                                  logger=MagicMock())

    def test_get_snapshots(self):
        """``_get_snapshots`` Returns a list of all snapshots"""
        fake_snap2 = MagicMock()
        fake_snap2.name = 'fake2'
        snap_child = MagicMock()
        snap_child.name = 'child'
        snap_child.__iter__.return_value = [fake_snap2]
        fake_snap1 = MagicMock()
        fake_snap1.name = 'fake1'
        fake_snap1.childSnapshotList.__iter__.return_value = snap_child
        snap_root = MagicMock()
        snap_root.name = 'root'
        snap_root.__iter__.return_value = [fake_snap1]

        snaps = vmware._get_snapshots(snap_root)
        expected = [fake_snap1, fake_snap2]

        self.assertEqual(snaps, expected)


if __name__ == '__main__':
    unittest.main()
