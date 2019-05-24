# -*- coding: UTF-8 -*-
"""Business logic for backend worker tasks"""
import uuid
import time
import random
import os.path
from vlab_inf_common.vmware import vCenter, Ova, vim, virtual_machine, consume_task

from vlab_snapshot_api.lib import const


def show_snapshot(username):
    """Obtain information about snapshot of virtual machines in a user's lab

    :Returns: Dictionary

    :param username: The name of the user who wants info about snapshots in their lab
    :type username: String
    """
    info = {}
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        snapshot_vms = {}
        for vm in folder.childEntity:
            snapshot_vms[vm.name] = []
            if vm.snapshot:
                for snap in _get_snapshots(vm.snapshot.rootSnapshotList):
                    snap_data = snap.name.split('_')
                    snap_id = snap_data[const.VLAB_SNAP_ID]
                    snap_created = snap_data[const.VLAB_SNAP_CREATED]
                    snap_exp = snap_data[const.VLAB_SNAP_EXPIRES]
                    snapshot_vms[vm.name].append({'id': snap_id,
                                                  'created' : snap_created,
                                                  'expires' : snap_exp})
    return snapshot_vms


def delete_snapshot(username, snap_id, machine_name, logger):
    """Destroy a snapshot

    :Returns: None

    :param username: The user who wants to delete their jumpbox
    :type username: String

    :param snap_id: The snapshot to destroy
    :type snap_id: Integer

    :param machine_name: The name of the virtual machine which owns the snapshot
    :type machine_name: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                if entity.snapshot:
                    for snap in _get_snapshots(entity.snapshot.rootSnapshotList):
                        snap_data = snap.name.split('_')
                        if snap_data[const.VLAB_SNAP_ID] == snap_id:
                            logger.info('Deleting snapshot {} from {}'.format(snap.name, machine_name))
                            consume_task(snap.snapshot.RemoveSnapshot_Task(removeChildren=False))
                            # return exits nested for-loop; break just stop immediate parent loop
                            return None
                    else:
                        error = 'VM has no snapshot by ID {}'.format(snap_id)
                        raise ValueError(error)
            else:
                error = 'No VM named {} found in inventory'.format(machine_name)
                logger.info(error)
                raise ValueError(error)


def create_snapshot(username, machine_name, shift, logger):
    """Deploy a new instance of Snapshot

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new Snapshot
    :type username: String

    :param machine_name: The name of the virtual machine to snapshot
    :type machine_name: String

    :param shift: When a VM already has the maximum number of snapshots, automatically
                  delete the oldest snapshot and take a new snapshot.
    :type shift: Boolean

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER,
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                logger.info("Creating snapshot for {}".format(machine_name))
                try:
                    total_snaps = len(_get_snapshots(entity.snapshot.rootSnapshotList))
                except AttributeError:
                    # entity.snapshot is None when there are no snapshots...
                    total_snaps = 0
                logger.info("Existing snap count: {}".format(total_snaps))
                if total_snaps >= const.VLAB_MAX_SNAPSHOTS:
                    if shift:
                        # delete oldest, make new one
                        snap_id, created, expires = _take_snapshot(entity)
                        snaps_deleted = _deleted_old_snaps(entity, logger)
                        logger.info('Deleted {} snapshots for shift functionality'.format(snaps_deleted))
                        return {machine_name: [{'id': snap_id,
                                                'created': created,
                                                'expires': expires}]}
                    else:
                        error = 'Unable to create snapshot. VM has {}, max allowed is {}'.format(total_snaps, const.VLAB_MAX_SNAPSHOTS)
                        logger.info(error)
                        raise ValueError(error)
                else:
                    snap_id, created, expires = _take_snapshot(entity)
                    return {machine_name: [{'id': snap_id,
                                            'created': created,
                                            'expires': expires}]}
            else:
                error = 'No VM named {} found in inventory'.format(machine_name)
                logger.info(error)
                raise ValueError(error)


def _take_snapshot(the_vm, dump_memory=True, quiesce=False, description=''):
    """Take a new snapshot of the virtual machine.

    :Returns: Tuple (snap_id, created_timestamp, expires_timesampt)

    :param the_vm: The virtual machine with snapshots to delete
    :type the_vm: vim.VirtualMachine

    :param dump_memory: When True, includes the running memory state of the VM in
                        the snapshot. Default True.
    :type dump_memory: Boolean

    :param quiesce: When the VM  has VMwareTools installed, setting this flag to
                    True waits to create a snapshot until after buffers in the VM
                    are flushed to disk. Useless to use when ``dump_memory`` is
                    set to True. Default False
    :type quiesce: Boolean
    """
    created = int(time.time())
    snap_id = '{}'.format(uuid.uuid4())[:6]
    expires = created + const.VLAB_SNAPSHOT_EXPIRES_AFTER
    snap_name = '{}_{}_{}'.format(snap_id, created, expires)
    consume_task(the_vm.CreateSnapshot(snap_name, description, dump_memory, quiesce))
    return snap_id, created, expires


def _deleted_old_snaps(the_vm, logger):
    """Delete all snapshots such that const.VLAB_SNAP_CREATED is not exceeded.
    Returns the number of snapshots deleted.

    :Returns: Integer

    :param the_vm: The virtual machine with snapshots to delete
    :type the_vm: vim.VirtualMachine
    """
    all_snaps = _get_snapshots(the_vm.snapshot.rootSnapshotList)
    all_snaps = sorted(all_snaps, key=lambda x: int(x.name.split('_')[const.VLAB_SNAP_CREATED]))
    delete_count = len(all_snaps) - const.VLAB_MAX_SNAPSHOTS
    to_delete = []
    for _ in range(delete_count):
        to_delete.append(all_snaps.pop(0))
    for snap in to_delete:
        consume_task(snap.snapshot.RemoveSnapshot_Task(removeChildren=False))
    return delete_count


def apply_snapshot(username, snap_id, machine_name, logger):
    """Apply a snapshot to a virtual machine

    :Returns: None

    :param username: The user who wants to delete their jumpbox
    :type username: String

    :param snap_id: The snapshot to destroy
    :type snap_id: Integer

    :param machine_name: The name of the virtual machine which owns the snapshot
    :type machine_name: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                if entity.snapshot:
                    for snap in _get_snapshots(entity.snapshot.rootSnapshotList):
                        snap_data = snap.name.split('_')
                        if snap_data[const.VLAB_SNAP_ID] == snap_id:
                            logger.info("Applying snapshot {} to {}".format(snap.name, machine_name))
                            consume_task(snap.snapshot.RevertToSnapshot_Task())
                            return None
            else:
                error = 'No VM named {} found in inventory'.format(machine_name)
                logger.info(error)
                raise ValueError(error)



def _get_snapshots(snap_root):
    snapshots = []
    branches = [snap_root]
    while branches:
        current = branches.pop(0)
        for snap_object in current:
            snapshots.append(snap_object)
            for child in snap_object.childSnapshotList:
                branches.append([child])
    return snapshots
