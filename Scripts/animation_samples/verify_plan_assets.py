"""Verify coverage, every rendered frame, complete video decodes and optional App copies."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
from PIL import Image
from plan_exercises import PLAN_EXERCISES
from exercise_catalog import EXERCISES
from collision_gate import require_media_pass

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/animation-plan-v3"
BUILD = ROOT / "build/animation-plan-v3"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(plan_path, bundle=False):
    require_media_pass()
    plan = json.loads(plan_path.read_text())
    ids = {
        e["exerciseID"]
        for w in plan["weeks"]
        for d in w["workouts"]
        for e in d["exercises"]
    }
    coverage = json.loads((OUT / "coverage.json").read_text())
    assert coverage["planID"] == plan["id"] and coverage["revision"] == plan["revision"]
    assert ids == {e["exerciseID"] for e in coverage["exercises"]}
    available = {c["id"]: (n, c) for n, c in {**EXERCISES, **PLAN_EXERCISES}.items()}
    assert ids <= available.keys()
    inspections = {}
    for filename in ["hand-grip-validation.json", "scene-validation.json"]:
        inspections[filename] = json.loads((OUT / filename).read_text())
        assert inspections[filename]["status"] == "passed"
    samples = {}
    total_frames = 0
    for name, c in PLAN_EXERCISES.items():
        count = c.get("frames", 120)
        for sex in ["male", "female"]:
            folder = BUILD / sex / name
            scene = OUT / sex / f"{name}.blend"
            assert json.loads((folder / "render-source.json").read_text())[
                "sha256"
            ] == digest(scene), (sex, name, "stale render")
            for report_name, inspection in inspections.items():
                if report_name == "hand-grip-validation.json" and c.get("open_hands"):
                    continue
                assert inspection["samples"][f"{sex}/{name}"]["sceneSHA256"] == digest(
                    scene
                ), (sex, name, "stale inspection")
            checks = json.loads((folder / "motion-checks.json").read_text())
            assert (
                checks["frames_checked"] == count + 1
                and checks["max_limb_length_error_m"] < 1e-5
                and checks["max_grip_target_error_m"] < 1e-4
                and checks["loop_matrix_error"] < 1e-5
            )
            for f in range(1, count + 1):
                with Image.open(folder / f"frames/frame-{f:04d}.png") as im:
                    box = (
                        im.getchannel("A")
                        .point(lambda a: 255 if a > 16 else 0)
                        .getbbox()
                    )
                    assert (
                        box
                        and box[0] > 0
                        and box[1] > 0
                        and box[2] < im.width
                        and box[3] < im.height
                    ), (sex, name, f, "empty/clipped")
            video = OUT / sex / f"{name}.mp4"
            poster = OUT / sex / f"{name}-poster.png"
            probe = json.loads(
                subprocess.check_output(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_streams",
                        "-show_format",
                        "-of",
                        "json",
                        str(video),
                    ]
                )
            )
            v = probe["streams"][0]
            assert (
                v["width"],
                v["height"],
                v["codec_name"],
                v["pix_fmt"],
                v["r_frame_rate"],
            ) == (1280, 960, "h264", "yuv420p", "24/1")
            assert (
                int(v["nb_frames"]) == count
                and abs(float(probe["format"]["duration"]) - count / 24) < 0.01
            )
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-xerror",
                    "-i",
                    str(video),
                    "-f",
                    "null",
                    "-",
                ],
                check=True,
            )
            with Image.open(poster) as im:
                assert im.size == (1280, 960)
            shutil.copyfile(
                folder / "motion-checks.json", OUT / sex / f"{name}-motion-checks.json"
            )
            samples[f"{sex}/{name}"] = dict(
                id=c["id"],
                frames=count,
                duration=count / 24,
                videoSHA256=digest(video),
                sceneSHA256=digest(scene),
                loop_matrix_error=checks["loop_matrix_error"],
                clipped_frames=0,
            )
            total_frames += count
    if bundle:
        dest = ROOT / "Repcendo/Resources/ExerciseAnimations"
        catalog = json.loads((dest / "catalog.json").read_text())
        # Independently delivered library batches coexist with the plan assets.
        # Validate their evidence and exact copies, rather than rejecting them
        # or accepting arbitrary extra catalog entries.
        from library_exercises import LIBRARY_EXERCISES
        from library_delivery import collect_entries

        names = [n for n, c in LIBRARY_EXERCISES.items() if c["id"] in catalog]
        library_entries, library_copies = collect_entries(names)
        assert ids <= catalog.keys()
        assert set(catalog) == set(available) | set(library_entries)
        assert all(catalog[k] == v for k, v in library_entries.items())
        assert all(digest(source) == digest(target) for source, target in library_copies)
        for id, (name, c) in available.items():
            source = (
                OUT if name in PLAN_EXERCISES else ROOT / "docs/animation-samples-v2"
            )
            for sex in ["male", "female"]:
                variant = catalog[id]["variants"][sex]
                for field, suffix in [("video", ".mp4"), ("poster", "-poster.png")]:
                    assert (
                        digest(dest / variant[field])
                        == variant[field + "SHA256"]
                        == digest(source / sex / f"{name}{suffix}")
                    )
    report = dict(
        status="passed",
        planID=plan["id"],
        planRevision=plan["revision"],
        planExerciseCount=len(ids),
        newMotionCount=len(PLAN_EXERCISES),
        newVideoCount=len(samples),
        renderedFramesChecked=total_frames,
        appBundleChecked=bundle,
        samples=samples,
    )
    (OUT / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"PASS: {len(ids)} plan exercises; {len(samples)} new videos; {total_frames} rendered frames; bundle={bundle}"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--plan",
        type=Path,
        default=ROOT / "workout_plans/recomposition-4day-2026-10-28-v3.json",
    )
    p.add_argument("--bundle", action="store_true")
    a = p.parse_args()
    verify(a.plan, a.bundle)
