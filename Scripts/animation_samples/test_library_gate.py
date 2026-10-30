"""Missing, stale and rejected evidence must stop independent batch publication."""
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from library_gate import require_scene_pass, digest, validator_hashes, specification_digest


class LibraryGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root/"docs/animation-library/male"
        self.folder.mkdir(parents=True)
        self.scene = self.folder/"hammer_curl.blend"
        self.scene.write_bytes(b"fixture scene")
        self.image = self.folder/"review.jpg"
        self.image.write_bytes(b"fixture evidence")
        self.audit = dict(status="passed",sceneSHA256=digest(self.scene),validatorSHA256=validator_hashes(),frames=list(range(1,122)),collision=dict(hits=[],tolerance_m=0.002),deformation=dict(failures=[],review_frames=[1,31,61,91]),motion=dict(failures=[]))
        self.review = dict(status="accepted",sceneSHA256=digest(self.scene),views=["main","front","side","back","grip"],frames=[1,31,61,91],notes="Fixture review",evidence={str(self.image.relative_to(self.root)):digest(self.image)})
        self.audit["collision"]["checks"] = dict(body_in_equipment=True, equipment_in_body=True, nonlocal_self_intersection=True)

    def tearDown(self):
        self.temp.cleanup()

    def check(self):
        (self.folder/"hammer_curl-audit.json").write_text(json.dumps(self.audit))
        (self.folder/"hammer_curl-review.json").write_text(json.dumps(self.review))
        return require_scene_pass("male","hammer_curl",self.root)

    def test_complete_evidence(self):
        self.check()

    def test_pending_or_rejected_never_passes(self):
        for status in ["pending","rejected"]:
            self.review["status"] = status
            with self.subTest(status=status), self.assertRaises(RuntimeError):
                self.check()

    def test_partial_audit_never_passes(self):
        self.audit["frames"] = [1,61]
        with self.assertRaises(RuntimeError):
            self.check()

    def test_modified_scene_or_evidence_never_passes(self):
        for path in [self.scene,self.image]:
            original = path.read_bytes()
            path.write_bytes(b"changed")
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                self.check()
            path.write_bytes(original)

    def test_validator_changes_and_actual_failures_never_pass(self):
        self.audit["validatorSHA256"]["library_audit.py"] = "old"
        with self.assertRaises(RuntimeError):
            self.check()
        self.audit["validatorSHA256"] = validator_hashes()
        self.audit["motion"]["failures"] = [dict(check="reversed_grip")]
        with self.assertRaises(RuntimeError):
            self.check()

    def test_press_requires_its_validator_and_exact_specification(self):
        name = "db_bench_press"
        self.scene.rename(self.folder/f"{name}.blend")
        audit_path = self.folder/f"{name}-audit.json"
        (self.folder/f"{name}-review.json").write_text(json.dumps(self.review))
        def check():
            audit_path.write_text(json.dumps(self.audit))
            return require_scene_pass("male", name, self.root)
        with self.assertRaises(RuntimeError):
            check()
        self.audit["validatorSHA256"] = validator_hashes(name)
        with self.assertRaises(RuntimeError):
            check()
        self.audit["specificationSHA256"] = specification_digest(name)
        check()
        self.audit["specificationSHA256"] = specification_digest("neutral_bench_press")
        with self.assertRaises(RuntimeError):
            check()

    def test_unilateral_requires_own_validator_spec_and_photo_reference(self):
        name = "single_curl"
        self.scene.rename(self.folder/f"{name}.blend")
        (self.folder/f"{name}-review.json").write_text(json.dumps(self.review))
        def check():
            (self.folder/f"{name}-audit.json").write_text(json.dumps(self.audit))
            return require_scene_pass("male", name, self.root)
        self.audit["validatorSHA256"] = validator_hashes(name)
        self.audit["specificationSHA256"] = specification_digest(name)
        check()
        self.audit["validatorSHA256"]["equipment-reference"] = "stale"
        with self.assertRaises(RuntimeError):
            check()
        self.audit["validatorSHA256"] = validator_hashes(name)
        self.audit["specificationSHA256"] = specification_digest("single_hammer_curl")
        with self.assertRaises(RuntimeError):
            check()

    @patch("equipment_gate.require_equipment_pass")
    def test_batch_four_rejects_press_validator_and_other_grip_specification(self, equipment_gate):
        name = "incline_biceps_curl"
        self.scene.rename(self.folder/f"{name}.blend")
        (self.folder/f"{name}-review.json").write_text(json.dumps(self.review))
        def check():
            (self.folder/f"{name}-audit.json").write_text(json.dumps(self.audit))
            return require_scene_pass("male", name, self.root)
        self.audit["specificationSHA256"] = specification_digest(name)
        self.audit["validatorSHA256"] = validator_hashes("db_bench_press")
        with self.assertRaises(RuntimeError):
            check()
        self.audit["validatorSHA256"] = validator_hashes(name)
        check()
        self.audit["specificationSHA256"] = specification_digest("incline_hammer_curl")
        with self.assertRaises(RuntimeError):
            check()


if __name__ == "__main__":
    unittest.main()
