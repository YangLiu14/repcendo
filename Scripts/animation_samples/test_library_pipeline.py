"""Exercise production limits with real competing Python processes."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ProductionConcurrencyTests(unittest.TestCase):
    def peak(self, slots):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = """
import json, sys, time
from pathlib import Path
from library_pipeline import production_lock
root, slots, index = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
with production_lock(root, 'shared', slots):
    start = time.monotonic_ns()
    time.sleep(0.12)
    end = time.monotonic_ns()
(root / (index + '.json')).write_text(json.dumps([start, end]))
"""
            def run(index):
                subprocess.run([sys.executable, "-c", code, str(root), str(slots), str(index)],
                               cwd=Path(__file__).parent, check=True, timeout=15)
            with concurrent.futures.ThreadPoolExecutor(6) as pool:
                list(pool.map(run, range(6)))
            events = []
            for path in root.glob("*.json"):
                start, end = json.loads(path.read_text())
                events.extend([(start, 1), (end, -1)])
            active = peak = 0
            for _, delta in sorted(events):
                active += delta
                peak = max(peak, active)
            self.assertEqual(active, 0)
            return peak

    def test_blender_limit_applies_across_processes(self):
        self.assertEqual(self.peak(2), 2)

    def test_variant_stages_do_not_overlap(self):
        self.assertEqual(self.peak(1), 1)


if __name__ == "__main__":
    unittest.main()
