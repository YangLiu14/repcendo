"""Run independent Blender workers and aggregate collision evidence atomically."""
import argparse
import concurrent.futures
import json
import subprocess
from pathlib import Path
from collision_gate import ROOT, CATALOG, REPORT

p = argparse.ArgumentParser()
p.add_argument("--exercise", choices=list(CATALOG))
p.add_argument("--exercises", nargs="+", choices=list(CATALOG))
p.add_argument("--sex", choices=["male", "female"])
p.add_argument("--frames", default="all")
p.add_argument("--workers", type=int, default=2)
p.add_argument("--root", type=Path, default=ROOT)
a = p.parse_args()
folder = a.root / "build/collision-audit"
folder.mkdir(parents=True, exist_ok=True)


def run(pair):
    sex, name = pair
    output = folder / f'{sex}-{name}-{a.frames.replace(",","_")}.json'
    log = output.with_suffix(".log")
    with log.open("w") as out:
        proc = subprocess.run(
            [
                "/opt/homebrew/bin/blender",
                "-b",
                "-t",
                "2",
                "--python-exit-code",
                "1",
                "--python",
                str(Path(__file__).with_name("collision_audit.py")),
                "--",
                "--sex",
                sex,
                "--exercise",
                name,
                "--frames",
                a.frames,
                "--output",
                str(output),
                "--root",
                str(a.root.resolve()),
            ],
            stdout=out,
            stderr=subprocess.STDOUT,
            cwd=ROOT,
        )
    if not output.exists():
        raise RuntimeError(f"{log}: {log.read_text()[-1800:]}")
    r = json.loads(output.read_text())
    if proc.returncode and all(v.get("passed") for v in r.values()):
        raise RuntimeError(f"{log}: Blender failed after audit")
    print(
        f"{sex}/{name}: "
        + (
            "PASS"
            if not proc.returncode
            else f'FAIL ({len(next(iter(r.values()))["hits"])} findings)'
        ),
        flush=True,
    )
    return r


pairs = [
    (s, n)
    for s in ([a.sex] if a.sex else ["male", "female"])
    for n in ([a.exercise] if a.exercise else a.exercises or CATALOG)
]
result = {}
with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
    for r in pool.map(run, pairs):
        result.update(r)
output = (
    a.root / "docs/animation-plan-v3/collision-validation.json"
    if a.frames == "all"
    else folder / "key-review.json"
)
previous = (
    json.loads(output.read_text())
    if output.exists() and (a.sex or a.exercise or a.exercises)
    else {}
)
previous.update(result)
temp = output.with_suffix(".tmp")
temp.write_text(json.dumps(previous, indent=2) + "\n")
temp.replace(output)
if any(not v["passed"] for v in result.values()):
    raise SystemExit("Collision gate failed; inspect " + str(output))
