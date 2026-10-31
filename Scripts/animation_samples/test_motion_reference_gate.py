"""Reference provenance and publication invalidation regressions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import motion_reference_gate as gate


class ReferenceGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.refs=self.root/'refs';self.refs.mkdir()
        self.name='db_upright_row';self.sex='male'
        self.ref=json.loads((gate.REFERENCES/f'{self.name}.json').read_text())
        self.folder=self.root/'docs/animation-library/male';self.folder.mkdir(parents=True)
        self.scene=self.folder/f'{self.name}.blend';self.scene.write_bytes(b'fixture scene')
        self.image=self.folder/'comparison.png';self.image.write_bytes(b'fixture rendered evidence')
        self.mock=patch.object(gate,'REFERENCES',self.refs);self.mock.start()
        self.addCleanup(self.mock.stop);self.addCleanup(self.tmp.cleanup)
        self.write_ref()
        self.frames=list(range(1,122))
        self.report=dict(status='passed',sceneSHA256=gate.digest(self.scene),referenceSHA256=gate.digest(self.refs/f'{self.name}.json'),specificationSHA256=gate.spec_digest(self.name),checkerSHA256=gate.digest(gate.__file__),frames=self.frames,profile=gate.PROFILE,failures=[],samples=[dict(frame=f,side=s,elevation=84,elbowFlexion=120,wristBend=0,upperForward=.23,foreDown=.4,foreInward=.6,elbowAboveWrist=.12,wristBelowShoulder=.15,wristForward=.25,elbowOutward=.3) for f in self.frames for s in ['Left','Right']])
        evidence={str(self.image.relative_to(self.root)):gate.digest(self.image)}
        self.review=dict(status='accepted',sceneSHA256=gate.digest(self.scene),frames=[1,31,61,91],evidence=evidence,motionReference=dict(status='accepted',referenceSHA256=self.report['referenceSHA256'],notes='Fixture comparison',views=['main','front','side'],evidence=evidence,comparisons=[dict(phase=o['phase'],frame=f,sourceId=o['sourceId'],locator=o['locator'],notes='Fixture stage observation') for o,f in zip(self.ref['observations'],[1,31,61,91])]))
    def write_ref(self):
        (self.refs/f'{self.name}.json').write_text(json.dumps(self.ref))
    def check(self,visual=True):
        (self.folder/f'{self.name}-reference-audit.json').write_text(json.dumps(self.report))
        (self.folder/f'{self.name}-review.json').write_text(json.dumps(self.review))
        return gate.require_reference_pass(self.sex,self.name,self.root,visual)
    def test_complete_reference_and_scene_match(self):
        self.assertEqual(self.check(),'reference_checked')
    def test_missing_pending_wrong_variant_and_partial_observations(self):
        original=copy.deepcopy(self.ref)
        for mutate in [lambda r:r.update(status='pending'),lambda r:r.update(exerciseId='0363'),lambda r:r['variant'].update(loadedSides=['Left']),lambda r:r.update(observations=r['observations'][:3]),lambda r:r['sources'][0].update(kind='synthetic')]:
            self.ref=copy.deepcopy(original);mutate(self.ref);self.write_ref()
            with self.assertRaises(RuntimeError):gate.load_reference(self.name)
        (self.refs/f'{self.name}.json').unlink()
        with self.assertRaises(RuntimeError):gate.load_reference(self.name)
    def test_source_scene_checker_and_evidence_changes_invalidate(self):
        for path in [self.refs/f'{self.name}.json',self.scene,self.image]:
            old=path.read_bytes();path.write_bytes(old+b' ')
            with self.assertRaises(RuntimeError):self.check()
            path.write_bytes(old)
        self.report['checkerSHA256']='stale'
        with self.assertRaises(RuntimeError):self.check()
    def test_partial_failed_and_false_positive_reports_rejected(self):
        old=copy.deepcopy(self.report)
        for mutate in [lambda r:r.update(frames=[1,61]),lambda r:r.update(status='failed'),lambda r:r['samples'].pop(),lambda r:r['samples'][120].update(elevation=136),lambda r:r['samples'][120].update(foreInward=-.5),lambda r:r['samples'][120].update(wristBend=float('nan'))]:
            self.report=copy.deepcopy(old);mutate(self.report)
            with self.assertRaises(RuntimeError):self.check()
    def test_pending_partial_or_wrong_phase_visual_review_rejected(self):
        old=copy.deepcopy(self.review)
        for mutate in [lambda r:r['motionReference'].update(status='pending'),lambda r:r['motionReference']['comparisons'].pop(),lambda r:r['motionReference']['comparisons'][0].update(locator='unseen timestamp'),lambda r:r['motionReference'].update(views=['main'])]:
            self.review=copy.deepcopy(old);mutate(self.review)
            with self.assertRaises(RuntimeError):self.check()
    def test_other_sex_cannot_reuse_receipt(self):
        with self.assertRaises(RuntimeError):gate.require_reference_pass('female',self.name,self.root)
    def test_upright_row_cannot_downgrade_to_visual_only_profile(self):
        self.ref['profile']='visual_reference_v1';self.write_ref()
        with self.assertRaises(RuntimeError):gate.load_reference(self.name)
    def test_legacy_is_exact_scene_and_spec_only_not_bake_permission(self):
        (self.refs/'legacy-scenes.json').write_text(json.dumps(dict(scenes={f'male/{self.name}':dict(sceneSHA256=gate.digest(self.scene),specificationSHA256=gate.spec_digest(self.name))})))
        (self.refs/f'{self.name}.json').unlink()
        self.assertEqual(gate.require_reference_pass('male',self.name,self.root),'legacy_reference_review_pending')
        with self.assertRaises(RuntimeError):gate.load_reference(self.name)
        self.scene.write_bytes(b'changed scene')
        with self.assertRaises(RuntimeError):gate.require_reference_pass('male',self.name,self.root)
    def test_bake_batch_preflight_fails_before_subprocess(self):
        import library_pipeline
        (self.refs/f'{self.name}.json').unlink()
        with patch('sys.argv',['pipeline','bake','--exercises',self.name,'--root',str(self.root)]),patch('library_pipeline.subprocess.run') as run:
            with self.assertRaises(RuntimeError):library_pipeline.main()
            run.assert_not_called()

if __name__=='__main__':unittest.main()
