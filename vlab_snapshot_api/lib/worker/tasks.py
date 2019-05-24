# -*- coding: UTF-8 -*-
"""
Entry point logic for available backend worker tasks
"""
from celery import Celery
from vlab_api_common import get_task_logger

from vlab_snapshot_api.lib import const
from vlab_snapshot_api.lib.worker import vmware

app = Celery('snapshot', backend='rpc://', broker=const.VLAB_MESSAGE_BROKER)


@app.task(name='snapshot.show', bind=True)
def show(self, username, txn_id):
    """Obtain all the snapshots on the machines a user owns

    :Returns: Dictionary

    :param username: The name of the user who wants info about snapshots in their lab
    :type username: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_SNAPSHOT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        info = vmware.show_snapshot(username)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
        resp['content'] = info
    return resp


@app.task(name='snapshot.create', bind=True)
def create(self, username, machine_name, shift, txn_id):
    """Create a new snapshot on a user's virtual machine

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new Snapshot
    :type username: String

    :param machine_name: The name of the virtual machine to snapshot
    :type machine_name: String

    :param shift: When a VM already has the maximum number of snapshots, automatically
                  delete the oldest snapshot and take a new snapshot.
    :type shift: Boolean

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_SNAPSHOT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        resp['content'] = vmware.create_snapshot(username, machine_name, shift, logger)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    logger.info('Task complete')
    return resp


@app.task(name='snapshot.delete', bind=True)
def delete(self, username, snap_id, machine_name, txn_id):
    """Destroy a Snapshot

    :Returns: Dictionary

    :param username: The name of the user who wants to delete an instance of Snapshot
    :type username: String

    :param snap_id: The snapshot to destroy
    :type snap_id: Integer

    :param machine_name: The name of the virtual machine which owns the snapshot
    :type machine_name: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_SNAPSHOT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        vmware.delete_snapshot(username, snap_id, machine_name, logger)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
    return resp


@app.task(name='snapshot.apply', bind=True)
def apply(self, username, snap_id, machine_name, txn_id):
    """Apply a snapshot to a virtual machine

    :Returns: Dictionary

    :param username: The name of the user who wants to apply a Snapshot
    :type username: String

    :param snap_id: The snapshot to apply
    :type snap_id: Integer

    :param machine_name: The name of the virtual machine to apply the snapshot to
    :type machine_name: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_SNAPSHOT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        vmware.apply_snapshot(username, snap_id, machine_name, logger)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
    return resp
