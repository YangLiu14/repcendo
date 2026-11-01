"""A numerical pass alone cannot publish a plan animation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import plan_reference_gate as gate

class PlanReferenceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.base=gate.folder(self.root,'male','curl');self.base.mkdir(parents=True)
        self.scene=self.base/'curl.blend';self.scene.write_bytes(b'fixture scene')
        self.evidence=self.base/'evidence.jpg';self.evidence.write_bytes(b'fixture review')
        self.ref={'observations':[dict(phase=p,sourceId='human',locator=p) for p in gate.PHASES]}
        mock=patch.object(gate,'load_reference',return_value=(self.ref,'reference-hash'));mock.start();self.addCleanup(mock.stop)
        self.audit=dict(status='passed',failures=[],sceneSHA256=gate.digest(self.scene),checkerSHA256=gate.digest(gate.__file__),specificationSHA256=gate.specification_digest('curl'),referenceSHA256='reference-hash',frames=list(range(1,122)))
        self.review=dict(status='accepted',notes='actual comparison fixture',sceneSHA256=gate.digest(self.scene),referenceSHA256='reference-hash',views=['main','front','side'],frames=[1,31,61,91],evidence={str(self.evidence.relative_to(self.root)):gate.digest(self.evidence)},comparisons=[dict(**o,frame=f,notes='compared') for o,f in zip(self.ref['observations'],[1,31,61,91])])
    def check(self):
        (self.base/'curl-reference-audit.json').write_text(json.dumps(self.audit))
        (self.base/'curl-reference-review.json').write_text(json.dumps(self.review))
        return gate.require_pass('male','curl',self.root)
    def test_complete(self):self.check()
    def test_pending_failed_or_partial(self):
        for data,key,value in [(self.review,'status','pending'),(self.audit,'failures',['collision']),(self.audit,'frames',[1,61])]:
            old=data[key];data[key]=value
            with self.assertRaises(RuntimeError):self.check()
            data[key]=old
    def test_stale_hashes(self):
        for data in [self.audit,self.review]:
            for key in [k for k in data if k.endswith('SHA256')]:
                old=data[key];data[key]='stale'
                with self.assertRaises(RuntimeError):self.check()
                data[key]=old
    def test_wrong_phase_and_source(self):
        old=copy.deepcopy(self.review['comparisons'])
        for key,val in [('frame',97),('locator','wrong'),('sourceId','other')]:
            self.review['comparisons'][2][key]=val
            with self.assertRaises(RuntimeError):self.check()
            self.review['comparisons']=copy.deepcopy(old)
    def test_changed_scene_or_evidence(self):
        for p in [self.scene,self.evidence]:
            old=p.read_bytes();p.write_bytes(b'changed')
            with self.assertRaises(RuntimeError):self.check()
            p.write_bytes(old)

if __name__=='__main__':unittest.main()
