"""Inverse contact-corrective support for Blender's rigid DQ and linear skinning.

This does not deform/render the character: Blender's Armature modifier does that.
The matrix is used only to map a contact displacement back to the rest mesh.
"""
from mathutils import Matrix, Quaternion, Vector


def blend_rigid(matrices, weights):
    reference = matrices[max(weights, key=lambda pair: pair[1])[0]].to_quaternion()
    real = Vector((0.0, 0.0, 0.0, 0.0))
    dual = Vector((0.0, 0.0, 0.0, 0.0))
    for name, weight in weights:
        matrix = matrices[name]
        q = matrix.to_quaternion()
        translation = matrix.translation
        d = Quaternion((0.0, *translation)) @ q
        sign = 1 if q.dot(reference) >= 0 else -1
        real += Vector(q) * weight * sign
        dual += Vector(d) * weight * sign * 0.5
    length = real.length
    if length < 1e-8:
        raise ValueError("Degenerate dual-quaternion blend")
    q = Quaternion(real / length)
    d = Quaternion(dual / length)
    translation = d @ q.conjugated()
    result = q.to_matrix().to_4x4()
    result.translation = Vector((translation.x, translation.y, translation.z)) * 2
    return result
