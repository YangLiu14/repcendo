"""Render all samples with two local Blender workers. Does not touch App files."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--previews-only',action='store_true')
args=parser.parse_args()


def render(exercise):
    for view in ['motion','front','back']:
        command=['blender','-b','-t','4','--python-exit-code','1','--python',
                 str(ROOT/'Scripts/animation_samples/build_scene.py'),'--','--exercise',exercise,'--view',view]
        if args.previews_only:command.append('--preview')
        log=ROOT/f'build/animation-{exercise}-{view}.log'
        with log.open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
        print(f'{exercise}/{view} done',flush=True)


with ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(render,['squat','bench','row']))
