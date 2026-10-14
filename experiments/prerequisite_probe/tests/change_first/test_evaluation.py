import unittest

from research.prerequisite_monitor.change_first_development_20261008.evaluate import score_events, score_state, cluster_bootstrap


class EvaluationTests(unittest.TestCase):
    def test_missing_unknown_and_hallucinated_events_stay_in_denominator(self):
        refs=[{'event_id':'a','entity':'lid','time_ms':1000,'impact':'beneficial'},
              {'event_id':'b','entity':'board','time_ms':3000,'impact':'harmful'}]
        preds=[{'entity':'lid','time_ms':1000,'impact':'unknown'},
               {'entity':'pink','time_ms':4000,'impact':'beneficial'}]
        s=score_events(refs,preds,tolerance_ms=500)
        self.assertEqual(s['fn']['beneficial'],1)
        self.assertEqual(s['fn']['harmful'],1)
        self.assertEqual(s['fp']['beneficial'],1)
        self.assertEqual(s['coverage'],0)

    def test_all_unknown_cannot_get_perfect_state_accuracy(self):
        s=score_state(['true','false'],['unknown','unknown'])
        self.assertEqual(s['coverage'],0)
        self.assertEqual(s['all_decidable_accuracy'],0)

    def test_cluster_bootstrap_keeps_paired_items_together(self):
        rows=[{'cluster':'x','C4':1.0,'D4':0.0},{'cluster':'x','C4':1.0,'D4':0.0},
              {'cluster':'y','C4':0.0,'D4':1.0}]
        out=cluster_bootstrap(rows,'C4','D4',iterations=100,seed=1)
        self.assertEqual(out['clusters'],2)
        self.assertTrue(out['low'] <= out['difference'] <= out['high'])


if __name__=='__main__':
    unittest.main()
