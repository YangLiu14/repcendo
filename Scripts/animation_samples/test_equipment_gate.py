import json,tempfile,unittest
from pathlib import Path
from equipment_gate import require_equipment_pass,digest,ROOT
class EquipmentGateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.folder=self.root/'docs/animation-plan-v3';self.scene=self.folder/'male/leg_press.blend';self.scene.parent.mkdir(parents=True);self.scene.write_bytes(b'fixture');self.image=self.folder/'equipment-review.jpg';self.image.write_bytes(b'evidence')
  self.r=dict(passed=True,failures=[],frames=list(range(1,122)),sceneSHA256=digest(self.scene),validatorSHA256=digest(Path(__file__).with_name('verify_equipment_refit.py')),referenceSHA256=digest(ROOT/'docs/equipment-references/equipment-audit.json'))
  self.r['metrics']=dict(fixed_drift=0.,link_length_variation=0.,slide_error=0.,cable_error=0.)
  self.v=dict(status='accepted',sceneSHA256=digest(self.scene),notes='Compared actual photo and main/side frames',views=['main','side'],evidence={str(self.image.relative_to(self.root)):digest(self.image)})
 def check(self):
  (self.folder/'equipment-validation.json').write_text(json.dumps({'male/leg_press':self.r}));(self.folder/'equipment-visual-review.json').write_text(json.dumps({'male/leg_press':self.v}));require_equipment_pass('male','leg_press',self.root)
 def test_complete(self):self.check()
 def test_partial_or_failed(self):
  for k,v in [('frames',[1,61]),('passed',False),('failures',['moving rail'])]:
   old=self.r[k];self.r[k]=v
   with self.assertRaises(RuntimeError):self.check()
   self.r[k]=old
 def test_changed_sources(self):
  for k in ['sceneSHA256','validatorSHA256','referenceSHA256']:
   old=self.r[k];self.r[k]='stale'
   with self.assertRaises(RuntimeError):self.check()
   self.r[k]=old
 def test_invalid_measurements(self):
  for value in [.02,float("nan")]:
   self.r["metrics"]["slide_error"]=value
   with self.assertRaises(RuntimeError):self.check()
 def test_unreviewed_or_changed_image(self):
  self.v['status']='pending'
  with self.assertRaises(RuntimeError):self.check()
  self.v['status']='accepted';self.image.write_bytes(b'changed')
  with self.assertRaises(RuntimeError):self.check()
if __name__=='__main__':unittest.main()
