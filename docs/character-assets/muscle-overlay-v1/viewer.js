import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const canvas=document.querySelector('#scene'),stage=canvas.parentElement;
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(34,1,.01,20);
const controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.target.set(0,.5,0);controls.minDistance=.65;controls.maxDistance=3;controls.maxPolarAngle=Math.PI*.92;
scene.add(new THREE.HemisphereLight(0xfffaf0,0x888d83,2.3));
for(const [position,color,power] of [[[2,3,2],0xfff6e8,2.4],[[-2,1,-2],0xe8f0ff,1.5],[[1,2,-3],0xffffff,1.8]]){const l=new THREE.DirectionalLight(color,power);l.position.set(...position);scene.add(l);}
const loader=new GLTFLoader(),textureLoader=new THREE.TextureLoader();
let current=null,activeSex='male',groups=[],selected=new Set([1]),motion=false,token=0,activePreset='chest';
const cache=new Map();
const presets=[['marble','白色雕塑',[]],['all','全部肌群',null],['chest','胸',[1]],['back','背',[11,12]],['legs','腿臀',[13,14,15,16]],['press','卧推示意',[1,2,6]],['row','划船示意',[4,5,11,12]],['squat','深蹲示意',[13,14]]];
function view(name){const position={front:[1.85,.57,0],back:[-1.85,.57,0],side:[0,.57,-1.85]}[name];camera.position.set(...position);controls.target.set(0,.49,0);controls.update();}
view('front');
function applySelection(presetKey=null){
 activePreset=presetKey;
 if(!current)return;
 for(const item of current.parts)item.mesh.material=selected.has(item.id)?item.muscle:item.marble;
 document.querySelectorAll('#groups input').forEach(el=>el.checked=selected.has(Number(el.value)));
 document.querySelectorAll('#presets button').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.key===presetKey)));
 document.querySelector('#selection-state').textContent=selected.size?`${selected.size} 个肌群已显示`:'白色雕塑';
}
function initControls(){
 document.querySelector('#groups').replaceChildren(...groups.filter(g=>g.id).map(g=>{
  const label=document.createElement('label'),input=document.createElement('input'),text=document.createElement('span');input.type='checkbox';input.value=g.id;input.checked=selected.has(g.id);text.textContent=g.name;
  input.addEventListener('change',()=>{input.checked?selected.add(g.id):selected.delete(g.id);applySelection();});label.append(input,text);return label;
 }));
 document.querySelector('#presets').replaceChildren(...presets.map(([key,label,ids])=>{
  const b=document.createElement('button');b.textContent=label;b.dataset.key=key;b.setAttribute('aria-pressed',String(key==='chest'));
  b.addEventListener('click',()=>{selected=new Set(ids??groups.filter(g=>g.id).map(g=>g.id));applySelection(key);if(['back','row'].includes(key))view('back');else view('front');});return b;
 }));
}
async function load(sex){
 const seq=++token;activeSex=sex;
 const loading=document.querySelector('#loading');loading.hidden=false;loading.textContent='正在载入人物与肌肉贴图…';loading.classList.remove('status-error');
 document.querySelectorAll('[data-sex]').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.sex===sex)));
 try{
  if(!cache.has(sex)){
   const [gltf,marbleTex,manifest]=await Promise.all([loader.loadAsync(`${sex}/greek-${sex}-muscles.glb`),textureLoader.loadAsync(`${sex}/textures/marble-basecolor.png`),fetch(`${sex}/manifest.json`).then(r=>{if(!r.ok)throw Error(r.status);return r.json();})]);
   marbleTex.flipY=false;marbleTex.colorSpace=THREE.SRGBColorSpace;
   const parts=[],bones=[];gltf.scene.updateMatrixWorld(true);
   gltf.scene.traverse(node=>{
    if(node.isMesh){const match=node.material.name.match(/^Muscle_(\d+)_/);if(!match)throw Error('模型缺少肌群材质标识');const id=Number(match[1]);const marble=node.material.clone();marble.map=marbleTex;marble.normalMap=null;marble.roughness=.68;parts.push({mesh:node,id,muscle:node.material,marble});}
    if(node.isBone){bones.push({bone:node,q:node.quaternion.clone(),world:node.getWorldQuaternion(new THREE.Quaternion())});}
   });
   cache.set(sex,{root:gltf.scene,parts,bones,manifest});
  }
  if(seq!==token)return;
  if(current)scene.remove(current.root);current=cache.get(sex);scene.add(current.root);groups=current.manifest.groups;initControls();applySelection(activePreset);
  document.querySelector('#character-name').textContent=(sex==='male'?'男性':'女性')+' · 希腊雕塑';
  document.querySelector('#blend-link').href=`${sex}/greek-${sex}-muscles.blend`;document.querySelector('#glb-link').href=`${sex}/greek-${sex}-muscles.glb`;
  loading.hidden=true;
 }catch(error){if(seq===token){loading.textContent='模型载入失败，请刷新重试。'+error.message;loading.classList.add('status-error');}console.error(error);}
}
document.querySelectorAll('[data-sex]').forEach(el=>el.addEventListener('click',()=>load(el.dataset.sex)));
document.querySelectorAll('[data-view]').forEach(el=>el.addEventListener('click',()=>view(el.dataset.view)));
document.querySelector('#motion').addEventListener('change',event=>{motion=event.target.checked;});
new ResizeObserver(()=>{const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}).observe(stage);
function animate(ms){
 if(current){const wave=motion?(1-Math.cos(ms*.0015))*.5:0;
  for(const item of current.bones){const {bone,q,world}=item;bone.quaternion.copy(q);let angle=0,axis;
   if(bone.name.endsWith('LeftForeArm')||bone.name.endsWith('RightForeArm')){angle=wave*.9;axis=new THREE.Vector3(0,0,1);}
   else if(bone.name.endsWith('LeftArm')){angle=wave*.35;axis=new THREE.Vector3(1,0,0);}
   else if(bone.name.endsWith('RightArm')){angle=-wave*.35;axis=new THREE.Vector3(1,0,0);}
   else if(bone.name.endsWith('LeftUpLeg')){angle=wave*.25;axis=new THREE.Vector3(0,0,1);}
   else if(bone.name.endsWith('LeftLeg')){angle=-wave*.5;axis=new THREE.Vector3(0,0,1);}
   if(axis){axis.applyQuaternion(world.clone().invert());bone.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(axis.normalize(),angle));}
  }
 }
 controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);
}
requestAnimationFrame(animate);load('male');
