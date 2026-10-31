"""Refine coarse grip-cavity chords before thickness-preserving contact fitting.

Subdivide existing hand faces with interpolated UVs/weights; never remove faces
or move the shaft. Angular resolution limits chords that would cut a round grip.
"""
import math
import bpy
import bmesh
from mathutils import Vector


def refine_cavity(body, grips, sides, rounds=3):
    counts = []
    for _ in range(rounds):
        bpy.context.view_layer.update()
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        skin = evaluated.to_mesh()
        points = [evaluated.matrix_world @ v.co for v in skin.vertices]
        evaluated.to_mesh_clear()
        selected = set()
        for sign, grip in grips.items():
            side = sides[sign]
            groups = {g.index for g in body.vertex_groups if g.name.startswith('mixamorig:'+side+'Hand')}
            hand = {v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in groups) > .65}
            inverse = grip.matrix_world.inverted()
            local = {i: inverse @ points[i] for i in hand}
            for edge in body.data.edges:
                a, b = edge.vertices
                if a not in hand or b not in hand:
                    continue
                p, q = local[a], local[b]
                ra, rb = math.hypot(p.y,p.z), math.hypot(q.y,q.z)
                if max(ra, rb) > .045 or min(ra, rb) < 1e-7:
                    continue
                angle = math.acos(max(-1, min(1, (p.y*q.y+p.z*q.z)/(ra*rb))))
                if angle > math.radians(20):
                    selected.add(edge.index)
        counts.append(len(selected))
        if not selected:
            break
        bm = bmesh.new(); bm.from_mesh(body.data); bm.edges.ensure_lookup_table()
        bmesh.ops.subdivide_edges(bm, edges=[bm.edges[i] for i in selected], cuts=1, use_grid_fill=True)
        bm.to_mesh(body.data); bm.free(); body.data.update()
    return dict(angular_limit_degrees=20, subdivided_edges_per_round=counts, vertices=len(body.data.vertices))
