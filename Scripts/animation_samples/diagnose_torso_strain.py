"""Reproduce the known dead-bug axillary stretch on the evaluated mesh.

This is a defect regression probe, not an anatomical validity certificate.
The ROI is calibrated to the current unit-height Greek athlete source meshes.
A low edge ratio alone is insufficient: candidates must preserve arm volume,
rib shape and motion and pass multi-view review and collision checks.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np


def inspect(scene, frames):
    body = next(
        o
        for o in scene.objects
        if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
    )
    rest = np.array([tuple(v.co) for v in body.data.vertices])
    edges = np.array([tuple(e.vertices) for e in body.data.edges])
    lengths = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    roi = (
        (abs(rest[:, 1]) > 0.06)
        & (abs(rest[:, 1]) < 0.145)
        & (rest[:, 2] > 0.62)
        & (rest[:, 2] < 0.76)
    )
    selected = edges[np.all(roi[edges], axis=1) & (lengths > 1e-5)]
    base = np.linalg.norm(rest[selected[:, 0]] - rest[selected[:, 1]], axis=1)
    if len(selected) < 100:
        raise ValueError("Unexpected character topology/coordinates; recalibrate ROI")
    samples = []
    for frame in frames:
        scene.frame_set(frame)
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        if len(mesh.vertices) != len(rest):
            raise ValueError("Topology changed; correspondence invalid")
        points = np.array([tuple(v.co) for v in mesh.vertices])
        evaluated.to_mesh_clear()
        ratios = (
            np.linalg.norm(points[selected[:, 0]] - points[selected[:, 1]], axis=1)
            / base
        )
        samples.append(
            dict(
                frame=frame,
                p95=float(np.percentile(ratios, 95)),
                maximum=float(ratios.max()),
            )
        )
    return dict(
        status="stretch_regression"
        if any(x["p95"] > 1.8 for x in samples)
        else "strain_probe_passed_visual_review_still_required",
        threshold_p95=1.8,
        scope="Known axillary defect ROI; engineering regression threshold, not a physiological limit",
        edges_checked=len(selected),
        samples=samples,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--all-frames", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    bpy.ops.wm.open_mainfile(filepath=str(args.scene.resolve()))
    scene = bpy.context.scene
    if scene.get("exercise") != "dead_bug":
        parser.error("This probe is calibrated only for dead_bug")
    frames = [
        1,
        1 + scene.frame_end // 4,
        1 + scene.frame_end // 2,
        1 + 3 * scene.frame_end // 4,
        scene.frame_end + 1,
    ]
    if args.all_frames:
        frames = list(range(1, scene.frame_end + 2))
    result = inspect(scene, frames)
    result.update(
        scene_sha256=hashlib.sha256(args.scene.read_bytes()).hexdigest(),
        validator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    if result["status"] == "stretch_regression":
        raise SystemExit("FAIL: dead-bug rib/axilla stretch remains unresolved")
