"""Mechanical reports alone, stale reviews and modified evidence cannot publish."""
import hashlib, json, tempfile, unittest
from pathlib import Path
from deformation_gate import (
    require_deformation_pass,
    require_grip_orientation_pass,
    require_axilla_strain_pass,
    digest,
)


class DeformationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / "docs/animation-plan-v3"
        self.folder.mkdir(parents=True)
        self.scene = self.folder / "male/curl.blend"
        self.scene.parent.mkdir()
        self.scene.write_bytes(b"scene fixture")
        self.image = self.folder / "review.png"
        self.image.write_bytes(b"review fixture")
        self.report = {
            "male/curl": dict(
                status="automated_checks_passed",
                failures=[],
                scene_sha256=digest(self.scene),
                validator_sha256=digest(
                    Path(__file__).with_name("deformation_audit.py")
                ),
                frames=list(range(1, 122)),
            )
        }
        self.review = {
            "male/curl": dict(
                status="accepted",
                scene_sha256=digest(self.scene),
                views=["front", "side", "back"],
                frames=[1, 31, 61, 91],
                notes="Reviewed joint silhouette and contact poses",
                evidence={"docs/animation-plan-v3/review.png": digest(self.image)},
            )
        }
        self.save()

    def save(self):
        (self.folder / "deformation-validation.json").write_text(
            json.dumps(self.report)
        )
        (self.folder / "deformation-visual-review.json").write_text(
            json.dumps(self.review)
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_evidence(self):
        require_deformation_pass("male", "curl", root=self.root)

    def test_automated_pass_without_visual_review_is_rejected(self):
        self.review = {}
        self.save()
        with self.assertRaises(RuntimeError):
            require_deformation_pass("male", "curl", root=self.root)

    def test_changed_scene_is_rejected(self):
        self.scene.write_bytes(b"changed")
        with self.assertRaises(RuntimeError):
            require_deformation_pass("male", "curl", root=self.root)

    def test_changed_image_is_rejected(self):
        self.image.write_bytes(b"changed")
        with self.assertRaises(RuntimeError):
            require_deformation_pass("male", "curl", root=self.root)

    def test_partial_frame_audit_is_rejected(self):
        self.report["male/curl"]["frames"] = [1, 61]
        self.save()
        with self.assertRaises(RuntimeError):
            require_deformation_pass("male", "curl", root=self.root)


class GripOrientationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / "docs/animation-plan-v3"
        self.scene = self.folder / "male/cable_crunch.blend"
        self.scene.parent.mkdir(parents=True)
        self.scene.write_bytes(b"grip scene fixture")
        self.path = self.folder / "grip-orientation-validation.json"
        self.record = dict(
            passed=True,
            failures=[],
            frames=list(range(1, 122)),
            sceneSHA256=digest(self.scene),
            validatorSHA256=digest(
                Path(__file__).with_name("verify_grip_orientation.py")
            ),
            max_wrist_twist_deg=30,
            max_wrist_bend_deg=1,
            min_thumb_up_dot=0.7,
            min_palm_inward_dot=0.9,
        )

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.path.write_text(json.dumps({"male/cable_crunch": self.record}))

    def check(self):
        require_grip_orientation_pass("male", "cable_crunch", self.root)

    def test_complete_orientation_evidence(self):
        self.save()
        self.check()

    def test_missing_orientation_is_rejected(self):
        with self.assertRaises(RuntimeError):
            self.check()

    def test_bad_grip_even_with_pass_flag_is_rejected(self):
        for field, value in [
            ("max_wrist_twist_deg", 163),
            ("max_wrist_bend_deg", 61),
            ("min_thumb_up_dot", 0.04),
            ("min_palm_inward_dot", -0.9),
        ]:
            original = self.record[field]
            with self.subTest(field=field):
                self.record[field] = value
                self.save()
                with self.assertRaises(RuntimeError):
                    self.check()
            self.record[field] = original

    def test_partial_stale_or_failed_reports_are_rejected(self):
        for field, value in [
            ("frames", [61]),
            ("sceneSHA256", "old"),
            ("validatorSHA256", "old"),
            ("passed", False),
            ("failures", [{"frame": 61}]),
        ]:
            original = self.record[field]
            with self.subTest(field=field):
                self.record[field] = value
                self.save()
                with self.assertRaises(RuntimeError):
                    self.check()
            self.record[field] = original


class AxillaGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / "docs/animation-plan-v3/male"
        self.folder.mkdir(parents=True)
        self.scene = self.folder / "dead_bug.blend"
        self.scene.write_bytes(b"dead-bug fixture")
        self.record = dict(
            status="strain_probe_passed_visual_review_still_required",
            scene_sha256=digest(self.scene),
            validator_sha256=digest(
                Path(__file__).with_name("diagnose_torso_strain.py")
            ),
            threshold_p95=1.8,
            edges_checked=6000,
            samples=[dict(frame=f, p95=1.4) for f in range(1, 194)],
        )

    def tearDown(self):
        self.temp.cleanup()

    def check(self):
        (self.folder / "dead_bug-strain.json").write_text(json.dumps(self.record))
        require_axilla_strain_pass("male", "dead_bug", self.root)

    def test_complete_cycle(self):
        self.check()

    def test_pass_label_cannot_hide_known_stretch_or_nan(self):
        for value in [2.7914, float("nan")]:
            self.record["samples"][144]["p95"] = value
            with self.assertRaises(RuntimeError):
                self.check()

    def test_keyframes_only_are_not_a_complete_cycle(self):
        self.record["samples"] = self.record["samples"][::48]
        with self.assertRaises(RuntimeError):
            self.check()

    def test_changed_scene_requires_new_audit(self):
        self.scene.write_bytes(b"modified geometry")
        with self.assertRaises(RuntimeError):
            self.check()


if __name__ == "__main__":
    unittest.main()
