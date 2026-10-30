"""Audit saved scenes without approving their visual quality automatically."""
import argparse, concurrent.futures, json, subprocess, sys
from pathlib import Path
from collision_gate import ROOT, CATALOG
from plan_exercises import PLAN_EXERCISES

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--root", type=Path, default=ROOT)
p.add_argument("--workers", type=int, default=2)
p.add_argument("--exercises", nargs="+", choices=list(CATALOG))
a = p.parse_args()
folder = a.root / "build/deformation-audit"
folder.mkdir(parents=True, exist_ok=True)


def run(pair):
    sex, name = pair
    collection = (
        "animation-plan-v3" if name in PLAN_EXERCISES else "animation-samples-v2"
    )
    output = folder / f"{sex}-{name}.json"
    log = output.with_suffix(".log")
    with log.open("w") as f:
        result = subprocess.run(
            [
                "/opt/homebrew/bin/blender",
                "-b",
                "-t",
                "2",
                "--python-exit-code",
                "1",
                "--python",
                str(Path(__file__).with_name("deformation_audit.py")),
                "--",
                "--scene",
                str(a.root / f"docs/{collection}/{sex}/{name}.blend"),
                "--output",
                str(output),
            ],
            stdout=f,
            stderr=subprocess.STDOUT,
        )
    if not output.exists():
        raise RuntimeError(log.read_text()[-2000:])
    data = json.loads(output.read_text())
    if result.returncode and data.get("status") != "failed":
        raise RuntimeError(log.read_text()[-2000:])
    print(sex, name, data["status"], flush=True)
    return sex + "/" + name, data


with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
    report = dict(
        pool.map(
            run, [(s, n) for s in ["male", "female"] for n in a.exercises or CATALOG]
        )
    )
target = a.root / "docs/animation-plan-v3/deformation-validation.json"
previous = json.loads(target.read_text()) if target.exists() and a.exercises else {}
previous.update(report)
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(previous, indent=2) + "\n")
if any(r["failures"] for r in report.values()):
    sys.exit("Deformation regression failed; review report")
