"""Photo-referenced equipment completion on baked poses; never edits the athlete.

Run after contact fitting. Original simplified hardware, not manufacturer CAD.
References and inspection notes: docs/equipment-references/equipment-audit.json.
"""
import json, math, hashlib
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
from equipment_refit_catalog import MOTIONS, LIBRARY_MOTIONS

VERSION = "photo-equipment-1"


class Hardware:
    def __init__(self, scene):
        self.s = scene
        self.dark = bpy.data.materials.get("Graphite steel")
        if self.dark is None:
            self.dark = next(
                m
                for m in bpy.data.materials
                if "steel" in m.name.lower() or "metal" in m.name.lower()
            )
        self.steel = next(
            (m for m in bpy.data.materials if "steel" in m.name.lower()), self.dark
        )
        self.created = []

    def cube(self, n, p, d, mat=None):
        bpy.ops.mesh.primitive_cube_add(size=1, location=p)
        o = bpy.context.object
        o.name = "EQ " + n
        o.dimensions = d
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        o.data.materials.append(mat or self.dark)
        mod = o.modifiers.new("Edge finish", "BEVEL")
        mod.width = 0.012
        mod.segments = 3
        o.modifiers.new("Normals", "WEIGHTED_NORMAL")
        self.created.append(o)
        return o

    def rod(self, n, a, b, r=0.025, mat=None):
        o = self.s.objects.get("EQ " + n)
        if o is None:
            bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=1)
            o = bpy.context.object
            o.name = "EQ " + n
            o.data.materials.append(mat or self.dark)
            self.created.append(o)
        self.place(o, a, b)
        return o

    def place(self, o, a, b):
        a, b = Vector(a), Vector(b)
        o.location = (a + b) / 2
        o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
        o.scale.z = (b - a).length

    def key(self, o, f):
        for p in ["location", "rotation_euler", "scale"]:
            o.keyframe_insert(p, frame=f)

    def stack(self, x, y, height=1.7):
        self.cube("stack base", (x, y, 0.08), (0.55, 0.42, 0.10))
        self.cube("stack rear guard", (x, y + 0.15, height / 2), (0.52, 0.035, height))
        for sign in [-1, 1]:
            self.rod(
                "stack guide " + str(sign),
                (x + sign * 0.16, y, 0.12),
                (x + sign * 0.16, y, height),
                0.012,
                self.steel,
            )
        self.cube("stack crown", (x, y, height), (0.54, 0.36, 0.10))
        plates = [
            self.cube(
                "selected plate " + str(i), (x, y, 0.13 + 0.04 * i), (0.43, 0.25, 0.035)
            )
            for i in range(10)
        ]
        return plates


def snapshot(scene):
    data = []
    for f in range(1, scene.frame_end + 2):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        data.append({o.name: o.matrix_world.copy() for o in scene.objects})
    return data


def point(m):
    return m.translation.copy()


def ends(m):
    return m @ Vector((0, 0, -0.5)), m @ Vector((0, 0, 0.5))


def refit(scene, name):
    if name not in MOTIONS:
        return
    if scene.get("equipment_refit_version"):
        raise ValueError("Already refitted; start from original scene")
    data = snapshot(scene)
    scene.frame_set(1)
    h = Hardware(scene)
    fixed = []
    rigid = []
    rules = []

    def freeze(o, m=None):
        o.animation_data_clear()
        if m is not None:
            o.matrix_world = m
        fixed.append(o.name)

    # Back-pad frames need a load path to the chassis, not a floating metal strip.
    if (
        name
        in ("incline_press", "shoulder_press", "leg_press", "leg_curl", "leg_extension")
        + LIBRARY_MOTIONS
    ):
        back = scene.objects["Back support"]
        m = back.matrix_world
        top = m @ Vector((0, -0.12, 0.20))
        bottom = Vector((0, top.y, 0.09))
        h.rod("back brace", bottom, top, 0.035)
        base = scene.objects["Seat base"]
        h.rod("rear chassis", bottom, (0, base.location.y, 0.09), 0.035)
    if name in ("pushdown", "pulldown", "straight_pulldown", "cable_crunch", "row"):
        old = [
            o
            for o in scene.objects
            if o.name.startswith(("Stack plate", "Weight stack"))
        ]
        for o in old:
            bpy.data.objects.remove(o, do_unlink=True)
        row = name == "row"
        cable = scene.objects["Cable" if row else "Tension cable"]
        lengths = [
            (ends(d[cable.name])[1] - ends(d[cable.name])[0]).length for d in data
        ]
        anchor = ends(data[0][cable.name])[1]
        x, y = 0, 1.55 if row else anchor.y + 0.16
        height = 1.35 if row else 2.18
        if row:
            bpy.data.objects.remove(scene.objects["Pulley tower"], do_unlink=True)
            for sign in [-1, 1]:
                h.cube(
                    "row tower " + str(sign),
                    (sign * 0.3, y, height / 2),
                    (0.06, 0.08, height),
                )
        plates = h.stack(x, y, height)
        top = Vector((x, y, height - 0.06))
        h.rod(
            "return pulley axle",
            top + Vector((-0.045, 0, 0)),
            top + Vector((0.045, 0, 0)),
            0.065,
            h.steel,
        )
        h.rod("pulley connector", anchor, top, 0.004)
        for i, plate in enumerate(plates):
            for f, length in enumerate(lengths, 1):
                plate.location.z = 0.13 + 0.04 * i + length - min(lengths)
                plate.keyframe_insert("location", frame=f)
        for f, length in enumerate(lengths, 1):
            line = h.rod(
                "stack return cable", (x, y, 0.51 + length - min(lengths)), top, 0.004
            )
            h.key(line, f)
        rules.append(
            dict(
                kind="cable_stack",
                cable=cable.name,
                plates=[o.name for o in plates],
                base_min=0.13,
            )
        )
        if name == "pulldown":
            pad = scene.objects["Thigh restraint"]
            p = pad.location
            h.rod(
                "thigh pad bracket", (0, p.y + 0.13, p.z), (0, p.y + 0.13, 0.12), 0.035
            )
            h.rod(
                "thigh pad axle",
                (-0.28, p.y + 0.13, p.z),
                (0.28, p.y + 0.13, p.z),
                0.025,
            )
            h.rod("thigh pad stem", (0, p.y + 0.13, p.z), (0, p.y + 0.06, p.z), 0.025)
            h.rod("pulldown floor chassis", (0, 0.05, 0.05), (0, y, 0.05), 0.035)
    if name in ("leg_curl", "leg_extension"):
        # Independent left/right knee pivots preserve the calibrated asymmetric anatomy.
        plates = h.stack(0.85, 0.20, 1.48)
        h.rod("stack chassis", (0.85, 0.20, 0.10), (0, 0.20, 0.10), 0.04)
        rig = next(o for o in scene.objects if o.type == "ARMATURE")
        for side, sign in [("Left", -1), ("Right", 1)]:
            lever = scene.objects["Knee lever " + side]
            roller = scene.objects["Shin roller " + side]
            a, b = ends(data[0][lever.name])
            pivot = a
            h.rod("knee pedestal " + side, (pivot.x, pivot.y, 0.12), pivot, 0.035)
            h.rod(
                "knee bearing " + side,
                pivot + Vector((-0.045, 0, 0)),
                pivot + Vector((0.045, 0, 0)),
                0.065,
                h.steel,
            )
            # Original contact-fit lengths vary slightly with soft tissue; rebuild
            # the axle to the actual roller, retaining the fixed knee pivot.
            for f, d in enumerate(data, 1):
                r = point(d[roller.name])
                end = Vector((pivot.x, r.y, r.z))
                h.place(lever, pivot, end)
                h.key(lever, f)
                axle = h.rod("roller axle " + side, end, r, 0.018, h.steel)
                h.key(axle, f)
            rigid.append(lever.name)
        # Visible cam, belt and stack lift encode the resisted knee rotation.
        axis = ends(data[0]["Knee lever Right"])[0]
        h.rod("cam axle", axis, (0.75, axis.y, axis.z), 0.025)
        h.rod("cam wheel", (0.67, axis.y, axis.z), (0.72, axis.y, axis.z), 0.13)
        h.rod("cam belt", (0.70, axis.y, axis.z + 0.13), (0.85, 0.20, 1.42), 0.006)
        start = ends(data[0]["Knee lever Right"])[1] - axis
        for f, d in enumerate(data, 1):
            v = ends(d["Knee lever Right"])[1] - axis
            lift = 0.13 * start.angle(v)
            for i, o in enumerate(plates):
                o.location.z = 0.13 + 0.04 * i + lift
                o.keyframe_insert("location", frame=f)
            line = h.rod(
                "stack return cable",
                (0.85, 0.20, 0.51 + lift),
                (0.85, 0.20, 1.42),
                0.004,
            )
            h.key(line, f)
        pad = scene.objects.get("Thigh hold-down")
        if pad:
            p = pad.location
            h.rod("hold down support", (0.40, p.y, 0.12), (0.40, p.y, p.z), 0.03)
            h.rod("hold down axle", (0.40, p.y, p.z), (0.25, p.y, p.z), 0.02)
    if name == "leg_press":
        # Use fitted footplate trajectory, and fix all guides to that same axis.
        plate = scene.objects["Sled footplate"]
        origin = point(data[0][plate.name])
        axis = Vector((0, 1, 1)).normalized()
        for sign in [-1, 1]:
            guide = scene.objects["Sled guide " + str(sign)]
            p = Vector((sign * 0.56, origin.y, origin.z - 0.07))
            h.place(guide, p - axis * 0.40, p + axis * 0.85)
            freeze(guide)
            upright = scene.objects["Sled upright " + str(sign)]
            end = p + axis * 0.85
            upright.animation_data_clear()
            upright.location = (end + Vector((end.x, end.y, 0.09))) / 2
            upright.dimensions.z = end.z - 0.09
            fixed.append(upright.name)
            h.rod(
                "lower rail foot " + str(sign),
                (sign * 0.56, (p - axis * 0.4).y, 0.09),
                p - axis * 0.40,
                0.04,
            )
            h.rod(
                "safety stop " + str(sign),
                p - axis * 0.34 - Vector((0.07, 0, 0)),
                p - axis * 0.34 + Vector((0.07, 0, 0)),
                0.04,
            )
            for f, d in enumerate(data, 1):
                pos = point(d[plate.name])
                p = Vector((sign * 0.56, pos.y, pos.z - 0.07))
                sleeve = h.rod(
                    "loading sleeve " + str(sign),
                    p,
                    p + Vector((sign * 0.34, 0, 0)),
                    0.025,
                    h.steel,
                )
                h.key(sleeve, f)
                for j in range(2):
                    center = p + Vector((sign * (0.13 + j * 0.07), 0, 0))
                    weight = h.rod(
                        "sled weight " + str(sign) + " " + str(j),
                        center - Vector((0.025, 0, 0)),
                        center + Vector((0.025, 0, 0)),
                        0.18,
                    )
                    h.key(weight, f)
                h.place(
                    scene.objects["Sled carriage " + str(sign)],
                    p - axis * 0.09,
                    p + axis * 0.09,
                )
                h.key(scene.objects["Sled carriage " + str(sign)], f)
                h.place(
                    scene.objects["Sled connector " + str(sign)],
                    p,
                    pos + Vector((sign * 0.38, 0.07, 0.07)),
                )
                h.key(scene.objects["Sled connector " + str(sign)], f)
            rules.append(
                dict(
                    kind="slide",
                    object=plate.name,
                    origin=list(origin),
                    axis=list(axis),
                    tolerance=0.0001,
                )
            )
    if name == "calf_raise":
        # Supported compound slide accommodates small fore-aft movement without
        # an impossible floating yoke or stretching a rigid shoulder arm.
        carriage = scene.objects["Calf moving carriage"]
        plates = h.stack(0.82, -0.30, 1.95)
        h.rod("calf stack chassis", (0.82, -0.30, 0.09), (0, -0.30, 0.09), 0.04)
        for sign in [-1, 1]:
            h.rod(
                "calf vertical guide " + str(sign),
                (sign * 0.48, -0.22, 0.15),
                (sign * 0.48, -0.22, 2.1),
                0.018,
                h.steel,
            )
            for f, d in enumerate(data, 1):
                c = point(d[carriage.name])
                p = Vector((sign * 0.48, -0.22, c.z + 0.10))
                bearing = h.rod(
                    "calf linear bearing " + str(sign),
                    p - Vector((0, 0, 0.08)),
                    p + Vector((0, 0, 0.08)),
                    0.045,
                )
                h.key(bearing, f)
                rail = h.rod(
                    "calf fore-aft guide " + str(sign),
                    p + Vector((0, -0.12, 0)),
                    p + Vector((0, 0.42, 0)),
                    0.02,
                    h.steel,
                )
                h.key(rail, f)
                # Upper crosshead sits clear above the head/neck and joins yoke.
                q = Vector((sign * 0.48, c.y, c.z + 0.10))
                sleeve = h.rod(
                    "calf horizontal bearing " + str(sign),
                    q - Vector((0, 0.05, 0)),
                    q + Vector((0, 0.05, 0)),
                    0.035,
                )
                h.key(sleeve, f)
                arm = h.rod(
                    "calf shoulder bridge " + str(sign),
                    q,
                    c + Vector((sign * 0.26, 0, 0.10)),
                    0.025,
                )
                h.key(arm, f)
                padname = "Shoulder pad" if sign == -1 else "Shoulder pad.001"
                padtop = point(d[padname]) + Vector((0, 0, 0.05))
                mount = h.rod(
                    "calf pad stem " + str(sign),
                    c + Vector((sign * 0.26, 0, 0.10)),
                    padtop,
                    0.025,
                )
                h.key(mount, f)
        zs = [point(d[carriage.name]).z for d in data]
        for f, z in enumerate(zs, 1):
            for i, o in enumerate(plates):
                o.location.z = 0.13 + 0.04 * i + z - min(zs)
                o.keyframe_insert("location", frame=f)
            c = point(data[f - 1][carriage.name])
            line = h.rod(
                "calf lift cable", (0.48, -0.22, c.z + 0.1), (0.48, -0.22, 2.13), 0.004
            )
            h.key(line, f)
            line = h.rod(
                "stack return cable",
                (0.82, -0.30, 0.51 + z - min(zs)),
                (0.82, -0.30, 2.13),
                0.004,
            )
            h.key(line, f)
        h.rod("calf top cable", (0.48, -0.22, 2.13), (0.82, -0.30, 2.13), 0.004)
        for x, y in [(0.48, -0.22), (0.82, -0.30)]:
            h.rod(
                "calf top pulley " + str(x),
                (x - 0.03, y, 2.13),
                (x + 0.03, y, 2.13),
                0.06,
                h.steel,
            )
    scene.frame_set(1)
    bpy.context.view_layer.update()
    for o in h.created:
        if o.animation_data is None:
            fixed.append(o.name)
    scene["equipment_refit_version"] = VERSION
    scene["equipment_reference_sha256"] = hashlib.sha256(
        (ROOT / "docs/equipment-references/equipment-audit.json").read_bytes()
    ).hexdigest()
    scene["equipment_constraints"] = json.dumps(
        dict(fixed=fixed, rigid=rigid, rules=rules)
    )
    from frame_plan_scene import fit

    fit(scene)
