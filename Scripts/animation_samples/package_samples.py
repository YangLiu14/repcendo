"""Compose the original renders into review cards, MP4s and GIFs (Pillow/ffmpeg)."""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'build/animation-samples'
OUT=ROOT/'docs/animation-samples'
FONT='/System/Library/Fonts/Hiragino Sans GB.ttc'
LATIN='/System/Library/Fonts/Supplemental/Arial.ttf'
BG='#F3F1EB'; INK='#21332E'; MUTED='#66746D'; ACCENT='#D85420'; RULE='#DADDD4'
CONFIG={
 'squat':dict(number='01',title='杠铃深蹲',en='BARBELL BACK SQUAT',id='0043',
              muscles=[('股四头肌','大腿前侧'),('臀大肌','臀部后侧')],
              note=['膝、髋共同屈伸','脚部保持固定'],phases=['准备','下蹲','底部','站起']),
 'bench':dict(number='02',title='杠铃卧推',en='BARBELL BENCH PRESS',id='0025',
              muscles=[('胸大肌','胸部前侧')],note=['肱三头肌、三角肌前束协同','本片仅突出胸大肌'],
              phases=['准备','下放','底部','推起']),
 'row':dict(number='03',title='坐姿绳索划船',en='SEATED CABLE ROW · CLOSE GRIP',id='0861',
            muscles=[('背阔肌','背部两侧'),('菱形肌 / 中斜方肌','肩胛骨之间 · 区域示意')],
            note=['采用窄握动作示意','手肘向后，绳索连接握把'],phases=['准备','拉回','收缩位','回放']),
}


def font(size,latin=False):
    return ImageFont.truetype(LATIN if latin else FONT,size)


def txt(draw,xy,value,size=20,fill=INK,latin=False):
    draw.text(xy,value,font=font(size,latin),fill=fill)


def paste(image,source,box):
    source=source.convert('RGBA')
    source.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS)
    x=box[0]+(box[2]-source.width)//2
    y=box[1]+(box[3]-source.height)//2
    image.paste(source,(x,y),source)


def phase(frame):
    t=(frame-1)/120
    return 0 if t<.06 or t>.94 else 1 if t<.46 else 2 if t<.54 else 3


def card(name,source,frame):
    c=CONFIG[name]
    im=Image.new('RGB',(1280,960),BG);d=ImageDraw.Draw(im)
    for j,h in enumerate([12,20,28]):
        d.rounded_rectangle((44+j*12,60-h,51+j*12,60),radius=3,fill=ACCENT)
    txt(d,(96,34),'REPCENDO',24,latin=True)
    txt(d,(275,37),'渐强 / 动作研究',18,fill=MUTED)
    txt(d,(1124,37),c['number']+' / 03',22,fill=MUTED,latin=True)
    d.line((44,81,1236,81),fill=RULE,width=1)
    txt(d,(42,97),c['title'],46)
    txt(d,(45,161),c['en'],18,fill=MUTED,latin=True)
    d.rounded_rectangle((1050,112,1236,150),radius=19,fill='#E4E8DF')
    txt(d,(1070,119),'原创样片 · 5s',17)
    paste(im,source,(10,195,884,610))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((910,210,1236,862),radius=22,fill='#FCFCF8')
    txt(d,(934,234),'主要训练肌群',24)
    d.ellipse((935,279,946,290),fill=ACCENT)
    txt(d,(956,273),'橙色标示位置',17,fill=MUTED)
    for view,x in [('front',925),('back',1080)]:
        path=BUILD/name/f'{view}.png'
        if path.exists(): paste(im,Image.open(path),(x,310,150,240))
    d=ImageDraw.Draw(im)
    txt(d,(981,551),'正面',16,fill=MUTED)
    txt(d,(1136,551),'背面',16,fill=MUTED)
    d.line((934,587,1212,587),fill=RULE,width=1)
    for j,(muscle,where) in enumerate(c['muscles']):
        y=604+j*75
        d.rounded_rectangle((934,y+7,940,y+49),radius=3,fill=ACCENT)
        txt(d,(953,y),muscle,22)
        txt(d,(953,y+34),where,17,fill=MUTED)
    txt(d,(934,797),'位置示意，非激活强度',17,fill=MUTED)
    txt(d,(934,824),'非解剖分层图',15,fill=MUTED)
    # Progress follows the actual 120-frame motion, including end holds.
    current=phase(frame)
    for j,label in enumerate(c['phases']):
        x=44+j*210
        d.rounded_rectangle((x,830,x+190,834),radius=2,fill=ACCENT if j==current else RULE)
        txt(d,(x,846),f'{j+1:02d}  {label}',19,fill=INK if j==current else MUTED)
    d.line((44,902,1236,902),fill=RULE,width=1)
    txt(d,(44,917),'原创模型与动作 · 视觉样片，尚未经过教练审核',16,fill=MUTED)
    txt(d,(1045,918),'MOTION STUDY / v01',15,fill=MUTED,latin=True)
    return im


def command(args):
    subprocess.run(args,check=True)


def package(name,preview=False):
    c=CONFIG[name];folder=BUILD/name
    still=folder/'frames/frame-0061.png'
    if not still.exists():still=folder/'motion.png'
    poster=card(name,Image.open(still),61)
    poster.save(OUT/f'{name}-poster.png')
    if preview:return
    dest=folder/'cards';dest.mkdir(exist_ok=True)
    for frame in range(1,121):
        p=folder/f'frames/frame-{frame:04d}.png'
        if not p.exists():raise FileNotFoundError(p)
        card(name,Image.open(p),frame).save(dest/f'{frame:04d}.png')
    command(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','24','-i',str(dest/'%04d.png'),
             '-c:v','libx264','-preset','slow','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/f'{name}.mp4')])
    command(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(OUT/f'{name}.mp4'),
             '-filter_complex','fps=16,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a',
             '-loop','0',str(OUT/f'{name}.gif')])
    print(f'Packaged {name}',flush=True)


def overview():
    sheet=Image.new('RGB',(1920,480),BG)
    for j,name in enumerate(CONFIG):
        p=Image.open(OUT/f'{name}-poster.png').resize((640,480),Image.Resampling.LANCZOS)
        sheet.paste(p,(j*640,0))
    sheet.save(OUT/'overview.png')


def webpage():
    cards=[]
    for name,c in CONFIG.items():
        links=' · '.join(f'<a href="{name}.{ext}" download>{label}</a>' for ext,label in [('gif','GIF'),('mp4','MP4'),('blend','Blender 源文件')])
        cards.append(f'''<article><div class="title"><div><small>{c['number']} / MOTION STUDY</small><h2>{c['title']}</h2></div><span>{c['en']}</span></div>
          <video controls loop muted playsinline preload="metadata" poster="{name}-poster.png" aria-label="{c['title']}，橙色表示主要训练肌群位置"><source src="{name}.mp4" type="video/mp4"></video>
          <div class="downloads">{links}</div></article>''')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>渐强 · 原创动作样片</title><style>
    :root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f3f1eb;color:#21332e;font:16px -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;line-height:1.6}main{max-width:1120px;margin:auto;padding:48px 24px 72px}small{color:#66746d;letter-spacing:.13em;font-size:12px}h1{font-size:clamp(32px,5vw,52px);margin:12px 0;font-weight:650;letter-spacing:-.04em}p{max-width:760px;color:#58665f}header{margin-bottom:36px}button{font:inherit;background:#21332e;color:#fff;border:0;border-radius:10px;min-height:46px;padding:10px 20px;margin:10px 10px 0 0;cursor:pointer}button:focus-visible,a:focus-visible{outline:3px solid #d85420;outline-offset:4px}article{margin:28px 0 48px;border:1px solid #daddd4;border-radius:18px;overflow:hidden;background:#fcfcf8}.title{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:22px 28px}h2{margin:4px 0 0;font-size:24px}.title span{color:#66746d;font-size:12px;letter-spacing:.06em}video{display:block;width:100%;height:auto;aspect-ratio:4/3;background:#f3f1eb}.downloads{padding:18px 28px;color:#89968b}a{color:#944021;text-underline-offset:4px}footer{color:#66746d;font-size:14px}@media(max-width:600px){main{padding:28px 12px}.title{padding:16px}.title span{display:none}.downloads{padding:16px}h2{font-size:22px}}
    </style><main><header><small>REPCENDO / ORIGINAL MOTION STUDIES</small><h1>三种动作，同一种表达。</h1><p>原创三维人物与器械，橙色标明主要训练肌群的位置。每段 5 秒，可暂停、拖动查看关键姿势；右侧正背面图用于补足遮挡。肌群区域是简化示意，不表示激活强度或解剖分层。</p><button id="play">同时播放</button><button id="pause">全部暂停</button><p id="status" aria-live="polite">视觉样片，尚未经过教练审核。未使用上游图片、GIF 或动画数据。</p></header>'''+''.join(cards)+'''<footer>可编辑源文件保留全部几何与动画。<a href="README.md">制作说明和肌群参考来源</a>。</footer></main><script>
    const videos=[...document.querySelectorAll('video')];
    document.querySelector('#play').onclick=()=>{videos.forEach(v=>v.play().catch(()=>{}));document.querySelector('#status').textContent='正在循环播放三段样片。'};
    document.querySelector('#pause').onclick=()=>{videos.forEach(v=>v.pause());document.querySelector('#status').textContent='已暂停，可逐帧附近拖动查看姿势。'};
    document.addEventListener('visibilitychange',()=>{if(document.hidden)videos.forEach(v=>v.pause())});
    </script></html>'''
    (OUT/'index.html').write_text(page)
    manifest={'fps':24,'frames':120,'duration_seconds':5,'size':[1280,960],
              'provenance':'Original procedural meshes and motion; no upstream media.',
              'review_status':'Visual prototypes; not professionally reviewed.',
              'samples':{name:{**c,'files':{ext:f'{name}.{ext}' for ext in ['gif','mp4','blend']}} for name,c in CONFIG.items()}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    for name in CONFIG:package(name,a.preview)
    overview();webpage()
