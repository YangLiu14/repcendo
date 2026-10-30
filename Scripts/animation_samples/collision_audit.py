"""Collision repro against evaluated meshes (metres), never IK targets."""
import argparse, json, sys, hashlib
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan_exercises import PLAN_EXERCISES
from exercise_catalog import EXERCISES

CATALOG = {k: v for k, v in {**EXERCISES, **PLAN_EXERCISES}.items() if k != "squat"}
DIRECTIONS = [
    Vector(v).normalized()
    for v in [(0.173, 0.493, 0.852), (-0.381, 0.819, 0.428), (0.657, -0.281, 0.699)]
]


def inside(bvh, point):
    votes = 0
    for direction in DIRECTIONS:
        origin = point.copy()
        crossings = 0
        for _ in range(64):
            hit, _, _, _ = bvh.ray_cast(origin, direction, 10)
            if hit is None:
                break
            crossings += 1
            origin = hit + direction * 1e-5
        votes += crossings % 2
    return votes >= 2


def mesh_data(obj, graph):
    ev = obj.evaluated_get(graph)
    m = ev.to_mesh()
    m.calc_loop_triangles()
    a = np.empty(len(m.vertices) * 3)
    m.vertices.foreach_get("co", a)
    a = a.reshape(-1, 3)
    matrix = np.array(ev.matrix_world)
    a = a @ matrix[:3, :3].T + matrix[:3, 3]
    tris = [tuple(t.vertices) for t in m.loop_triangles]
    ev.to_mesh_clear()
    return a, tris


TOLERANCE = 0.002


def penetrations(samples, tree, lo, hi):
    candidates = np.flatnonzero(np.all((samples >= lo) & (samples <= hi), axis=1))
    hits = []
    for i in candidates:
        p = Vector(samples[i])
        near, normal, face, distance = tree.find_nearest(p)
        if distance > TOLERANCE and (p - near).dot(normal) < 0 and inside(tree, p):
            hits.append((float(distance), int(i), int(face)))
    return sorted(hits, reverse=True)


def surface_samples(points, triangles, spacing=0.012):
    """Vertices plus subdivided triangle edges catch long thin rods through skin."""
    edges = set()
    for a, b, c in triangles:
        edges.update(
            [tuple(sorted((a, b))), tuple(sorted((b, c))), tuple(sorted((c, a)))]
        )
    extra = [points]
    for a, b in edges:
        steps = int(np.ceil(np.linalg.norm(points[a] - points[b]) / spacing))
        if steps > 1:
            t = np.arange(1, steps)[:, None] / steps
            extra.append(points[a] * (1 - t) + points[b] * t)
    return np.concatenate(extra)


def region(label):
    for side in ["Left", "Right"]:
        if side in label:
            for part in ["Hand", "ForeArm", "Arm", "UpLeg", "Leg", "Foot", "ToeBase"]:
                if part in label:
                    return side + ("Foot" if part == "ToeBase" else part)
    return "Head" if "Head" in label or "Neck" in label else "Torso"


def self_intersections(coords, tris, tree, labels, rest_coords):
    """Nonlocal surface crossings. Local joint folds/finger contacts are separate.

    Shared topology and same anatomical patch aren't independent collision solids.
    Adjacent patch seams are excluded only within 14 cm in the undeformed model.
    Opposing limbs, hands vs torso/head, and distal limbs remain in scope.
    """
    tri = np.asarray(tris)
    centers = rest_coords[tri].mean(axis=1)
    regions = [region(labels[t[0]]) for t in tris]
    neighbors = {frozenset(("Head", "Torso"))}
    for side in ["Left", "Right"]:
        neighbors.update(
            frozenset(pair)
            for pair in [
                ("Torso", side + "Arm"),
                ("Torso", side + "UpLeg"),
                (side + "Arm", side + "ForeArm"),
                (side + "ForeArm", side + "Hand"),
                (side + "UpLeg", side + "Leg"),
                (side + "Leg", side + "Foot"),
            ]
        )
    groups = {}
    for a, b in tree.overlap(tree):
        if a >= b or regions[a] == regions[b] or set(tris[a]) & set(tris[b]):
            continue
        key = tuple(sorted((regions[a], regions[b])))
        if (
            frozenset(key) in neighbors
            and np.linalg.norm(centers[a] - centers[b]) < 0.14
        ):
            continue
        pa, pb = coords[tri[a]], coords[tri[b]]
        na = np.cross(pa[1] - pa[0], pa[2] - pa[0])
        nb = np.cross(pb[1] - pb[0], pb[2] - pb[0])
        la, lb = np.linalg.norm(na), np.linalg.norm(nb)
        if min(la, lb) < 1e-12:
            continue
        depth = min(
            max(0, float(-((pa - pb[0]) @ (nb / lb)).min())),
            max(0, float(-((pb - pa[0]) @ (na / la)).min())),
        )
        if depth <= TOLERANCE:
            continue
        entry = groups.setdefault(
            key,
            dict(
                object="Body self-contact",
                body_region="/".join(key),
                depth_m=0,
                triangle_pairs=0,
            ),
        )
        entry["triangle_pairs"] += 1
        if depth > entry["depth_m"]:
            entry.update(
                depth_m=depth,
                point=((pa.mean(0) + pb.mean(0)) / 2).tolist(),
                triangles=[a, b],
            )
    return list(groups.values())


def audit_scene(scene, frames, reverse=True, self_check=True):
    body = next(
        o
        for o in scene.objects
        if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
    )
    labels = [
        body.vertex_groups[
            max(
                (
                    g
                    for g in v.groups
                    if body.vertex_groups[g.group].name.startswith("mixamorig:")
                ),
                key=lambda g: g.weight,
            ).group
        ].name
        if v.groups
        else "unweighted"
        for v in body.data.vertices
    ]
    rest_coords = np.array(
        [tuple(body.matrix_world @ v.co) for v in body.data.vertices]
    )
    records = []
    for f in frames:
        scene.frame_set(f)
        graph = bpy.context.evaluated_depsgraph_get()
        coords, tris = mesh_data(body, graph)
        assert len(coords) == len(
            labels
        ), "Body topology changed: collision labels must be rebuilt"
        bodytree = BVHTree.FromPolygons(coords.tolist(), tris, all_triangles=True)
        blo, bhi = coords.min(0), coords.max(0)
        for obj in scene.objects:
            if obj.type != "MESH" or obj == body or obj.hide_render:
                continue
            points, faces = mesh_data(obj, graph)
            lo, hi = points.min(0), points.max(0)
            if np.any(hi < blo) or np.any(lo > bhi):
                continue
            tree = BVHTree.FromPolygons(points.tolist(), faces, all_triangles=True)
            hits = penetrations(coords, tree, lo, hi)
            if hits:
                depth, vertex, _ = hits[0]
                records.append(
                    dict(
                        frame=f,
                        object=obj.name,
                        depth_m=depth,
                        vertices=len(hits),
                        body_region=labels[vertex],
                        point=coords[vertex].tolist(),
                        kind="body-inside-equipment",
                    )
                )
            if reverse:
                samples = surface_samples(points, faces)
                hits = penetrations(samples, bodytree, blo, bhi)
                if hits:
                    depth, index, face = hits[0]
                    records.append(
                        dict(
                            frame=f,
                            object=obj.name,
                            depth_m=depth,
                            samples=len(hits),
                            body_region=labels[tris[face][0]],
                            point=samples[index].tolist(),
                            kind="equipment-inside-body",
                        )
                    )
        if self_check:
            for record in self_intersections(
                coords, tris, bodytree, labels, rest_coords
            ):
                records.append(
                    dict(frame=f, kind="nonlocal-self-intersection", **record)
                )
    return records


def probe(sex, name, frames, reverse=True, self_check=True, root=None):
    collection = (
        "animation-plan-v3" if name in PLAN_EXERCISES else "animation-samples-v2"
    )
    source = (root or ROOT) / f"docs/{collection}/{sex}/{name}.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    if frames == "all":
        frames = list(range(1, scene.frame_end + 2))
    elif frames == "key":
        frames = sorted(
            set(
                [1, scene.frame_end + 1]
                + [round(1 + scene.frame_end * i / 8) for i in range(8)]
            )
        )
    else:
        frames = [int(n) for n in frames.split(",")]
    records = audit_scene(scene, frames, reverse, self_check)
    return dict(
        sceneSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),
        auditVersion=2,
        validatorSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        tolerance_m=TOLERANCE,
        surface_sample_spacing_m=0.012,
        checks=dict(
            body_in_equipment=True,
            equipment_in_body=reverse,
            nonlocal_self_intersection=self_check,
        ),
        frames=frames,
        totalFrames=scene.frame_end + 1,
        hits=records,
        passed=not records,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--exercise", choices=list(CATALOG))
    p.add_argument("--sex", choices=["male", "female"])
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument(
        "--frames",
        default="all",
        help="all (production), key (9 poses), or comma-separated frames",
    )
    p.add_argument(
        "--body-only",
        action="store_true",
        help="Diagnostic only: skip reverse and self checks",
    )
    p.add_argument(
        "--output", type=Path, default=ROOT / "build/collision-baseline.json"
    )
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    result = {}
    for sex in [a.sex] if a.sex else ["male", "female"]:
        for name in [a.exercise] if a.exercise else CATALOG:
            r = probe(sex, name, a.frames, not a.body_only, not a.body_only, a.root)
            result[sex + "/" + name] = r
            print(
                "COLLISION",
                sex,
                name,
                len(r["hits"]),
                sorted(r["hits"], key=lambda x: x["depth_m"], reverse=True)[:5],
                flush=True,
            )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    assert not any(
        r["hits"] for r in result.values()
    ), "Geometry penetrations detected; see report"
