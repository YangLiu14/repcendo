"""No Blender needed: partial and stale reports must never authorize exports."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import collision_gate as gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.scene = self.root / "docs/animation-plan-v3/male/curl.blend"
        self.scene.parent.mkdir(parents=True)
        self.scene.write_bytes(b"fixture scene")
        self.report = self.root / "report.json"
        self.entry = dict(
            passed=True,
            hits=[],
            auditVersion=2,
            validatorSHA256=gate.validator_digest(),
            frames=list(range(1, 122)),
            tolerance_m=0.002,
            checks=dict(
                body_in_equipment=True,
                equipment_in_body=True,
                nonlocal_self_intersection=True,
            ),
            sceneSHA256=hashlib.sha256(self.scene.read_bytes()).hexdigest(),
        )
        self.rootpatch = patch.object(gate, "ROOT", self.root)
        self.rootpatch.start()

    def tearDown(self):
        self.rootpatch.stop()
        self.temp.cleanup()

    def check(self, entry):
        self.report.write_text(json.dumps({"male/curl": entry}))
        return gate.require_collision_pass("male", "curl", self.report)

    def test_complete_current_report_passes(self):
        self.check(self.entry)

    def test_reject_each_missing_contract(self):
        for field, value in [
            ("passed", False),
            ("hits", [{"depth_m": 0.01}]),
            ("frames", [1, 61]),
            ("validatorSHA256", "old"),
            ("checks", {}),
            ("sceneSHA256", "old"),
        ]:
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                self.check(dict(self.entry, **{field: value}))

    def test_changed_scene_rejects_prior_pass(self):
        self.scene.write_bytes(b"changed geometry")
        with self.assertRaises(RuntimeError):
            self.check(self.entry)


if __name__ == "__main__":
    unittest.main()
