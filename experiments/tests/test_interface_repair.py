import unittest
from experiments.interface_repair_20261003 import probe_usable

def records(method):
    return [dict(tick=q,method=method,parse_status='valid',budget_reason=None,
                 memory_in='' if q==0 or method=='S0' else 'previous observation',
                 memory_out=None if method=='S0' else 'previous observation',
                 cost={'output_tokens_known':90,'memory_tokens':0 if q==0 else 4}) for q in range(3)]

class RepairGateTest(unittest.TestCase):
    def test_rejects_actual_v1_parser_failures(self):
        import json
        from pathlib import Path
        rows=[json.loads(x) for x in Path('experiments/artifacts/r1_upstream_diagnostic_v1/ep618_S1/records.jsonl').read_text('utf-8').splitlines()][:3]
        self.assertFalse(probe_usable(records('S0'),rows))

    def test_rejects_valid_json_without_memory_handoff(self):
        s1=records('S1');s1[1]['memory_in']=''
        self.assertFalse(probe_usable(records('S0'),s1))

    def test_rejects_truncation_and_partial_output(self):
        for field,value in [('parse_status','partial_invalid'),('budget_reason','input_tokens')]:
            s1=records('S1');s1[0][field]=value
            self.assertFalse(probe_usable(records('S0'),s1))
        s1=records('S1');s1[0]['cost']['output_tokens_known']=256
        self.assertFalse(probe_usable(records('S0'),s1))

    def test_gate_does_not_select_on_truth_labels(self):
        self.assertTrue(probe_usable(records('S0'),records('S1')))

if __name__=='__main__':unittest.main()
