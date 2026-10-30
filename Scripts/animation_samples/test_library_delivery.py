"""A partial batch cannot replace a catalog or discard unrelated animation IDs."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from library_delivery import sync


class BatchSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dest = self.root/"Repcendo/Resources/ExerciseAnimations"
        self.dest.mkdir(parents=True)
        (self.dest.parent/"exercises.json").write_text(json.dumps([{"id":"0313"},{"id":"0043"}]))
        self.previous = {"0043":{"title":"existing","variants":{"untouched":True}}}
        self.catalog = self.dest/"catalog.json"
        self.catalog.write_text(json.dumps(self.previous))
        for sex in ["male","female"]:
            folder = self.root/"docs/animation-library"/sex
            folder.mkdir(parents=True)
            for suffix in [".mp4","-poster.png"]:
                (folder/("hammer_curl"+suffix)).write_bytes((sex+suffix).encode())

    def tearDown(self):
        self.temp.cleanup()

    def test_merge_preserves_unrelated_entries(self):
        with patch("library_delivery.require_media_pass"):
            sync(["hammer_curl"],self.root)
        result = json.loads(self.catalog.read_text())
        self.assertEqual(result["0043"],self.previous["0043"])
        self.assertEqual(set(result["0313"]["variants"]),{"male","female"})
        self.assertEqual(len(list(self.dest.glob("0313-*"))),4)

    def test_failed_female_preflight_does_not_write_male_or_catalog(self):
        def gate(sex,*args):
            if sex == "female":
                raise RuntimeError("Rejected review")
        with patch("library_delivery.require_media_pass",side_effect=gate):
            with self.assertRaises(RuntimeError):
                sync(["hammer_curl"],self.root)
        self.assertEqual(json.loads(self.catalog.read_text()),self.previous)
        self.assertEqual(list(self.dest.glob("0313-*")),[])


if __name__ == "__main__":
    unittest.main()
