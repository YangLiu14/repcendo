"""Compose source-bound plan review sheets and pending decisions; never approve."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from plan_reference_gate import ROOT,CATALOG,PHASES,digest,folder,load_reference

def compose(root,sex,name):
    src_dir=root/f'build/plan-reference-review/{sex}/{name}'
    source=json.loads((src_dir/'source.json').read_text())
    scene_sha=digest(folder(root,sex,name)/f'{name}.blend')
    assert source['sceneSHA256']==scene_sha, 'Stale reference renders'
    ref,ref_sha=load_reference(name)
    views,frames=source['views'],source['frames']
    font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
    im=Image.new('RGB',(1200,len(frames)*328+35),'#f3f1e9');d=ImageDraw.Draw(im)
    d.text((10,5),sex+' / '+name,font=font,fill='black')
    for row,f in enumerate(frames):
        for col,view in enumerate(views):
            x,y=col*300,row*328+35;d.text((x+5,y+2),f'{view} / {f}',font=font,fill='black')
            raw=Image.open(src_dir/f'{view}-{f:04d}.png').convert('RGBA')
            bg=Image.new('RGBA',raw.size,'#f3f1e9');bg.alpha_composite(raw)
            im.paste(bg.convert('RGB').resize((300,300)),(x,y+28))
    board=root/f'docs/animation-plan-v3/reference-review/{sex}/{name}.jpg'
    board.parent.mkdir(parents=True,exist_ok=True);im.save(board,quality=92)
    phase_frames=[61,91,1,31] if name=='incline_press' else [1,25,49,73] if name=='dead_bug' else [1,31,61,91]
    review=dict(status='pending',sceneSHA256=scene_sha,referenceSHA256=ref_sha,views=views,frames=frames,notes='',evidence={str(board.relative_to(root)):digest(board)},comparisons=[dict(phase=p,sourceId=o['sourceId'],locator=o['locator'],frame=f,notes='') for p,f in zip(PHASES,phase_frames) for o in ref['observations'] if o['phase']==p])
    (folder(root,sex,name)/f'{name}-reference-review-pending.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--exercise',choices=list(CATALOG));p.add_argument('--sex',choices=['male','female']);a=p.parse_args()
    for n in [a.exercise] if a.exercise else CATALOG:
        for s in [a.sex] if a.sex else ['male','female']:compose(a.root,s,n)
