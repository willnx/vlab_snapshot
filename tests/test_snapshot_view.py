# -*- coding: UTF-8 -*-
"""
A suite of tests for the snapshot object
"""
import unittest
from unittest.mock import patch, MagicMock

import ujson
from flask import Flask
from vlab_api_common import flask_common
from vlab_api_common.http_auth import generate_v2_test_token


from vlab_snapshot_api.lib.views import snapshot


class TestSnapshotView(unittest.TestCase):
    """A set of test cases for the SnapshotView object"""
    @classmethod
    def setUpClass(cls):
        """Runs once for the whole test suite"""
        cls.token = generate_v2_test_token(username='bob')

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        app = Flask(__name__)
        snapshot.SnapshotView.register(app)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        # Mock Celery
        app.celery_app = MagicMock()
        cls.fake_task = MagicMock()
        cls.fake_task.id = 'asdf-asdf-asdf'
        app.celery_app.send_task.return_value = cls.fake_task

    def test_get_task(self):
        """SnapshotView - GET on /api/1/inf/snapshot returns a task-id"""
        resp = self.app.get('/api/1/inf/snapshot',
                            headers={'X-Auth': self.token})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_get_task_link(self):
        """SnapshotView - GET on /api/1/inf/snapshot sets the Link header"""
        resp = self.app.get('/api/1/inf/snapshot',
                            headers={'X-Auth': self.token})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/1/inf/snapshot/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_post_task(self):
        """SnapshotView - POST on /api/1/inf/snapshot returns a task-id"""
        resp = self.app.post('/api/1/inf/snapshot',
                             headers={'X-Auth': self.token},
                             json={'network': "someLAN",
                                   'name': "mySnapshotBox",
                                   'image': "someVersion"})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_post_task_link(self):
        """SnapshotView - POST on /api/1/inf/snapshot sets the Link header"""
        resp = self.app.post('/api/1/inf/snapshot',
                             headers={'X-Auth': self.token},
                             json={'network': "someLAN",
                                   'name': "mySnapshotBox",
                                   'image': "someVersion"})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/1/inf/snapshot/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_delete_task(self):
        """SnapshotView - DELETE on /api/1/inf/snapshot returns a task-id"""
        resp = self.app.delete('/api/1/inf/snapshot',
                               headers={'X-Auth': self.token},
                               json={'name' : 'SomeVM', 'id': '1234ad'})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_delete_task_link(self):
        """SnapshotView - DELETE on /api/1/inf/snapshot sets the Link header"""
        resp = self.app.delete('/api/1/inf/snapshot',
                               headers={'X-Auth': self.token},
                               json={'name' : 'SomeVM', 'id': '1234ad'})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/1/inf/snapshot/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)


    def test_put_task(self):
        """SnapshotView - PUT on /api/1/inf/snapshot returns a task-id"""
        resp = self.app.put('/api/1/inf/snapshot',
                               headers={'X-Auth': self.token},
                               json={'name' : 'SomeVM', 'id': '1234ad'})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_pust(self):
        """SnapshotView - PUT on /api/1/inf/snapshot sets the Link header"""
        resp = self.app.put('/api/1/inf/snapshot',
                            headers={'X-Auth': self.token},
                            json={'name' : 'SomeVM', 'id': '1234ad'})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/1/inf/snapshot/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)


if __name__ == '__main__':
    unittest.main()
