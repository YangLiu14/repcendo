"""Verify six v2 loops, all rendered frames and complete encoded media."""
import json, subprocess, shutil
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/animation-samples-v2"
BUILD = ROOT / "build/animation-samples-v2"
report = {}
sheet = Image.new("RGB", (1600, 2160), "#f3f1eb")
draw = ImageDraw.Draw(sheet)
for row, (sex, name) in enumerate(
    (s, n) for s in ["male", "female"] for n in ["squat", "bench", "row"]
):
    checks = json.loads((BUILD / sex / name / "motion-checks.json").read_text())
    assert checks["frames_checked"] == 121
    assert (
        checks["max_limb_length_error_m"] < 1e-5
        and checks["max_grip_target_error_m"] < 1e-4
        and checks["loop_matrix_error"] < 1e-5
    )
    clipped = []
    for frame in range(1, 121):
        p = BUILD / sex / name / f"frames/frame-{frame:04d}.png"
        im = Image.open(p)
        box = im.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()
        assert box, (sex, name, frame, "empty")
        if box[0] == 0 or box[1] == 0 or box[2] == im.width or box[3] == im.height:
            clipped.append(frame)
    assert not clipped, (sex, name, clipped)
    media = {}
    for ext in ["mp4", "gif"]:
        p = OUT / sex / f"{name}.{ext}"
        data = json.loads(
            subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_streams",
                    "-show_format",
                    "-of",
                    "json",
                    str(p),
                ]
            )
        )
        stream = data["streams"][0]
        assert abs(float(data["format"]["duration"]) - 5) < 0.05
        assert (stream["width"], stream["height"]) == (
            (1280, 960) if ext == "mp4" else (960, 720)
        )
        assert int(stream["nb_frames"]) == (120 if ext == "mp4" else 80)
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(p), "-f", "null", "-"], check=True
        )
        media[ext] = {
            k: stream.get(k)
            for k in [
                "codec_name",
                "width",
                "height",
                "nb_frames",
                "duration",
                "r_frame_rate",
            ]
        }
    for col, frame in enumerate([1, 31, 61, 91]):
        im = Image.open(BUILD / sex / name / f"frames/frame-{frame:04d}.png")
        im.thumbnail((400, 333))
        sheet.paste(im, (col * 400, row * 360 + 25), im)
        draw.text(
            (col * 400 + 10, row * 360 + 5), f"{sex}/{name} / {frame}", fill="#21332e"
        )
    shutil.copyfile(
        BUILD / sex / name / "motion-checks.json",
        OUT / sex / f"{name}-motion-checks.json",
    )
    report[f"{sex}/{name}"] = {
        "media": media,
        "clipped_frames": clipped,
        "motion": {k: v for k, v in checks.items() if k != "pose_records"},
    }
sheet.save(BUILD / "keyframes-review.jpg", quality=92)
(OUT / "validation.json").write_text(
    json.dumps(
        {
            "status": "passed",
            "rendered_frames_checked": 720,
            "complete_media_decodes": 12,
            "samples": report,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)
print(
    "PASS: 720 rendered frames, 6 loops, 12 complete media decodes; no frame-edge clipping."
)
