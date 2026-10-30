"""Package v2 sculpture renders into labelled MP4/GIF review cards."""
from collision_gate import require_render_pass, record_media
import argparse, json, subprocess, hashlib
from pathlib import Path
from PIL import Image, ImageDraw
from package_samples import txt, paste, phase

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build/animation-samples-v2"
OUT = ROOT / "docs/animation-samples-v2"
BG = "#F3F1EB"
INK = "#21332E"
MUTED = "#66746D"
ACCENT = "#AA5141"
RULE = "#DADDD4"
from exercise_catalog import EXERCISES as CONFIG


def card(sex, name, frame):
    c = CONFIG[name]
    folder = BUILD / sex / name
    source = folder / f"frames/frame-{frame:04d}.png"
    if not source.exists():
        source = folder / f"motion-{frame:04d}.png"
    im = Image.new("RGB", (1280, 960), BG)
    d = ImageDraw.Draw(im)
    for j, h in enumerate([12, 20, 28]):
        d.rounded_rectangle(
            (44 + j * 12, 60 - h, 51 + j * 12, 60), radius=3, fill=ACCENT
        )
    txt(d, (96, 34), "REPCENDO", 24, latin=True)
    txt(
        d, (275, 37), "渐强 / " + ("男性" if sex == "male" else "女性") + "雕塑", 18, fill=MUTED
    )
    txt(d, (1124, 37), c["number"] + " / 03", 22, fill=MUTED, latin=True)
    d.line((44, 81, 1236, 81), fill=RULE)
    txt(d, (42, 97), c["title"], 46)
    txt(d, (45, 161), c["en"], 18, fill=MUTED, latin=True)
    d.rounded_rectangle((1050, 112, 1236, 150), radius=19, fill="#E4E8DF")
    txt(d, (1070, 119), "雕塑样片 · 5s", 17)
    paste(im, Image.open(source), (8, 195, 892, 620))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((910, 210, 1236, 862), radius=22, fill="#FCFCF8")
    txt(d, (934, 234), "主要训练肌群", 24)
    d.ellipse((935, 279, 946, 290), fill=ACCENT)
    txt(d, (956, 273), "红色纤维标示位置", 17, fill=MUTED)
    for view, x in [("front", 925), ("back", 1080)]:
        paste(im, Image.open(folder / f"{view}.png"), (x, 310, 150, 240))
    d = ImageDraw.Draw(im)
    txt(d, (981, 551), "正面", 16, fill=MUTED)
    txt(d, (1136, 551), "背面", 16, fill=MUTED)
    d.line((934, 587, 1212, 587), fill=RULE)
    for j, (muscle, where) in enumerate(c["muscles"]):
        y = 604 + j * 75
        d.rounded_rectangle((934, y + 7, 940, y + 49), radius=3, fill=ACCENT)
        txt(d, (953, y), muscle, 22)
        txt(d, (953, y + 34), where, 17, fill=MUTED)
    txt(d, (934, 797), "体表区域示意", 17, fill=MUTED)
    txt(d, (934, 824), "不表示激活强度", 15, fill=MUTED)
    current = phase(frame)
    for j, label in enumerate(c["phases"]):
        x = 44 + j * 210
        d.rounded_rectangle(
            (x, 830, x + 190, 834), radius=2, fill=ACCENT if j == current else RULE
        )
        txt(d, (x, 846), f"{j+1:02d}  {label}", 19, fill=INK if j == current else MUTED)
    d.line((44, 902, 1236, 902), fill=RULE)
    txt(d, (44, 917), "希腊雕塑人物 · 绑定骨架与纤维材质 · 动作制作样片", 16, fill=MUTED)
    txt(d, (1045, 918), "MOTION STUDY / v02", 15, fill=MUTED, latin=True)
    return im


def command(args):
    subprocess.run(args, check=True)


def package(sex, name, preview):
    if not preview:
        require_render_pass(sex, name)
    folder = BUILD / sex / name
    dest = OUT / sex
    dest.mkdir(exist_ok=True, parents=True)
    card(sex, name, 61).save(dest / f"{name}-poster.png")
    if preview:
        return
    frames = folder / "cards"
    frames.mkdir(exist_ok=True)
    for f in range(1, 121):
        card(sex, name, f).save(frames / f"{f:04d}.png")
    command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            "24",
            "-i",
            str(frames / "%04d.png"),
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(dest / f"{name}.mp4"),
        ]
    )
    command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(dest / f"{name}.mp4"),
            "-filter_complex",
            "fps=16,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a",
            "-loop",
            "0",
            str(dest / f"{name}.gif"),
        ]
    )
    if not preview:
        record_media(sex, name)
    print(f"Packaged {sex}/{name}", flush=True)


def hand_overview():
    sources = OUT / "hand-closeups"
    if not sources.exists():
        return
    sheet = Image.new("RGB", (1800, 1320), BG)
    bench = Image.new("RGB", (1200, 660), BG)
    for row, sex in enumerate(["male", "female"]):
        for col, name in enumerate(CONFIG):
            tile = Image.new("RGB", (600, 660), BG)
            d = ImageDraw.Draw(tile)
            txt(
                d,
                (24, 16),
                ("男性" if sex == "male" else "女性") + " · " + CONFIG[name]["title"],
                25,
            )
            paste(
                tile, Image.open(sources / f"{sex}-{name}-061.png"), (0, 60, 600, 600)
            )
            sheet.paste(tile, (col * 600, row * 660))
            if name == "bench":
                bench.paste(tile, (row * 600, 0))
    sheet.save(OUT / "hand-grips-overview.png")
    bench.save(OUT / "hand-grips-bench.png")


def shoulder_overview():
    folder = OUT / "shoulder-review"
    if not (folder / "male-061-back.png").exists():
        return
    compare = Image.new("RGB", (1200, 1320), BG)
    for row, view in enumerate(["front", "back"]):
        for col, (file, label) in enumerate(
            [(f"before-{view}.png", "修正前"), (f"male-061-{view}.png", "修正后")]
        ):
            tile = Image.new("RGB", (600, 660), BG)
            d = ImageDraw.Draw(tile)
            txt(d, (24, 16), label + " · " + ("正面" if view == "front" else "背面"), 25)
            paste(tile, Image.open(folder / file), (0, 60, 600, 600))
            compare.paste(tile, (col * 600, row * 660))
    compare.save(OUT / "squat-shoulder-comparison.png")
    views = Image.new("RGB", (1500, 1120), BG)
    for row, sex in enumerate(["male", "female"]):
        for col, (view, label) in enumerate(
            [("front", "正面"), ("back", "背面"), ("side", "侧面 · 隐藏配重便于检查")]
        ):
            tile = Image.new("RGB", (500, 560), BG)
            d = ImageDraw.Draw(tile)
            txt(d, (16, 18), ("男" if sex == "male" else "女") + " · " + label, 21)
            paste(tile, Image.open(folder / f"{sex}-061-{view}.png"), (0, 60, 500, 500))
            views.paste(tile, (col * 500, row * 560))
    views.save(OUT / "squat-shoulder-views.png")


def overview():
    sheet = Image.new("RGB", (1920, 960), BG)
    for row, sex in enumerate(["male", "female"]):
        for col, name in enumerate(CONFIG):
            sheet.paste(
                Image.open(OUT / sex / f"{name}-poster.png").resize(
                    (640, 480), Image.Resampling.LANCZOS
                ),
                (col * 640, row * 480),
            )
    sheet.save(OUT / "overview.png")


def webpage():
    cards = []
    for name, c in CONFIG.items():
        links = " · ".join(
            f'<a data-file="{name}.{ext}" href="male/{name}.{ext}" download>{label}</a>'
            for ext, label in [("mp4", "MP4"), ("gif", "GIF"), ("blend", "Blender 源文件")]
        )
        cards.append(
            f'<article><div class="title"><div><small>{c["number"]} / MOTION STUDY v02</small><h2>{c["title"]}</h2></div><span>{c["en"]}</span></div><video data-exercise="{name}" controls loop muted playsinline preload="metadata" poster="male/{name}-poster.png?v=shoulders2" src="male/{name}.mp4?v=shoulders2" aria-label="{c["title"]}，红色表示主要训练肌群位置"></video><div class="downloads">{links}</div></article>'
        )
    page = (
        """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>渐强 · 雕塑动作样片 v2</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f3f1eb;color:#21332e;font:16px/1.6 -apple-system,BlinkMacSystemFont,sans-serif}main{max-width:1120px;margin:auto;padding:44px 24px 70px}small{color:#66746d;letter-spacing:.13em;font-size:12px}h1{font:500 clamp(30px,5vw,48px)/1.2 Georgia,"Songti SC",serif;margin:15px 0}p{max-width:780px;color:#58665f}button{font:inherit;background:#fcfcf8;color:#21332e;border:1px solid #daddd4;border-radius:8px;min-height:44px;padding:8px 18px;margin:5px 6px 0 0;cursor:pointer}button[aria-pressed=true],#play{background:#354537;color:white;border-color:#354537}button:focus-visible,a:focus-visible{outline:3px solid #aa5141;outline-offset:4px}article{margin:30px 0 44px;border:1px solid #daddd4;border-radius:15px;overflow:hidden;background:#fcfcf8}.title{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:20px 26px}h2{margin:5px 0 0;font-size:24px}.title span{color:#66746d;font-size:12px;letter-spacing:.06em}video{display:block;width:100%;aspect-ratio:4/3;background:#f3f1eb}.downloads{padding:16px 26px;color:#89968b}a{color:#904d3f;text-underline-offset:4px}.tools{display:flex;flex-wrap:wrap;align-items:center;gap:15px}.tabs{display:inline-flex}.status{font-size:13px;color:#737e71}footer{font-size:14px;color:#66746d}@media(max-width:600px){main{padding:26px 12px}.title{padding:16px}.title span{display:none}.downloads{padding:16px}h2{font-size:22px}.tools{gap:6px}}</style>
<main><header><small>REPCENDO / SCULPTURE MOTION STUDIES</small><h1>雕塑，开始训练。</h1><p>用新人物重做深蹲、卧推和坐姿划船。红色纤维显露主要训练肌群，右侧正背面图补足遮挡。每段 5 秒，可切换男女、暂停和拖动查看。已修正深蹲落杠与肩颈轮廓，保留五指握持。</p><details open><summary style="cursor:pointer;color:#904d3f">深蹲肩颈与落杠：修正前后</summary><p>上背形体、肩部蒙皮和抬臂旋转均已调整，杠铃按真实表面定位。<a href="squat-shoulder-views.png">查看男女正 / 背 / 侧面</a> · <a href="squat-shoulder-validation.json">接触检查</a></p><img src="squat-shoulder-comparison.png?v=shoulders2" alt="男性深蹲肩颈修正前后的正面和背面对照" style="width:100%;max-width:900px;border-radius:12px"></details><details><summary style="cursor:pointer;color:#904d3f">查看手部近景与骨架资产</summary><p><a href="../character-assets/hand-rig-v1/README.md">可编辑手指骨架：Blender / GLB</a> · <a href="hand-grip-validation.json">握持检查结果</a></p><img src="hand-grips-overview.png?v=shoulders2" alt="男女版深蹲、卧推和划船的实际手部握持近景" style="width:100%;border-radius:12px"></details><div class="tools"><div class="tabs" aria-label="人物选择"><button data-sex="male" aria-pressed="true">男性</button><button data-sex="female" aria-pressed="false">女性</button></div><div><button id="play">同时播放</button><button id="pause">全部暂停</button></div></div><p id="status" class="status" aria-live="polite">男性版本 · 红色为体表位置示意，不表示激活强度。</p></header>"""
        + "".join(cards)
        + """<footer>保留旧版以便比较：<a href="../animation-samples/">v1 人偶样片</a> · <a href="../character-assets/muscle-overlay-v1/">独立肌群 3D 预览</a> · <a href="README.md">制作说明与验证范围</a>。</footer></main>
<script>const videos=[...document.querySelectorAll('video')];let sex='male';const status=document.querySelector('#status');document.querySelector('#play').onclick=()=>{videos.forEach(v=>v.play().catch(()=>{}));status.textContent=(sex==='male'?'男性':'女性')+'版本 · 三段循环播放中。'};document.querySelector('#pause').onclick=()=>{videos.forEach(v=>v.pause());status.textContent='已暂停，可拖动查看关键姿势。'};document.querySelectorAll('[data-sex]').forEach(b=>b.onclick=()=>{sex=b.dataset.sex;document.querySelectorAll('[data-sex]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));videos.forEach(v=>{v.pause();const e=v.dataset.exercise;v.poster=sex+'/'+e+'-poster.png?v=shoulders2';v.src=sex+'/'+e+'.mp4?v=shoulders2';v.load()});document.querySelectorAll('[data-file]').forEach(a=>a.href=sex+'/'+a.dataset.file);status.textContent=(sex==='male'?'男性':'女性')+'版本 · 红色为体表位置示意，不表示激活强度。'});document.addEventListener('visibilitychange',()=>{if(document.hidden)videos.forEach(v=>v.pause())});</script></html>"""
    )
    revision = hashlib.sha256(
        b"".join(
            (OUT / sex / f"{name}.mp4").read_bytes()
            for sex in ["male", "female"]
            for name in CONFIG
        )
    ).hexdigest()[:12]
    (OUT / "index.html").write_text(page.replace("v=shoulders2", "v=" + revision))
    manifest = {
        "shoulder_revision": 1,
        "hand_rig_revision": 1,
        "finger_bones_per_character": 30,
        "app_integration": True,
        "deformation_rig": {
            "bench": "athlete-deformation-2",
            "row": "athlete-deformation-2",
            "squat": "legacy-53-bones",
        },
        "new_tripo_credits": 0,
        "version": 2,
        "fps": 24,
        "frames": 120,
        "duration_seconds": 5,
        "size": [1280, 960],
        "characters": ["male", "female"],
        "source_characters": "../character-assets/muscle-overlay-v1/",
        "samples": CONFIG,
        "review_status": "Visual motion prototypes; no professional movement review yet.",
    }
    manifest["files"] = {
        str(f.relative_to(OUT)): {
            "bytes": f.stat().st_size,
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        }
        for f in sorted(OUT.rglob("*"))
        if f.is_file()
        and f.suffix in [".mp4", ".gif", ".blend", ".png"]
        and "preview" not in f.stem
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--preview", action="store_true")
    p.add_argument("--exercise", choices=list(CONFIG))
    a = p.parse_args()
    OUT.mkdir(exist_ok=True, parents=True)
    for sex in ["male", "female"]:
        for name in [a.exercise] if a.exercise else CONFIG:
            package(sex, name, a.preview)
    overview()
    hand_overview()
    shoulder_overview()
    webpage()
