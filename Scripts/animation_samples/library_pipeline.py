"""Run bounded, explicit full-library batches without approving visual evidence.

Stages: bake, audit, review, compose, render, references, package, sync, page.
Run review/compose, inspect the sheets and write scene-matched decisions before
render. One scene's failure never approves it or changes an unrelated scene.
"""
import argparse
import concurrent.futures
import contextlib
import fcntl
import subprocess
import sys
import time
from pathlib import Path
from library_exercises import LIBRARY_EXERCISES
from library_gate import ROOT


@contextlib.contextmanager
def production_lock(root, key, slots=1):
    """Bound Blender memory across invocations and serialize each variant."""
    folder = root / "build/animation-library/locks"
    folder.mkdir(parents=True, exist_ok=True)
    handles = [(folder/f"{key}-{i}.lock").open("a") for i in range(slots)]
    acquired = None
    try:
        while acquired is None:
            for handle in handles:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                acquired = handle
                break
            if acquired is None:
                time.sleep(0.25)
        yield
    finally:
        if acquired is not None:
            fcntl.flock(acquired, fcntl.LOCK_UN)
        for handle in handles:
            handle.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=["bake","audit","review","compose","render","references","package","sync","page"])
    p.add_argument("--batch",default="001")
    p.add_argument("--exercises",nargs="+",choices=list(LIBRARY_EXERCISES))
    p.add_argument("--sex",choices=["male","female"])
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--workers",type=int,default=2,choices=[1,2])
    p.add_argument("--frames",default="all",help="Audit only: all, or comma-separated diagnostic frame numbers")
    p.add_argument("--dry-run",action="store_true")
    a = p.parse_args()
    if a.frames != "all" and a.stage != "audit":
        p.error("--frames is only available for diagnostic audits")
    names = a.exercises or [n for n,c in LIBRARY_EXERCISES.items() if c["batch"] == a.batch]
    if not names:
        p.error("No authored motions in this batch")
    root = a.root.resolve()
    # Fail the whole batch before starting any bake if a reference is missing.
    if a.stage == 'bake' and not a.dry_run:
        from motion_reference_gate import load_reference
        for name in names:
            load_reference(name)
    logdir = root/"build/animation-library/logs"
    logdir.mkdir(parents=True,exist_ok=True)
    if a.stage in ["sync","page"]:
        if a.dry_run:
            print(a.stage,names)
            return
        from library_delivery import sync,page
        sync(names,root) if a.stage=="sync" else page(root)
        return
    def run_unlocked(pair):
        sex,name = pair
        if a.stage in ["compose","package"]:
            if not a.dry_run:
                from library_delivery import compose,package
                (compose if a.stage=="compose" else package)(sex,name,root)
        else:
            prefix = ["blender","-b","-t","4","--python-exit-code","1","--python"]
            if a.stage in ["bake","references"]:
                commands = [[*prefix,str(ROOT/"Scripts/animation_samples/build_sculpture_scene.py"),"--","--sex",sex,"--exercise",name,"--output-root",str(root),*( ["--no-render"] if a.stage=="bake" else ["--view",view])] for view in ([None] if a.stage=="bake" else ["front","back"])]
            else:
                version = LIBRARY_EXERCISES[name].get("audit_version", 1)
                script = f"library_scene_v{version}.py" if version >= 3 else "library_scene.py"
                commands = [[*prefix,str(Path(__file__).with_name(script)),"--",a.stage,"--sex",sex,"--exercise",name,"--root",str(root)]]
                if a.stage == "audit":
                    commands[0].extend(["--frames",a.frames])
            if a.stage == "audit" and a.frames == "all" and LIBRARY_EXERCISES[name].get("unilateral"):
                commands.append([*prefix,str(Path(__file__).with_name("active_side_camera.py")),"--","audit","--sex",sex,"--exercise",name,"--root",str(root)])
            if a.stage == 'audit' and a.frames == 'all':
                from motion_reference_gate import requires_audit
                if requires_audit(sex, name, root):
                    commands.append([*prefix,str(Path(__file__).with_name('motion_reference_gate.py')),'--','--sex',sex,'--exercise',name,'--root',str(root)])
            for index,command in enumerate(commands):
                if a.dry_run:
                    print(" ".join(command))
                    continue
                log = logdir/f"{sex}-{name}-{a.stage}-{index}.log"
                with production_lock(root,"blender",2), log.open("w") as output:
                    result = subprocess.run(command,stdout=output,stderr=subprocess.STDOUT,cwd=ROOT)
                if result.returncode:
                    raise RuntimeError(f"{log}: {log.read_text()[-1600:]}")
        print(a.stage,sex,name,"DONE",flush=True)
    def run(pair):
        with production_lock(root,"variant-"+"-".join(pair)):
            run_unlocked(pair)
    pairs = [(sex,n) for n in names for sex in ([a.sex] if a.sex else ["male","female"])]
    errors = []
    with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
        futures = {pool.submit(run,pair):pair for pair in pairs}
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as error:
                errors.append(str(error))
                print("FAILED",futures[future],str(error),file=sys.stderr,flush=True)
    if errors:
        raise SystemExit(f"{len(errors)} variant(s) failed; no failed variant was approved. See stage logs.")


if __name__ == "__main__":
    main()
