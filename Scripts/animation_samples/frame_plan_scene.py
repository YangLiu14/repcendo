"""Fit an orthographic camera to actual evaluated scene geometry over a full loop."""
import bpy, numpy as np
from mathutils import Vector


def fit(scene, margin=0.035):
    camera = scene.camera
    if camera.data.type != "ORTHO":
        raise ValueError("Orthographic camera required")
    previous = scene.frame_current
    lo = np.array([np.inf, np.inf])
    hi = -lo
    view = np.array(camera.matrix_world.inverted())
    for f in sorted(
        set(
            [1, scene.frame_end + 1]
            + [1 + round(scene.frame_end * t / 16) for t in range(16)]
        )
    ):
        scene.frame_set(f)
        graph = bpy.context.evaluated_depsgraph_get()
        for obj in scene.objects:
            if obj.type != "MESH" or obj.hide_render:
                continue
            ev = obj.evaluated_get(graph)
            mesh = ev.to_mesh()
            coords = np.empty(len(mesh.vertices) * 3)
            mesh.vertices.foreach_get("co", coords)
            coords = coords.reshape(-1, 3)
            matrix = view @ np.array(ev.matrix_world)
            xy = (coords @ matrix[:3, :3].T + matrix[:3, 3])[:, :2]
            if len(xy):
                lo = np.minimum(lo, xy.min(axis=0))
                hi = np.maximum(hi, xy.max(axis=0))
            ev.to_mesh_clear()
    center = (lo + hi) / 2
    camera.location += (
        camera.rotation_quaternion @ Vector((center[0], center[1], 0))
        if camera.rotation_mode == "QUATERNION"
        else camera.rotation_euler.to_quaternion() @ Vector((center[0], center[1], 0))
    )
    aspect = scene.render.resolution_x / scene.render.resolution_y
    camera.data.ortho_scale = float(
        max(hi[0] - lo[0], (hi[1] - lo[1]) * aspect) / (1 - 2 * margin)
    )
    scene.frame_set(previous)
    scene[
        "camera_fit"
    ] = "Evaluated scene surface over 17 poses, 3.5 percent edge margin"
    return dict(bounds=[lo.tolist(), hi.tolist()], ortho_scale=camera.data.ortho_scale)
