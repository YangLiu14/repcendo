"""Package plan renders as offline H.264 loops and a grouped review page."""
from collision_gate import require_render_pass, record_media
import argparse, hashlib, concurrent.futures, json, subprocess
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw
from package_samples import txt, paste
from plan_exercises import PLAN_EXERCISES
from exercise_catalog import EXERCISES

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build/animation-plan-v3"
OUT = ROOT / "docs/animation-plan-v3"


@lru_cache(maxsize=80)
def reference(path):
    return Image.open(path).convert("RGBA")


def card(sex, name, f, config=None, build_root=None, series="PLAN SERIES / 03"):
    c = config if config is not None else PLAN_EXERCISES[name]
    folder = (build_root or BUILD) / sex / name
    count = c.get("frames", 120)
    im = Image.new("RGB", (1280, 960), "#F3F1EB")
    d = ImageDraw.Draw(im)
    txt(d, (44, 32), "REPCENDO", 24, latin=True)
    txt(
        d,
        (255, 34),
        "渐强 / " + ("男性" if sex == "male" else "女性") + "雕塑",
        18,
        fill="#66746D",
    )
    d.line((44, 81, 1236, 81), fill="#DADDD4")
    txt(d, (42, 100), c["title"], 44)
    txt(d, (45, 161), c["en"], 18, latin=True, fill="#66746D")
    paste(im, reference(str(folder / f"frames/frame-{f:04d}.png")), (8, 195, 892, 620))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((910, 210, 1236, 862), radius=22, fill="#FCFCF8")
    txt(d, (934, 234), "主要训练肌群", 24)
    txt(d, (934, 275), "红色纤维标示位置", 17, fill="#AA5141")
    for view, x in [("front", 925), ("back", 1080)]:
        paste(im, reference(str(folder / f"{view}.png")), (x, 310, 150, 240))
    d = ImageDraw.Draw(im)
    txt(d, (981, 551), "正面", 16, fill="#66746D")
    txt(d, (1136, 551), "背面", 16, fill="#66746D")
    d.line((934, 587, 1212, 587), fill="#DADDD4")
    for j, (muscle, where) in enumerate(c["muscles"]):
        y = 604 + j * 75
        d.rounded_rectangle((934, y + 7, 940, y + 49), radius=3, fill="#AA5141")
        txt(d, (953, y), muscle, 20)
        txt(d, (953, y + 34), where, 16, fill="#66746D")
    txt(d, (934, 797), "体表区域示意", 17, fill="#66746D")
    txt(d, (934, 824), "不表示激活强度", 15, fill="#66746D")
    t = (f - 1) / count
    phase = (
        min(int(t * 4), 3)
        if name == "dead_bug" or c.get("alternating") or c.get("quarter_phases")
        else (0 if t < 0.06 or t > 0.94 else 1 if t < 0.46 else 2 if t < 0.54 else 3)
    )
    if c.get("phase_ends"):
        phase = next((i for i, end in enumerate(c["phase_ends"]) if t < end), len(c["phases"])-1)
    for j, label in enumerate(c["phases"]):
        x = 44 + j * 210
        color = "#AA5141" if j == phase else "#DADDD4"
        d.rounded_rectangle((x, 830, x + 190, 834), radius=2, fill=color)
        txt(
            d,
            (x, 846),
            f"{j+1:02d}  {label}",
            19,
            fill="#21332E" if j == phase else "#66746D",
        )
    d.line((44, 902, 1236, 902), fill="#DADDD4")
    txt(d, (44, 917), "动作示范 · " + str(count // 24) + " 秒循环", 16, fill="#66746D")
    txt(d, (1030, 918), series, 15, fill="#66746D", latin=True)
    return im


def package(pair):
    sex, name = pair
    require_render_pass(sex, name)
    c = PLAN_EXERCISES[name]
    dest = OUT / sex
    dest.mkdir(parents=True, exist_ok=True)
    count = c.get("frames", 120)
    card(sex, name, 1 + count // 4 if name == "dead_bug" else 61).save(
        dest / f"{name}-poster.png"
    )
    args = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        "1280x960",
        "-r",
        "24",
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-threads",
        "2",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest / f"{name}.mp4"),
    ]
    with subprocess.Popen(args, stdin=subprocess.PIPE) as proc:
        for f in range(1, count + 1):
            proc.stdin.write(card(sex, name, f).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError(name)
    diagnostics = json.loads((BUILD / sex / name / "motion-checks.json").read_text())
    diagnostics["scope"] = "Skeletal bake diagnostics; final surface/contact evidence is in collision-validation.json and hand-grip-validation.json"
    # Grip shape can receive an additional surface corrective after the bone bake.
    diagnostics.pop("contact_corrective", None)
    (dest / f"{name}-motion-checks.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    record_media(sex, name)
    print("PACKAGED", sex, name, flush=True)


def page():
    coverage = json.loads((OUT / "coverage.json").read_text())
    lookup = {
        c["id"]: (n, "../animation-samples-v2" if n in EXERCISES else ".", c)
        for n, c in {**EXERCISES, **PLAN_EXERCISES}.items()
    }
    sections = {}
    for e in coverage["exercises"]:
        name, folder, c = lookup[e["exerciseID"]]
        sections.setdefault(e["day"], []).append(
            dict(
                id=e["exerciseID"],
                title=e["title"],
                name=name,
                folder=folder,
                revision={
                    sex: hashlib.sha256(
                        (OUT / folder / sex / f"{name}.mp4").read_bytes()
                    ).hexdigest()[:12]
                    for sex in ["male", "female"]
                },
                muscles=" / ".join(m[0] for m in c["muscles"]),
            )
        )
    data = json.dumps(sections, ensure_ascii=False)
    html = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>训练计划 · 动作示范 | Repcendo</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f3f1eb;color:#21332e;font:16px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1300px;margin:auto;padding:42px 24px}header{border-bottom:1px solid #daddd4;padding-bottom:28px}small{letter-spacing:.12em;color:#66746d}h1{font-size:clamp(28px,5vw,48px);margin:14px 0}p{color:#66746d;line-height:1.7}.toolbar{position:sticky;top:0;background:#f3f1ebee;backdrop-filter:blur(12px);padding:14px 0;z-index:2;display:flex;gap:12px;align-items:center;flex-wrap:wrap}button,select{font:inherit;border:1px solid #ccd1c8;border-radius:99px;padding:9px 20px;background:#fff;color:inherit;cursor:pointer}button[aria-pressed=true]{background:#21332e;color:white}h2{font-size:24px;margin-top:40px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{background:#fcfcf8;border:1px solid #e1e3da;border-radius:18px;overflow:hidden}video{display:block;width:100%;aspect-ratio:4/3;background:#f3f1eb;cursor:pointer}.meta{padding:16px 20px 20px}.meta h3{margin:0 0 8px}.meta p{margin:0;font-size:14px}footer{padding:32px 0;color:#66746d}dialog{border:0;margin:0;padding:0;width:100vw;height:100dvh;max-width:none;max-height:none;background:#101713;color:white}dialog::backdrop{background:#101713}#videoStage{position:absolute;inset:0;width:100%;height:100%;overflow:hidden}#videoStage video{position:absolute;inset:0;width:100%;height:100%;min-height:0;aspect-ratio:auto;object-fit:contain}#closeVideo{position:absolute;right:20px;top:16px;z-index:3;background:#21332e;color:white} @media(max-width:720px){main{padding:24px 14px}.grid{grid-template-columns:1fr}h2{font-size:21px}}</style>
<main><header><small>REPCENDO / PLAN SERIES</small><h1>四日训练计划 · 动作示范</h1><p>19 个计划动作，男女双版本。沿用希腊雕塑人物，红色纤维标示主要训练肌群位置。</p></header><div class="toolbar"><button data-sex="male" aria-pressed="true">男性</button><button data-sex="female" aria-pressed="false">女性</button><label>训练日 <select id="day"><option value="all">全部</option></select></label><span id="status" role="status"></span></div><div id="content"></div><footer>进入画面自动循环播放，点击视频可全屏。肌群颜色表示位置，不表示激活强度。</footer></main><dialog id="viewer" aria-label="动作示范全屏"><button id="closeVideo" aria-label="退出全屏">关闭 ×</button><div id="videoStage"></div></dialog>
<script>const groups=DATA;let sex='male';let observer;
const viewer=document.querySelector('#viewer');let returnVideo=null;document.querySelector('#closeVideo').onclick=()=>viewer.close();viewer.onclose=()=>{if(returnVideo){returnVideo();returnVideo=null}};function openVideo(v){const marker=document.createElement('div');marker.style.aspectRatio='4/3';v.before(marker);document.querySelector('#videoStage').append(v);v.controls=true;returnVideo=()=>{marker.replaceWith(v);v.controls=false;v.play().catch(()=>{})};viewer.showModal();v.play().catch(()=>{})}const day=document.querySelector('#day');Object.keys(groups).forEach(k=>{let o=new Option(k,k);day.add(o)});
function render(){if(observer)observer.disconnect();document.querySelectorAll('video').forEach(v=>{v.pause();v.removeAttribute('src');v.load()});const root=document.querySelector('#content');root.replaceChildren();let count=0;observer=new IntersectionObserver(entries=>entries.forEach(({target:v,isIntersecting})=>{if(isIntersecting){if(!v.getAttribute('src'))v.src=v.dataset.src;v.play().catch(()=>{v.controls=true})}else v.pause()}),{threshold:.25});for(const [group,items]of Object.entries(groups)){if(day.value!=='all'&&day.value!==group)continue;const section=document.createElement('section');const h=document.createElement('h2');h.textContent=group;section.append(h);const grid=document.createElement('div');grid.className='grid';for(const e of items){count++;const a=document.createElement('article'),v=document.createElement('video');v.muted=true;v.loop=true;v.playsInline=true;v.preload='none';v.poster=`${e.folder}/${sex}/${e.name}-poster.png?v=${e.revision[sex]}`;v.dataset.src=`${e.folder}/${sex}/${e.name}.mp4?v=${e.revision[sex]}`;v.src=v.dataset.src;v.setAttribute('aria-label',e.title+'动作示范');v.tabIndex=0;const fullscreen=()=>openVideo(v);v.onclick=fullscreen;v.onkeydown=ev=>{if(ev.key==='Enter')fullscreen()};const meta=document.createElement('div');meta.className='meta';const title=document.createElement('h3');title.textContent=e.title;const m=document.createElement('p');m.textContent=e.muscles;meta.append(title,m);a.append(v,meta);grid.append(a);observer.observe(v)}section.append(grid);root.append(section)}document.querySelector('#status').textContent=count+' 个动作'}
document.querySelectorAll('[data-sex]').forEach(b=>b.onclick=()=>{sex=b.dataset.sex;document.querySelectorAll('[data-sex]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));render()});day.onchange=render;document.addEventListener('visibilitychange',()=>{document.querySelectorAll('video').forEach(v=>{if(document.hidden)v.pause();else{const r=v.getBoundingClientRect();if(r.bottom>0&&r.top<innerHeight)v.play().catch(()=>{})}})});render();</script></html>""".replace(
        "DATA", data
    )
    (OUT / "index.html").write_text(html)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--page-only", action="store_true")
    p.add_argument("--exercise", choices=list(PLAN_EXERCISES))
    p.add_argument("--sex", choices=["male", "female"])
    a = p.parse_args()
    if not a.page_only:
        pairs = [
            (s, n)
            for s in ([a.sex] if a.sex else ["male", "female"])
            for n in ([a.exercise] if a.exercise else PLAN_EXERCISES)
        ]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            list(pool.map(package, pairs))
    page()
