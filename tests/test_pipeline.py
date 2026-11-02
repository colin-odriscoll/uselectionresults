"""Synthetic fixtures are confined to tests; never copied to public/."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from catalog import seed
from validate import validate, ROOT
from pipeline import parse_minnesota, guard_minnesota, collect_minnesota, atomic_json, apply_editorial, MN_FILES

EVIDENCE=dict(sourceId='mn-sos',url='https://electionresultsfiles.sos.mn.gov/20261103/ussenate.txt',retrievedAt='2026-11-02T17:00:00Z',sourceUpdatedAt=None,sha256='a'*64)
def fixture(office='senate',district='',count=10):
    label={'senate':'U.S. Senator','governor':'Governor & Lt Governor','house':'U.S. Representative District '+str(district)}[office]
    return f'MN;;;0102;{label};{district};0001;Synthetic Test Candidate;;;DFL;1;5;{count};100.00;{count}'
def populated():
    data=seed()
    next(r for r in data['races'] if r['id']=='MN-senate-2')['official']=parse_minnesota(fixture(),'senate',EVIDENCE)['MN-senate-2']
    return data
class PipelineTests(unittest.TestCase):
    def test_inventory(self):
        data=validate(seed())
        self.assertEqual([sum(r['office']==o for r in data['races']) for o in ['house','senate','governor']],[435,35,36])
        self.assertTrue(all(r['official'] is None for r in data['races']))
    def test_valid_totals(self): validate(populated())
    def test_unknown_not_zero(self):
        self.assertIsNone(seed()['races'][0]['official'])
    def test_test_mode_rejected(self):
        for mode in ['Test','TEST','Mock','Sample']:
            with self.assertRaises(ValueError): guard_minnesota(f'<h1>{mode} Results Tuesday, November 3, 2026</h1>')
    def test_wrong_election_rejected(self):
        with self.assertRaises(ValueError): guard_minnesota('Unofficial Results November 5, 2024')
        guard_minnesota('Unofficial Results Tuesday, November 3, 2026')
    def test_negative_votes_rejected(self):
        with self.assertRaises(ValueError): parse_minnesota(fixture(count=-1),'senate',EVIDENCE)
    def test_duplicate_candidate_rejected(self):
        data=populated();o=next(r['official'] for r in data['races'] if r['official'])
        o['candidates']*=2;o['totalVotes']*=2
        with self.assertRaises(AssertionError): validate(data)
    def test_sum_mismatch_rejected(self):
        data=populated();next(r['official'] for r in data['races'] if r['official'])['totalVotes']=11
        with self.assertRaises(AssertionError): validate(data)
    def test_reporting_mismatch_rejected(self):
        data=populated();next(r['official'] for r in data['races'] if r['official'])['reporting']['counted']=6
        with self.assertRaises(AssertionError): validate(data)
    def test_wrong_geography_rejected(self):
        with self.assertRaises(ValueError): parse_minnesota(fixture().replace('MN;;;','MN;01;;'),'senate',EVIDENCE)
    def test_source_type_rejected(self):
        data=populated();o=next(r['official'] for r in data['races'] if r['official']);o['sourceId']='cnn'
        with self.assertRaises(AssertionError): validate(data)
    def test_dangerous_url_rejected(self):
        data=populated();o=next(r['official'] for r in data['races'] if r['official']);o['url']='javascript:alert(1)'
        with self.assertRaises(Exception): validate(data)
    def test_unknown_call_candidate_rejected(self):
        data=populated();r=next(r for r in data['races'] if r['official'])
        r['calls']=[dict(sourceId='cnn',url='https://www.cnn.com/politics',retrievedAt=EVIDENCE['retrievedAt'],calledAt=EVIDENCE['retrievedAt'],candidateId='absent',status='called')]
        with self.assertRaises(AssertionError): validate(data)
    def test_zero_votes_do_not_certify(self):
        data=populated();r=next(r for r in data['races'] if r['official'])
        self.assertIsNone(r['certification']);self.assertEqual(r['calls'],[])
    def test_truncated_feed(self):
        with self.assertRaises(ValueError): parse_minnesota('MN;broken','senate',EVIDENCE)
    def test_complete_adapter(self):
        page='Unofficial Results November 3, 2026 '+ ' '.join('https://electionresultsfiles.sos.mn.gov/20261103/'+f for f in MN_FILES.values())
        def fetcher(url):
            if 'Index?' in url:return page.encode(),None
            office=next(o for o,f in MN_FILES.items() if url.endswith(f))
            body='\n'.join(fixture(office,str(i)) for i in range(1,9)) if office=='house' else fixture(office)
            return body.encode(),None
        with tempfile.TemporaryDirectory() as d:
            result=collect_minnesota({'id':'mn-sos'},Path(d),fetcher)
            self.assertEqual(len(result),10)
            self.assertTrue(list(Path(d).glob('*.raw')))
    def test_atomic_write(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.json';atomic_json(path,{'a':1});self.assertEqual(json.loads(path.read_text()),{'a':1})
            self.assertFalse(path.with_suffix('.tmp').exists())
    def test_editorial_retraction_and_removal(self):
        data=populated();r=next(r for r in data['races'] if r['official'])
        call=dict(raceId=r['id'],sourceId='cnn',url='https://www.cnn.com/politics',retrievedAt=EVIDENCE['retrievedAt'],calledAt=EVIDENCE['retrievedAt'],candidateId=r['official']['candidates'][0]['id'],status='retracted')
        apply_editorial(data,{'calls':[call],'certifications':[]});validate(data)
        self.assertEqual(r['calls'][0]['status'],'retracted')
        apply_editorial(data,{'calls':[],'certifications':[]});self.assertEqual(r['calls'],[])
    def test_failure_preserves_snapshot(self):
        import pipeline
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'config').mkdir();(root/'public/data').mkdir(parents=True)
            snapshot=populated();atomic_json(root/'public/data/results.json',snapshot)
            sources=json.loads((ROOT/'config/sources.json').read_text());sources[0]['notBefore']='2000-01-01T00:00:00Z'
            atomic_json(root/'config/sources.json',sources);atomic_json(root/'config/editorial.json',{'calls':[],'certifications':[]})
            with patch.object(pipeline,'ROOT',root), patch.object(pipeline,'collect_minnesota',side_effect=ValueError('TEST RESULTS')):
                self.assertEqual(pipeline.run(),1)
            self.assertEqual(json.loads((root/'public/data/results.json').read_text()),snapshot)
            self.assertEqual(json.loads((root/'public/data/health.json').read_text())['sources'][0]['status'],'error')
if __name__=='__main__':unittest.main()
