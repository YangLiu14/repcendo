"""Compose inspection sheets and pending review records; never auto-approve."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from collision_gate import ROOT, CATALOG

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--root", type=Path, default=ROOT)
p.add_argument("--sex", choices=["male", "female"])
p.add_argument("--exercise", choices=list(CATALOG))
a = p.parse_args()
records = {}
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
for sex in [a.sex] if a.sex else ["male", "female"]:
    for name in [a.exercise] if a.exercise else CATALOG:
        folder = a.root / f"build/deformation-review/{sex}/{name}"
        source = json.loads((folder / "source.json").read_text())
        frames = source["frames"]
        views = source["views"]
        image = Image.new("RGB", (1200, len(frames) * 428 + 42), "#f3f1e9")
        draw = ImageDraw.Draw(image)
        draw.text(
            (14, 10),
            f"{sex} / {name}   -   isolated body deformation review",
            font=font,
            fill="#213c35",
        )
        for row, frame in enumerate(frames):
            for col, view in enumerate(views):
                path = folder / f"{view}-{frame:04d}.png"
                im = Image.open(path).convert("RGBA")
                background = Image.new("RGBA", im.size, "#f3f1e9")
                background.alpha_composite(im)
                x = col * 400
                y = 42 + row * 428
                draw.text(
                    (x + 10, y + 3),
                    f"{view} / frame {frame}",
                    font=font,
                    fill="#213c35",
                )
                image.paste(background.convert("RGB").resize((400, 400)), (x, y + 28))
        output = a.root / f"docs/animation-plan-v3/deformation-review/{sex}/{name}.jpg"
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output, quality=91)
        records[sex + "/" + name] = dict(
            status="pending",
            scene_sha256=source["scene_sha256"],
            views=views,
            frames=frames,
            notes="",
            evidence={
                str(output.relative_to(a.root)): hashlib.sha256(
                    output.read_bytes()
                ).hexdigest()
            },
        )
        if name in ("cable_crunch", "dead_bug"):
            prefix = "grip" if name == "cable_crunch" else "shoulder"
            suffix = "grips" if name == "cable_crunch" else "shoulders"
            sheet = Image.new("RGB", (1000, ((len(frames) + 1) // 2) * 530), "#f3f1e9")
            labels = ImageDraw.Draw(sheet)
            for i, frame in enumerate(frames):
                raw = Image.open(folder / f"{prefix}-{frame:04d}.png").convert("RGBA")
                bg = Image.new("RGBA", raw.size, "#f3f1e9")
                bg.alpha_composite(raw)
                x, y = (i % 2) * 500, (i // 2) * 530
                labels.text(
                    (x + 10, y + 4),
                    f"{sex} / {prefix} / frame {frame}",
                    font=font,
                    fill="#213c35",
                )
                sheet.paste(bg.convert("RGB"), (x, y + 30))
            closeup = output.with_name(name + "-" + suffix + ".jpg")
            sheet.save(closeup, quality=94)
            records[sex + "/" + name]["evidence"][
                str(closeup.relative_to(a.root))
            ] = hashlib.sha256(closeup.read_bytes()).hexdigest()
output = a.root / "docs/animation-plan-v3/deformation-review-pending.json"
previous = (
    json.loads(output.read_text()) if (a.sex or a.exercise) and output.exists() else {}
)
previous.update(records)
output.write_text(json.dumps(previous, indent=2) + "\n")
print("Created", len(records), "pending reviews; none approved")
