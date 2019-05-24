# -*- coding: UTF-8 -*-
"""
A suite of tests for the HTTP API schemas
"""
import unittest

from jsonschema import Draft4Validator, validate, ValidationError
from vlab_snapshot_api.lib.views import snapshot


class TestSnapshotViewSchema(unittest.TestCase):
    """A set of test cases for the schemas of /api/1/inf/snapshot"""

    def test_post_schema(self):
        """The schema defined for POST base end point on is valid"""
        try:
            Draft4Validator.check_schema(snapshot.SnapshotView.POST_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)


    def test_get_schema(self):
        """The schema defined for GET on base end point is valid"""
        try:
            Draft4Validator.check_schema(snapshot.SnapshotView.GET_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_delete_schema(self):
        """The schema defined for DELETE on base end point is valid"""
        try:
            Draft4Validator.check_schema(snapshot.SnapshotView.DELETE_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_put_schema(self):
        """The schema defined for PUT on base end point is valid"""
        try:
            Draft4Validator.check_schema(snapshot.SnapshotView.PUT_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)


if __name__ == '__main__':
    unittest.main()
