# -*- coding: UTF-8 -*-
"""
Defines the RESTful API for working with snapshots in vLab
"""
import ujson
from flask import current_app
from flask_classy import request, route, Response
from vlab_inf_common.views import TaskView
from vlab_inf_common.vmware import vCenter, vim
from vlab_api_common import describe, get_logger, requires, validate_input


from vlab_snapshot_api.lib import const


logger = get_logger(__name__, loglevel=const.VLAB_SNAPSHOT_LOG_LEVEL)


class SnapshotView(TaskView):
    """API end point for working with snapshots in vLab"""
    route_base = '/api/1/inf/snapshot'
    POST_SCHEMA = { "$schema": "http://json-schema.org/draft-04/schema#",
                    "type": "object",
                    "description": "Create a snapshot; Maximum per VM is {}".format(const.VLAB_MAX_SNAPSHOTS),
                    "properties": {
                        "name": {
                            "description": "The virtual machine to take a snapshot of",
                            "type": "string"
                        },
                        "shift": {
                            "description": "When a VM has the maximum number of snaps, delete the oldest and take a new snapshot",
                            "type": "boolean",
                            "default": "false"
                        }
                    },
                    "required": ["name"]
                  }
    DELETE_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "Destroy a Snapshot",
                     "type": "object",
                     "properties": {
                        "id": {
                            "description": "The Snapshot unique ID",
                            "type": "string",
                        },
                        "name": {
                            "description": "The VM that owns the snapshot",
                            "type": "string"
                        }
                     },
                     "required": ["name", "id"]
                    }
    GET_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                  "description": "Display the Snapshot instances you own"
                 }
    PUT_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "Apply a Snapshot to a VM",
                     "type": "object",
                     "properties": {
                        "id": {
                            "description": "The Snapshot unique ID",
                            "type": "string",
                        },
                        "name": {
                            "description": "The VM that owns the snapshot",
                            "type": "string"
                        }
                     },
                     "required": ["name", "id"]
                    }

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @describe(post=POST_SCHEMA, delete=DELETE_SCHEMA, get=GET_SCHEMA, put=PUT_SCHEMA)
    def get(self, *args, **kwargs):
        """Display the Snapshot instances you own"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        task = current_app.celery_app.send_task('snapshot.show', [username, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=POST_SCHEMA)
    def post(self, *args, **kwargs):
        """Create a Snapshot"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        body = kwargs['body']
        machine_name = body['name']
        shift = body.get('shift', False)
        task = current_app.celery_app.send_task('snapshot.create', [username, machine_name, shift, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=DELETE_SCHEMA)
    def delete(self, *args, **kwargs):
        """Destroy a Snapshot"""
        username = kwargs['token']['username']
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        resp_data = {'user' : username}
        snap_id = kwargs['body'].get('id', -1)
        machine_name = kwargs['body']['name']
        task = current_app.celery_app.send_task('snapshot.delete', [username, snap_id, machine_name, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=PUT_SCHEMA)
    def put(self, *args, **kwargs):
        """Apply a snapshot to a VM"""
        username = kwargs['token']['username']
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        resp_data = {'user' : username}
        snap_id = kwargs['body']['id']
        machine_name = kwargs['body']['name']
        task = current_app.celery_app.send_task('snapshot.apply', [username, snap_id, machine_name, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp
