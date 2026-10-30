"""Photo-referenced pec/rear-delt machine; fixed vertical pivots, rigid arms.

Structure reference: docs/equipment-references/pec-deck.json (SS-FLY photo).
Character-facing +Y remains unchanged; the machine is oriented around the
shared pad for chest fly versus rear-delt fly. This is a simplified adaptation.
"""
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector
import bpy

REFERENCE = (
    Path(__file__).resolve().parents[2] / "docs/equipment-references/pec-deck.json"
)


def reference():
    data = json.loads(REFERENCE.read_text())
    if (
        not data.get("photo_inspected")
        or not data.get("photo_urls")
        or not data.get("observed_structure")
    ):
        raise ValueError("Inspect and document an equipment photograph before modeling")
    return hashlib.sha256(REFERENCE.read_bytes()).hexdigest()


class PecDeck:
    RADIUS = 0.58
    HEIGHT = 1.94

    def __init__(self, motion):
        self.m = m = motion
        self.reverse = m.name == "reverse_fly"
        self.tower_y = 0.96 if self.reverse else -0.65
        self.grip_z = 1.095 if m.args.sex == "male" else 1.08
        self.radius = self.RADIUS if m.args.sex == "male" else 0.555
        self.pivots = {s: Vector((s * 0.17, 0.02, self.HEIGHT)) for s in (-1, 1)}
        bpy.context.scene["equipment_reference_id"] = "pec-deck"
        bpy.context.scene["equipment_reference_sha256"] = reference()
        bpy.context.scene["equipment_mechanism_version"] = "pec-deck-fixed-pivots-1"
        self.cams = {}
        if m.args.view == "motion":
            self.build()

    def build(self):
        m = self.m
        y = self.tower_y
        m.items["Seat base"].dimensions = (0.14, abs(y) + 0.6, 0.08)
        m.items["Seat base"].location.y = y / 2
        # One selectorized tower with guard, rather than an empty portal frame.
        m.block("Pec stack guard", (0, y + 0.08, 0.87), (0.58, 0.18, 1.50))
        for s in (-1, 1):
            m.block(
                "Pec tower upright " + str(s), (s * 0.35, y, 1.00), (0.075, 0.12, 1.95)
            )
            m.block(
                "Pec tower foot " + str(s),
                (s * 0.35, y + (0.20 if self.reverse else -0.20), 0.045),
                (0.22, 0.50, 0.09),
            )
            m.rod(
                "Pec overhead support " + str(s),
                (s * 0.35, y, 1.94),
                self.pivots[s],
                0.043,
                m.DARK,
            )
            m.cylinder(
                "Pec guide rod " + str(s),
                (s * 0.21, y - 0.035, 0.14),
                (s * 0.21, y - 0.035, 1.48),
                0.011,
                m.STEEL,
            )
        m.block("Pec crown", (0, 0.02, 2.02), (0.55, 0.14, 0.09))
        for j in range(12):
            m.block(
                "Pec weight plate " + str(j),
                (0, y - 0.055, 0.18 + j * 0.041),
                (0.34, 0.13, 0.032),
            )
        m.cylinder(
            "Pec selector pin",
            (0.19, y - 0.15, 0.42),
            (0.19, y - 0.06, 0.42),
            0.018,
            m.ACCENT,
        )
        for s, side in m.SIDES.items():
            pivot = self.pivots[s]
            m.cylinder(
                "Pec pivot " + side,
                pivot - Vector((0, 0, 0.06)),
                pivot + Vector((0, 0, 0.08)),
                0.045,
                m.STEEL,
            )
            self.cams[s] = m.cylinder(
                "Pec cam " + side,
                pivot - Vector((0, 0, 0.045)),
                pivot - Vector((0, 0, 0.015)),
                0.12,
                m.DARK,
            )
            # Cam/guard area keeps the transmission above the user's reach.
            m.rod(
                "Pec drive cable " + side,
                pivot + Vector((0, 0, 0.03)),
                (s * 0.21, y, 1.92),
                0.005,
                m.STEEL,
            )
        m.cylinder(
            "Pec seat adjustment", (0, -0.08, 0.30), (0, -0.16, 0.30), 0.023, m.ACCENT
        )

    def target(self, s, d):
        angle = (-0.10 + 1.40 * d) if self.reverse else (1.05 - 1.15 * d)
        radial = Vector((s * math.sin(angle), math.cos(angle), 0))
        p = self.pivots[s] + radial * self.radius
        p.z = self.grip_z
        return p, radial, angle

    def animate(self, d):
        m = self.m
        for s, side in m.SIDES.items():
            grip, radial, angle = self.target(s, d)
            top = Vector((grip.x, grip.y, self.HEIGHT))
            m.rod("Pec rotating boom " + side, self.pivots[s], top, 0.032, m.DARK)
            m.rod("Pec descending arm " + side, top, m.grip_end(s), 0.027, m.DARK)
            self.cams[s].rotation_euler.z = -s * angle
            self.cams[s].keyframe_insert("rotation_euler", frame=m.f)


def fit_pad_frame(scene):
    """Attach the pad's support after the existing skin-contact fit moves it."""
    pad = scene.objects.get("Chest support") or scene.objects.get("Back support")
    reverse = scene["exercise"] == "reverse_fly"
    y = 0.96 if reverse else -0.65
    direction = 1 if reverse else -1
    p = pad.location + Vector((0, direction * (pad.dimensions.y / 2 + 0.03), 0))
    from mathutils import Vector as V

    # Create a rigid, visible connection from the pad to the tower.
    for name, a, b, r in [
        ("Pec pad upright", (0, p.y, p.z - 0.24), (0, p.y, p.z + 0.20), 0.029),
        ("Pec pad brace", (0, p.y, p.z - 0.20), (0, y, p.z - 0.20), 0.026),
    ]:
        a, b = V(a), V(b)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=32, radius=r, depth=(b - a).length, location=(a + b) / 2
        )
        o = bpy.context.object
        o.name = name
        o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
        o.data.materials.append(scene.objects["Pec stack guard"].data.materials[0])
