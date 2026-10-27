"""Validate and package local Tripo outputs. No network calls or credit spending.

Run from any directory with Python 3 after inspect_character.py has succeeded.
"""
import hashlib
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/character-assets/greek-athletes-v1"


def read(path):
    return json.loads(path.read_text())


def record(path):
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def package(sex):
    folder = BASE / sex
    source, rig = [read(folder / stage / "task.json") for stage in ["source", "rig"]]
    check = read(folder / "rig-check-task.json")
    assert all(task["status"] == "success" for task in [source, check, rig])
    assert check["output"]["riggable"] and check["output"]["rig_type"] == "biped"
    report = read(folder / "inspection/inspection.json")
    assert 0 < report["triangles"] <= 50000
    assert len(report["armatures"]) == 1
    assert report["poseCheck"]["finiteDeformedVertices"]
    assert len(report["poseCheck"]["poses"]) == 2
    for pose in report["poseCheck"]["poses"].values():
        assert pose["movedVertexCount"] > 100 and pose["finiteDeformedVertices"]
    for mesh in report["meshes"]:
        assert mesh["unweightedVertices"] == 0
        assert all(abs(w - 1) < 1e-4 for w in mesh["boneWeightRange"])
    # Female delivery includes the requested local chest refinement; preserve
    # original provider downloads as provenance, never package them by mistake.
    rig_path = "refined/rig.glb" if sex == "female" else "rig/model.glb"
    source_path = "refined/source.glb" if sex == "female" else "source/model.glb"
    payload = (folder / rig_path).read_bytes()
    assert payload[:4] == b"glTF"
    assert struct.unpack_from("<II", payload, 4) == (2, len(payload))
    n = struct.unpack_from("<I", payload, 12)[0]
    gltf = json.loads(payload[20:20+n])
    assert len(gltf["skins"]) == 1 and len(gltf["skins"][0]["joints"]) == 23
    assert all("bufferView" in image for image in gltf["images"])
    assert all("JOINTS_0" in p["attributes"] and "WEIGHTS_0" in p["attributes"]
               for mesh in gltf["meshes"] for p in mesh["primitives"])
    names = {node.get("name") for node in gltf["nodes"]}
    assert {f"mixamorig:{s}{p}" for s in ["Left", "Right"]
            for p in ["Arm","ForeArm","Hand","UpLeg","Leg","Foot"]} <= names
    files = []
    for origin_path, filename in [
        (source_path, f"greek-{sex}-source.glb"),
        (rig_path, f"greek-{sex}-rigged.glb"),
        ("inspection/character.blend", f"greek-{sex}.blend"),
        ("inspection/view-pos-x.png", "preview-front.png"),
        ("inspection/rig-skeleton-projection.png", "preview-skeleton.png"),
    ]:
        target = folder / filename
        shutil.copyfile(folder / origin_path, target)
        files.append(record(target))
    files.append(record(folder / "rig-check.mp4"))
    tasks = [{"stage": stage, "id": task["task_id"], "status": task["status"],
              "credits": task["credits_consumed"]}
             for stage,task in [("generation",source),("rig-check",check),("rig",rig)]]
    return {"files": files, "tasks": tasks, "triangles": report["triangles"],
            "localRefinement": read(folder / "refined/refinement.json") if sex == "female" else None,
            "vertices": report["vertices"], "rigNodes": 23, "skins": 1,
            "embeddedTextureImages": len(gltf["images"]),
            "textureDetails": report["materials"],
            "unweightedVertices": 0, "poseChecks": report["poseCheck"],
            "blenderBounds": report["bounds"],
            "creditsConsumed": sum(t["credits"] for t in tasks)}


def main():
    manifest = read(BASE / "manifest.json")
    for source in manifest["selected_concepts"]:
        assert record(ROOT / source["path"])["sha256"] == source["sha256"]
    manifest["characters"] = {sex: package(sex) for sex in ["male", "female"]}
    manifest["creditsConsumed"] = sum(c["creditsConsumed"] for c in manifest["characters"].values())
    manifest["status"] = "complete"
    manifest["validation"] = "Blender 5.2.1 import, weights, finite deformation, four-view and flexion visual review"
    manifest["limitations"] = [
        "23-node body rig; individual finger bones and facial expressions are not included.",
        "Automatic triangulated topology and skin weights may need correction at extreme poses.",
        "Single-front reconstruction approximates back details; female rear bun is simplified.",
        "Diagnostic motion is not an exercise. No IK controls, equipment contact, muscle masks or finished exercise clips yet.",
        "Master assets retain 4K textures and provider-normalized scale; iOS runtime optimization is untested."
    ]
    (BASE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": manifest["status"], "credits": manifest["creditsConsumed"],
                      "characters": {s:{k:c[k] for k in ["triangles","vertices","rigNodes"]}
                                     for s,c in manifest["characters"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
