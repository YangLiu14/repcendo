"""Missing, stale and rejected evidence must stop independent batch publication."""
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from library_gate import require_scene_pass, digest, validator_hashes, specification_digest


class LibraryGateTests(unittest.TestCase):
    def setUp(self):
        # This suite isolates the original collision/deformation/camera gates.
        # The human-reference gate has its own full invalidation suite.
        reference = patch("motion_reference_gate.require_reference_pass", return_value="reference_checked")
        reference.start(); self.addCleanup(reference.stop)
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

    def camera_fixture(self, name):
        from active_side_camera import digest as camera_digest
        import active_side_camera
        frames = list(range(1,122))
        report = dict(passed=True, sceneSHA256=digest(self.folder/f"{name}.blend"),
            validatorSHA256=camera_digest(active_side_camera.__file__), activeSide="Left",
            frames=frames, minimumNearDepth=.2,
            samples=[dict(frame=f,workingShoulderNearDepth=.2) for f in frames])
        (self.folder/f"{name}-camera.json").write_text(json.dumps(report))
        self.review.update(activeSideViews=["main"],activeSideFrames=[1,31,61,91],activeSideEvidence=self.review["evidence"])
        return report

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
        self.camera_fixture(name)
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

    def test_single_bench_needs_complete_equipment_views(self):
        name = "single_bench_press"
        self.scene.rename(self.folder/f"{name}.blend")
        self.camera_fixture(name)
        self.audit["validatorSHA256"] = validator_hashes(name)
        self.audit["specificationSHA256"] = specification_digest(name)
        (self.folder/f"{name}-audit.json").write_text(json.dumps(self.audit))
        def check():
            (self.folder/f"{name}-review.json").write_text(json.dumps(self.review))
            return require_scene_pass("male", name, self.root)
        with self.assertRaises(RuntimeError):
            check()
        self.review.update(equipmentEvidence=self.review["evidence"], equipmentViews=["main","side"], equipmentFrames=[1,31,61])
        check()
        self.review["equipmentFrames"] = [1,61]
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


    def test_batch_six_requires_its_own_photo_and_motion_evidence(self):
        name = "db_kickback"
        self.review.update(gripEvidence=self.review["evidence"],gripSides=["Left","Right"],gripFrames=[1,31,61])
        self.scene.rename(self.folder/f"{name}.blend")
        self.audit["specificationSHA256"] = specification_digest(name)
        (self.folder/f"{name}-review.json").write_text(json.dumps(self.review))
        def check():
            (self.folder/f"{name}-audit.json").write_text(json.dumps(self.audit))
            return require_scene_pass("male", name, self.root)
        self.audit["validatorSHA256"] = validator_hashes("single_kickback")
        check()
        self.audit["validatorSHA256"]["equipment-reference"] = "stale photo record"
        with self.assertRaises(RuntimeError):
            check()
        self.audit["validatorSHA256"] = validator_hashes("single_curl")
        with self.assertRaises(RuntimeError):
            check()
        self.audit["validatorSHA256"] = validator_hashes(name)
        self.audit["specificationSHA256"] = specification_digest("seated_kickback")
        with self.assertRaises(RuntimeError):
            check()

    def test_batch_six_seated_requires_complete_equipment_views(self):
        name = "seated_bent_lateral_raise"
        self.review.update(gripEvidence=self.review["evidence"],gripSides=["Left","Right"],gripFrames=[1,31,61])
        self.scene.rename(self.folder/f"{name}.blend")
        self.audit["validatorSHA256"] = validator_hashes(name)
        self.audit["specificationSHA256"] = specification_digest(name)
        (self.folder/f"{name}-audit.json").write_text(json.dumps(self.audit))
        def check():
            (self.folder/f"{name}-review.json").write_text(json.dumps(self.review))
            return require_scene_pass("male", name, self.root)
        with self.assertRaises(RuntimeError):
            check()
        self.review.update(equipmentEvidence=self.review["evidence"], equipmentViews=["main","side"], equipmentFrames=[1,31,61])
        check()
        self.review["gripSides"] = ["Left"]
        with self.assertRaises(RuntimeError):
            check()
        self.review["gripSides"] = ["Left","Right"]
        self.review["equipmentViews"] = ["main"]
        with self.assertRaises(RuntimeError):
            check()


    def test_unilateral_rejects_far_side_stale_and_missing_main_review(self):
        name = "single_curl"
        self.scene.rename(self.folder/f"{name}.blend")
        self.audit.update(validatorSHA256=validator_hashes(name),specificationSHA256=specification_digest(name))
        (self.folder/f"{name}-audit.json").write_text(json.dumps(self.audit))
        report=self.camera_fixture(name)
        (self.folder/f"{name}-review.json").write_text(json.dumps(self.review))
        def check():
            return require_scene_pass("male",name,self.root)
        check()
        for change in [dict(sceneSHA256="old"),dict(validatorSHA256="old"),dict(activeSide="Right"),dict(frames=[1,61]),dict(minimumNearDepth=-.2),dict(samples=[dict(frame=f,workingShoulderNearDepth=-.2) for f in range(1,122)])]:
            (self.folder/f"{name}-camera.json").write_text(json.dumps({**report,**change}))
            with self.subTest(change=change.keys()), self.assertRaises(RuntimeError):check()
        (self.folder/f"{name}-camera.json").write_text(json.dumps(report))
        self.review.pop("activeSideEvidence")
        (self.folder/f"{name}-review.json").write_text(json.dumps(self.review))
        with self.assertRaises(RuntimeError):check()


if __name__ == "__main__":
    unittest.main()
