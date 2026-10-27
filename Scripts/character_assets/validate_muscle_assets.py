"""Independent GLB/atlas validation; reads local exports without spending credits."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/character-assets/muscle-overlay-v1'
def validate(sex):
    folder=BASE/sex;manifest=json.loads((folder/'manifest.json').read_text())
    p=folder/f'greek-{sex}-muscles.glb';data=p.read_bytes()
    assert data[:4]==b'glTF' and struct.unpack_from('<II',data,4)==(2,len(data))
    n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n])
    assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==23
    names={m['name'] for m in g['materials']};assert len(names)==18
    tris=0
    for mesh in g['meshes']:
        for prim in mesh['primitives']:
            assert {'POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0'} <= set(prim['attributes'])
            tris+=g['accessors'][prim['indices']]['count']//3
    assert tris==manifest['triangles']
    assert all('bufferView' in image for image in g['images'])
    ids=np.asarray(Image.open(folder/'textures/muscle-id.png'))[:,:,0]
    assert set(range(18))<=set(np.unique(ids))
    masks=[]
    for group in manifest['groups'][1:]:
        path=folder/'textures/masks'/f"{group['id']:02d}-{group['key']}.png"
        pixels=np.asarray(Image.open(path))[:,:,0]
        assert pixels.shape==(2048,2048) and pixels.max()>200 and np.count_nonzero(pixels)>20
        assert np.count_nonzero(pixels[ids!=group['id']])==0
        masks.append({'group':group['key'],'nonzeroPixels':int(np.count_nonzero(pixels))})
    files=[]
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.suffix in ['.png','.glb','.blend','.json']:
            files.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'sex':sex,'status':'passed','triangles':tris,'rigNodes':23,'materials':18,'atlasIDs':list(range(18)),'masks':masks,'files':files}
result={'characters':[validate(s) for s in ['male','female']], 'checks':'GLB structure, skin attributes, triangle totals, embedded maps, ID atlas and 17 nonempty disjoint UV masks per character'}
(BASE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({c['sex']:c['status'] for c in result['characters']}))
