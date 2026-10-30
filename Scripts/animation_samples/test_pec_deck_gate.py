"""Rigid-link regressions and stale photo/scene evidence must block publication."""
import json, tempfile, unittest
from pathlib import Path
from deformation_gate import require_pec_deck_pass, digest, ROOT


class PecDeckGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "docs/animation-plan-v3"
        self.scene = self.folder / "male/reverse_fly.blend"
        self.scene.parent.mkdir(parents=True)
        self.scene.write_bytes(b"fixture")
        self.report = dict(
            passed=True,
            sceneSHA256=digest(self.scene),
            validatorSHA256=digest(Path(__file__).with_name("verify_pec_deck.py")),
            referenceSHA256=digest(ROOT / "docs/equipment-references/pec-deck.json"),
            frames=list(range(1, 122)),
            max_joint_error_m=0.0,
            max_grip_axis_error=0.0,
            link_length_variation_m={
                s + p: 0.0 for s in ["Left", "Right"] for p in ["boom", "hanger"]
            },
        )

    def check(self):
        (self.folder / "pec-deck-validation.json").write_text(
            json.dumps({"male/reverse_fly": self.report})
        )
        require_pec_deck_pass("male", "reverse_fly", self.root)

    def test_valid_complete_cycle(self):
        self.check()

    def test_stretch_or_nonfinite_rejected(self):
        for value in [0.02, float("nan")]:
            with self.subTest(value=value):
                self.report["link_length_variation_m"]["Lefthanger"] = value
                with self.assertRaises(RuntimeError):
                    self.check()

    def test_stale_reference_or_scene_rejected(self):
        for field in ["sceneSHA256", "referenceSHA256", "validatorSHA256"]:
            with self.subTest(field=field):
                old = self.report[field]
                self.report[field] = "old"
                with self.assertRaises(RuntimeError):
                    self.check()
                self.report[field] = old

    def test_incomplete_cycle_rejected(self):
        self.report["frames"] = [1, 31, 61, 91, 121]
        with self.assertRaises(RuntimeError):
            self.check()


if __name__ == "__main__":
    unittest.main()
