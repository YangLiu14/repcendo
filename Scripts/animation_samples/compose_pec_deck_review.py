"""Compose full-equipment comparison sheets; this does not approve them."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
for sex in ['male','female']:
 for name in ['pec_fly','reverse_fly']:
  folder=a.root/f'build/pec-deck-review/{sex}/{name}';source=json.loads((folder/'source.json').read_text());sheet=Image.new('RGB',(1000,1650),'#f3f1eb');d=ImageDraw.Draw(sheet);d.text((12,12),f'{sex} / {name} | Structure reference: Life Fitness SS-FLY',font=font,fill='#21332e')
  for row,f in enumerate(source['frames']):
   for col,view in enumerate(source['views']):
    im=Image.open(folder/f'{view}-{f:03d}.png').convert('RGBA');bg=Image.new('RGBA',im.size,'#f3f1eb');bg.alpha_composite(im);sheet.paste(bg.convert('RGB').resize((500,500)),(col*500,70+row*530));d.text((col*500+12,45+row*530),f'{view} / frame {f}',font=font,fill='#21332e')
  output=a.root/f'docs/animation-plan-v3/equipment-review/{sex}/{name}.jpg';output.parent.mkdir(parents=True,exist_ok=True);sheet.save(output,quality=92)
print('Composed 4 equipment sheets; none approved')
