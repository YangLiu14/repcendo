"""Check rendered output, framing, loop seam and encoded delivery formats."""
import json
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/animation-samples'; BUILD=ROOT/'build/animation-samples'
sheet=Image.new('RGB',(1600,1080),'#f3f1eb');draw=ImageDraw.Draw(sheet)
report={}
for row,name in enumerate(['squat','bench','row']):
    probes={}
    for ext in ['mp4','gif']:
        data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(OUT/f'{name}.{ext}')]))
        stream=data['streams'][0]
        probes[ext]={k:stream.get(k) for k in ['codec_name','width','height','nb_frames','duration','r_frame_rate']}
        assert abs(float(data['format']['duration'])-5)<.05
        assert (stream['width'],stream['height'])==((1280,960) if ext=='mp4' else (960,720))
        assert int(stream['nb_frames'])==(120 if ext=='mp4' else 80)
        # Decode the complete delivery, not just its metadata.
        subprocess.run(['ffmpeg','-v','error','-i',str(OUT/f'{name}.{ext}'),'-f','null','-'],check=True)
    clipped=[]
    for frame in range(1,121):
        im=Image.open(BUILD/name/f'frames/frame-{frame:04d}.png')
        box=im.getchannel('A').point(lambda p:255 if p>16 else 0).getbbox()
        if box[0]==0 or box[1]==0 or box[2]==im.width or box[3]==im.height:
            clipped.append(frame)
    assert not clipped,(name,clipped)
    for column,frame in enumerate([1,31,61,91]):
        im=Image.open(BUILD/name/f'frames/frame-{frame:04d}.png').convert('RGBA')
        im.thumbnail((400,333))
        sheet.paste(im,(column*400,row*360+25),im)
        draw.text((column*400+12,row*360+5),f'{name} / frame {frame}',fill='#21332e')
    checks=json.loads((BUILD/name/'motion-checks.json').read_text())
    assert not checks['limb_length_errors'] and checks['loop_position_error_m']<1e-6
    report[name]={'media':probes,'clipped_frames':clipped,'motion':checks}
sheet.save(BUILD/'keyframes-review.jpg',quality=92)
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 360 frames, 3 loop checks, 6 complete media decodes; no frame-edge clipping.')
