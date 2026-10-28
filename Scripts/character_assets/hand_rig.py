"""Five-digit FK hands for the selected Tripo sculpture topology.

Adds 3 deform bones per digit and normalized skin weights. Hand-local poses are
shared across exercises; the equipment contact frame controls wrist placement.
Coordinates are calibrated to these two source meshes, not a generic auto-rigger.
"""
import math
import bpy
from mathutils import Vector, Matrix

DIGITS = ("Thumb", "Index", "Middle", "Ring", "Pinky")


def install(rig, mesh, sex):
    male = sex == "male"
    # (x, unsigned y, z), CMC/MCP -> PIP -> DIP -> tip.
    lines = (
        {
            "Index": [
                (0.067, 0.259, 0.457),
                (0.070, 0.265, 0.436),
                (0.071, 0.261, 0.421),
                (0.071, 0.256, 0.409),
            ],
            "Middle": [
                (0.049, 0.260, 0.455),
                (0.052, 0.266, 0.432),
                (0.053, 0.261, 0.416),
                (0.053, 0.256, 0.404),
            ],
            "Ring": [
                (0.033, 0.260, 0.456),
                (0.035, 0.266, 0.435),
                (0.036, 0.262, 0.420),
                (0.036, 0.259, 0.407),
            ],
            "Pinky": [
                (0.018, 0.260, 0.459),
                (0.019, 0.264, 0.442),
                (0.020, 0.261, 0.427),
                (0.020, 0.258, 0.414),
            ],
            "Thumb": [
                (0.052, 0.239, 0.480),
                (0.071, 0.237, 0.467),
                (0.078, 0.235, 0.453),
                (0.078, 0.235, 0.440),
            ],
        }
        if male
        else {
            "Index": [
                (0.039, 0.230, 0.457),
                (0.042, 0.231, 0.440),
                (0.042, 0.225, 0.425),
                (0.042, 0.220, 0.416),
            ],
            "Middle": [
                (0.026, 0.230, 0.455),
                (0.028, 0.230, 0.435),
                (0.030, 0.222, 0.421),
                (0.031, 0.216, 0.411),
            ],
            "Ring": [
                (0.013, 0.228, 0.456),
                (0.014, 0.226, 0.437),
                (0.016, 0.219, 0.426),
                (0.017, 0.215, 0.419),
            ],
            "Pinky": [
                (0.001, 0.225, 0.459),
                (0.001, 0.223, 0.442),
                (0.002, 0.217, 0.431),
                (0.003, 0.215, 0.424),
            ],
            "Thumb": [
                (0.031, 0.211, 0.480),
                (0.045, 0.207, 0.467),
                (0.051, 0.208, 0.453),
                (0.052, 0.208, 0.444),
            ],
        }
    )
    centers = {}
    chains = {}
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for side, sign in [("Left", 1), ("Right", -1)]:
        centers[side] = Vector(
            (0.045 if male else 0.025, sign * (0.245 if male else 0.214), 0.451)
        )
        for digit, points in lines.items():
            pts = [Vector((x, sign * y, z)) for x, y, z in points]
            chains[side, digit] = pts
            parent = rig.data.edit_bones["mixamorig:" + side + "Hand"]
            for j in range(3):
                b = rig.data.edit_bones.new(f"mixamorig:{side}Hand{digit}{j+1}")
                b.head = pts[j]
                b.tail = pts[j + 1]
                b.parent = parent
                b.use_connect = j > 0
                b.align_roll(Vector((1, 0, 0)))
                parent = b
    bpy.ops.object.mode_set(mode="OBJECT")
    for side, digit in chains:
        for j in range(3):
            mesh.vertex_groups.new(name=f"mixamorig:{side}Hand{digit}{j+1}")
    # Nearest digit centerline identifies separate fingers, then weights blend
    # across phalange joints and into the existing palm. Thumb uses 3D distance.
    for v in mesh.data.vertices:
        p = v.co
        if p.z > 0.491 or abs(p.y) < (0.194 if not male else 0.215):
            continue
        side = "Left" if p.y > 0 else "Right"
        candidates = []
        for digit in DIGITS:
            pts = chains[side, digit]
            lengths = [(pts[j + 1] - pts[j]).length for j in range(3)]
            acc = 0
            best = None
            for j in range(3):
                delta = pts[j + 1] - pts[j]
                t = max(0, min(1, (p - pts[j]).dot(delta) / delta.length_squared))
                dist = (p - (pts[j] + t * delta)).length
                item = (dist, acc + t * lengths[j])
                if best is None or dist < best[0]:
                    best = item
                acc += lengths[j]
            # Root projection allows a smooth transition into the palm.
            along = (p - pts[0]).dot((pts[1] - pts[0]).normalized())
            candidates.append((best[0], digit, best[1], along, lengths))
        dist, digit, along, root_along, lengths = min(candidates)
        amount = max(0, min(1, (root_along + 0.007) / 0.014))
        if dist > 0.020 or amount <= 0:
            continue
        old = [(g.group, g.weight) for g in v.groups]
        for index, weight in old:
            mesh.vertex_groups[index].add([v.index], weight * (1 - amount), "REPLACE")
        joint1 = lengths[0]
        joint2 = joint1 + lengths[1]
        w = 0.0035
        if along < joint1 - w:
            weights = [(0, 1)]
        elif along < joint1 + w:
            t = (along - joint1 + w) / (2 * w)
            weights = [(0, 1 - t), (1, t)]
        elif along < joint2 - w:
            weights = [(1, 1)]
        elif along < joint2 + w:
            t = (along - joint2 + w) / (2 * w)
            weights = [(1, 1 - t), (2, t)]
        else:
            weights = [(2, 1)]
        for j, weight in weights:
            mesh.vertex_groups[f"mixamorig:{side}Hand{digit}{j+1}"].add(
                [v.index], amount * weight, "REPLACE"
            )
    rig["hand_rig_version"] = "individual-fingers-v1"
    rig["hand_rig_description"] = "30 FK deform bones; 5 digits x 3 segments x 2 hands"
    return centers, chains


def closed_points(chains, centers, side, digit):
    pts = chains[side, digit]
    center = centers[side]
    sign = 1 if side == "Left" else -1
    if digit == "Thumb":
        # Oppose across the bar from the other digits. Thumb pad ends on the
        # index finger side, forming a closed grip instead of a thumbless grip.
        target = [
            pts[0],
            Vector((pts[1].x, center.y - sign * 0.012, center.z + 0.012)),
            Vector((pts[1].x - 0.008, center.y - sign * 0.015, center.z - 0.002)),
            Vector((pts[1].x - 0.015, center.y - sign * 0.005, center.z - 0.010)),
        ]
        return target
    out = [pts[0].copy()]
    radius = math.hypot(pts[0].y - center.y, pts[0].z - center.z)
    angle = math.atan2(pts[0].z - center.z, sign * (pts[0].y - center.y))
    for a, b in zip(pts, pts[1:]):
        length = (b - a).length
        angle -= 2 * math.asin(min(0.98, length / (2 * radius)))
        out.append(
            Vector(
                (
                    b.x,
                    center.y + sign * radius * math.cos(angle),
                    center.z + radius * math.sin(angle),
                )
            )
        )
    return out


def pose_fingers(rig, chains, centers, side, frame, closed=True):
    hand = rig.pose.bones["mixamorig:" + side + "Hand"]
    deform = hand.matrix @ hand.bone.matrix_local.inverted()
    for digit in DIGITS:
        pts = (
            closed_points(chains, centers, side, digit)
            if closed
            else chains[side, digit]
        )
        for j in range(3):
            b = rig.pose.bones[f"mixamorig:{side}Hand{digit}{j+1}"]
            old = b.bone.tail_local - b.bone.head_local
            new = pts[j + 1] - pts[j]
            rot = old.rotation_difference(new).to_matrix().to_4x4()
            m = rot @ b.bone.matrix_local
            m.translation = pts[j]
            b.matrix = deform @ m
            b.rotation_mode = "QUATERNION"
            bpy.context.view_layer.update()
            b.keyframe_insert("location", frame=frame)
            b.keyframe_insert("rotation_quaternion", frame=frame)


def add_contact_clearance(rig, mesh, centers, radius_world=0.0155):
    """Small pose corrective prevents the fixed 28 mm grip from piercing skin.

    Invert the actual blended skin matrix, so the correction follows the hand
    in every exercise. This is a contact cleanup, not the source of finger curl.
    Set the keys to zero for an open hand or a different grip/shaft diameter.
    """
    if not mesh.data.shape_keys:
        mesh.shape_key_add(name="Basis")
    scale = rig.matrix_world.to_scale().x
    bones = {
        b.name: rig.matrix_world
        @ b.matrix
        @ b.bone.matrix_local.inverted()
        @ rig.matrix_world.inverted()
        @ mesh.matrix_world
        for b in rig.pose.bones
    }
    report = {}
    for side in ["Left", "Right"]:
        key = mesh.shape_key_add(name=side + "_Grip_Clearance")
        hand = rig.pose.bones["mixamorig:" + side + "Hand"]
        to_world = rig.matrix_world @ hand.matrix @ hand.bone.matrix_local.inverted()
        from_world = to_world.inverted()
        center = centers[side]
        changed = 0
        maximum = 0
        for v in mesh.data.vertices:
            if (
                sum(
                    g.weight
                    for g in v.groups
                    if ("mixamorig:" + side + "Hand")
                    in mesh.vertex_groups[g.group].name
                )
                < 0.65
            ):
                continue
            weights = [
                (mesh.vertex_groups[g.group].name, g.weight)
                for g in v.groups
                if g.weight > 0 and mesh.vertex_groups[g.group].name in bones
            ]
            total = sum(w for _, w in weights)
            skin = Matrix(
                [
                    [
                        sum(bones[n][r][c] * w / total for n, w in weights)
                        for c in range(4)
                    ]
                    for r in range(4)
                ]
            )
            posed = from_world @ (skin @ v.co)
            dy = posed.y - center.y
            dz = posed.z - center.z
            r = math.hypot(dy, dz)
            if r >= radius_world / scale:
                continue
            target = posed.copy()
            target.y = center.y + dy / max(r, 1e-8) * radius_world / scale
            target.z = center.z + dz / max(r, 1e-8) * radius_world / scale
            new = skin.inverted() @ (to_world @ target)
            key.data[v.index].co = new
            changed += 1
            maximum = max(maximum, (target - posed).length * scale)
        key.value = 1
        report[side] = {
            "vertices": changed,
            "max_surface_adjustment_m": maximum,
            "shaft_radius_m": 0.014,
            "clearance_radius_m": radius_world,
        }
    rig["hand_contact_corrective"] = str(report)
    return report
