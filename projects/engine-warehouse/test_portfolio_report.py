import unittest
from build_portfolio_report import summarize
class ReportTests(unittest.TestCase):
    def row(self):
        return dict(case='sample',accepted=True,finished=True,fault=None,observations=1,
                    checks=[dict(engine=e,seat_error_m=.001) for e in ('E1','E2','E3')])
    def test_completion_needs_three_distinct_engine_checks(self):
        r=self.row();self.assertTrue(summarize([r])[0]['passed'])
        r['checks'][2]['engine']='E1';self.assertFalse(summarize([r])[0]['passed'])
    def test_fault_or_unaccepted_never_pass(self):
        for field,value in [('fault','HOLD'),('accepted',False),('finished',False)]:
            r=self.row();r[field]=value;self.assertFalse(summarize([r])[0]['passed'])
    def test_bad_evidence_rejected(self):
        with self.assertRaises(ValueError):summarize([self.row(),self.row()])
        r=self.row();r['checks'][0]['seat_error_m']=float('nan')
        with self.assertRaises(ValueError):summarize([r])
if __name__=='__main__':unittest.main()
