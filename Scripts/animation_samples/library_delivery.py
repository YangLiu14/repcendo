"""Compose pending review sheets and package only accepted library motions."""
import html
import json
import shutil
import subprocess
from pathlib import Path
from library_exercises import LIBRARY_EXERCISES
from library_gate import ROOT, paths, digest, validator_hashes, specification_digest, require_scene_pass, require_media_pass


def compose(sex, name, root=ROOT):
    from PIL import Image, ImageDraw, ImageFont
    folder, build = paths(root, sex, name)
    source = json.loads((build / "review/source.json").read_text())
    if source["sceneSHA256"] != digest(folder / f"{name}.blend"):
        raise RuntimeError("Stale review renders")
    sheet = Image.new("RGB", (1600, len(source["frames"]) * 348 + 32), "#f3f1eb")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    draw.text((10, 8), f"{sex} / {name} - equipment visible", font=font, fill="#21332e")
    for row, f in enumerate(source["frames"]):
        for col, view in enumerate(source["views"]):
            im = Image.open(build / f"review/{view}-{f:04d}.png").convert("RGBA")
            bg = Image.new("RGBA", im.size, "#f3f1eb")
            bg.alpha_composite(im)
            x, y = col * 320, row * 348 + 32
            draw.text((x+8, y+3), f"{view} / {f}", font=font, fill="#21332e")
            sheet.paste(bg.convert("RGB").resize((320,320)), (x,y+28))
    target = folder / f"{name}-review.jpg"
    sheet.save(target, quality=94)
    # Never overwrite an actual review decision with an automatic acceptance.
    (folder / f"{name}-review-pending.json").write_text(json.dumps({**source, "status":"pending", "notes":"", "evidence":{str(target.relative_to(root)):digest(target)}}, indent=2)+"\n")


def package(sex, name, root=ROOT):
    from PIL import Image
    from package_plan import card
    require_scene_pass(sex, name, root)
    folder, build = paths(root, sex, name)
    if json.loads((build / "render-source.json").read_text())["sha256"] != digest(folder / f"{name}.blend"):
        raise RuntimeError("Stale render frames")
    config = LIBRARY_EXERCISES[name]
    count = config.get("frames",120)
    clipped = []
    for f in range(1,count+1):
        with Image.open(build / f"frames/frame-{f:04d}.png") as raw:
            alpha = raw.getchannel("A")
            box = alpha.getbbox()
            if box is None or box[0] < 2 or box[1] < 2 or box[2] > raw.width-2 or box[3] > raw.height-2:
                clipped.append(f)
    if clipped:
        raise RuntimeError(f"{sex}/{name}: clipped/empty frames {clipped[:10]}")
    def frame(f):
        return card(sex,name,f,config,root/"build/animation-library","LIBRARY / "+config["batch"])
    poster = folder / f"{name}-poster.png"
    frame(1+count//4 if config.get("alternating") or config.get("quarter_phases") else 1+count//2).save(poster)
    video = folder / f"{name}.mp4"
    with subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s","1280x960","-r","24","-i","-","-an","-c:v","libx264","-threads","2","-preset","fast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(video)],stdin=subprocess.PIPE) as proc:
        try:
            for f in range(1,count+1):
                proc.stdin.write(frame(f).tobytes())
        finally:
            proc.stdin.close()
        if proc.wait():
            raise RuntimeError("Encoding failed")
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(video),"-f","null","-"],check=True)
    probe = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-of","json",str(video)]))["streams"][0]
    if not (probe["codec_name"] == "h264" and probe["width"] == 1280 and probe["height"] == 960 and probe["pix_fmt"] == "yuv420p" and int(probe["nb_frames"]) == count and probe["r_frame_rate"] == "24/1"):
        raise RuntimeError("Unexpected video properties")
    receipt = dict(sceneSHA256=digest(folder/f"{name}.blend"),validatorSHA256=validator_hashes(name),specificationSHA256=specification_digest(name),files={p.name:digest(p) for p in [video,poster]},mediaValidation=dict(decoded=True,frames=count,clippedFrames=[],codec="h264",width=1280,height=960,fps=24))
    (folder/f"{name}-media.json").write_text(json.dumps(receipt,indent=2)+"\n")
    shutil.copyfile(build/"motion-checks.json",folder/f"{name}-motion-checks.json")


def collect_entries(names, root=ROOT):
    """Validate every selected variant before returning any planned file writes."""
    target = root / "Repcendo/Resources/ExerciseAnimations"
    catalog = {}
    known = {e["id"] for e in json.loads((root/"Repcendo/Resources/exercises.json").read_text())}
    copies = []
    for name in names:
        c = LIBRARY_EXERCISES[name]
        if c["id"] not in known:
            raise ValueError("Unknown dataset ID: "+c["id"])
        variants = {}
        for sex in ("male","female"):
            require_media_pass(sex,name,root)
            folder,_ = paths(root,sex,name)
            fields = {}
            for field,suffix in [("video",".mp4"),("poster","-poster.png")]:
                source = folder/f"{name}{suffix}"
                output = f"{c['id']}-{sex}{suffix}"
                fields[field],fields[field+"SHA256"] = output,digest(source)
                copies.append((source,target/output))
            variants[sex] = fields
        catalog[c["id"]] = dict(title=c["title"],variants=variants)
    return catalog, copies


def sync(names, root=ROOT):
    """Add only this fully checked batch, preserving every unrelated catalog entry."""
    entries, copies = collect_entries(names, root)
    catalog_path = root / "Repcendo/Resources/ExerciseAnimations/catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog.update(entries)
    for source,dest in copies:
        shutil.copyfile(source,dest)
        if digest(dest) != digest(source):
            raise RuntimeError("Copied asset mismatch")
    temp = catalog_path.with_suffix(".tmp")
    temp.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n")
    temp.replace(catalog_path)


def page(root=ROOT):
    cards, batches = [], {}
    for name,c in LIBRARY_EXERCISES.items():
        if not all((root/f"docs/animation-library/{sex}/{name}-media.json").is_file() for sex in ("male","female")):
            continue
        revisions = {}
        for sex in ("male","female"):
            require_media_pass(sex,name,root)
            revisions[sex] = digest(root/f"docs/animation-library/{sex}/{name}.mp4")[:12]
        batch = c["batch"]
        batches[batch] = batches.get(batch,0) + 1
        cards.append(f'<article data-batch="{batch}"><h2>{html.escape(c["title"])}</h2><p>ID {c["id"]} · 第 {batch} 批 · {c.get("frames",120)/24:g} 秒</p><video controls muted loop playsinline preload="none" aria-label="{html.escape(c["title"])}动作示范" data-name="{name}" data-male="{revisions["male"]}" data-female="{revisions["female"]}"></video></article>')
    options = "".join(f'<option value="{b}">第 {b} 批 · {batches[b]} 个动作</option>' for b in sorted(batches,reverse=True))
    content = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Repcendo · 全库动作制作</title><style>body{margin:32px auto;padding:0 24px;max-width:1200px;background:#f3f1eb;color:#21332e;font-family:system-ui}header{margin:40px 0}button,select{font:inherit;padding:10px 20px;margin:8px 8px 8px 0;cursor:pointer;border:1px solid #aeb8b1;border-radius:8px;background:#fffdf7;color:#21332e}button[aria-pressed="true"]{background:#21332e;color:#fffdf7}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,360px),1fr));gap:24px}article{background:#fffdf7;padding:20px;border-radius:16px}article[hidden]{display:none}h2{font-size:22px}video{width:100%;border-radius:10px}p{color:#66746d}</style><header><h1>全库动作制作</h1><p>男女双版本 · 全库 1,324 项持续分批制作与验收</p><label for="batch">查看批次 </label><select id="batch" onchange="render()">'''+options+'''<option value="all">所有已交付批次</option></select><button data-sex="male" aria-pressed="true" onclick="choose('male')">男性</button><button data-sex="female" aria-pressed="false" onclick="choose('female')">女性</button><p id="status" aria-live="polite"></p></header><main>'''+"".join(cards)+'''</main><script>
let sex='male';
function choose(value){sex=value;document.querySelectorAll('[data-sex]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.sex===sex));render()}
function render(){const batch=document.querySelector('#batch').value;let count=0;document.querySelectorAll('article').forEach(a=>{const v=a.querySelector('video');v.pause();v.removeAttribute('src');a.hidden=batch!=='all'&&a.dataset.batch!==batch;if(!a.hidden){count++;const rev=v.dataset[sex];v.poster=`${sex}/${v.dataset.name}-poster.png?v=${rev}`;v.src=`${sex}/${v.dataset.name}.mp4?v=${rev}`;v.preload='metadata'}v.load()});document.querySelector('#status').textContent=`当前显示 ${count} 个动作 · ${sex==='male'?'男性':'女性'}版本`}
render();
</script></html>'''
    (root/"docs/animation-library/index.html").write_text(content)
