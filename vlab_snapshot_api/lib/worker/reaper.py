# -*- coding: UTF-8 -*-
"""This script iterates VM inventory, and deletes expired snapshots"""
import time

from vlab_api_common.std_logger import get_logger
from vlab_inf_common.vmware import vCenter, vim, consume_task

from vlab_snapshot_api.lib import const
from vlab_snapshot_api.lib.worker.vmware import _get_snapshots

ONE_DAY = 30 * 60 * 24 # seconds in a day
LOOP_INTERVAL = 300 # 5 minutes


def is_expired(snap):
    """Determine if the snapshot is expired

    :Returns: Boolean

    :param snap: The name of the snapshot
    :type snap: String
    """
    exp_epoch = int(snap.split("_")[const.VLAB_SNAP_EXPIRES])
    current_time = int(time.time())
    return exp_epoch < current_time


def reap_snapshots(vcenter, logger):
    """Walk the VMs owned by users in vLab, and delete all expired VM snapshots.

    :Returns: None

    :param vcenter: The vCenter server that hosts the user's Virtual Machines
    :type vcenter: vlab_inf_common.vmware.vCenter

    :param logger: Handles logging messages while the reaper runs
    :type logger: logging.Logger
    """
    all_users = vcenter.get_by_name(name=const.INF_VCENTER_USERS_DIR, vimtype=vim.Folder)
    for username in all_users.childEntity:
        vms = vcenter.get_by_name(name=username.name, vimtype=vim.Folder)
        for vm in vms.childEntity:
            if vm.snapshot:
                vm_snaps = _get_snapshots(vm.snapshot.rootSnapshotList)
                for snap in vm_snaps:
                    if is_expired(snap.name):
                        logger.info("deleteing snap {} of VM {} owned by {}".format(snap, vm.name, username))
                        consume_task(snap.snapshot.RemoveSnapshot_Task(removeChildren=False))


def main(logger):
    """Entry point logic for deleting expired snapshots

    :Returns: None

    :param logger: Handles logging messages while the reaper runs
    :type logger: logging.Logger
    """
    logger.info('Snapshot Reaper starting')
    keep_running = True
    while keep_running:
        logger.info("Connecting to vCenter {} as {}".format(const.INF_VCENTER_SERVER, const.INF_VCENTER_USER))
        with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER,
                     password=const.INF_VCENTER_PASSWORD) as vcenter:
            try:
                start_loop = time.time()
                reap_snapshots(vcenter, logger)
            except Exception as doh:
                logger.exception(doh)
                keep_running = False
            else:
                ran_for = int(time.time() - start_loop)
                logger.debug('Took {} seconds to check all snapshots'.format(ran_for))
                loop_delta = LOOP_INTERVAL - ran_for
                sleep_for = max(0, loop_delta)
                time.sleep(sleep_for)


if __name__ == '__main__':
    main(logger=get_logger(__name__, loglevel=const.VLAB_SNAPSHOT_LOG_LEVEL))
