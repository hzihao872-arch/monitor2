import json
import tempfile
import unittest
from pathlib import Path

from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger, BudgetExceeded, AmbiguousRequest
from experiments.prerequisite_probe.change_first_monitor.runner import run,unknown_answers
from experiments.prerequisite_probe.change_first_monitor.backends import ScriptedBackend
from experiments.prerequisite_probe.change_first_monitor.prefix import materialize_frames
import numpy as np


class LedgerTests(unittest.TestCase):
    def test_complete_request_is_reused_without_new_call(self):
        with tempfile.TemporaryDirectory() as td:
            calls=[]
            req={'stage':'L2','arm':'C4','prompt':'p','images':[],'image_hashes':[],'limits':(2200,640),'prefix_signature':'abc'}
            ledger=RequestLedger(td,'protocol-a',max_requests=1)
            self.assertEqual(ledger.invoke(req,lambda r: calls.append(1) or '{}'),'{}')
            again=RequestLedger(td,'protocol-a',max_requests=1)
            self.assertEqual(again.invoke(req,lambda r: calls.append(1) or 'wrong'),'{}')
            self.assertEqual(len(calls),1)
            self.assertRaises(BudgetExceeded, again.invoke,dict(req,prompt='new'),lambda r:'{}')

    def test_pending_is_ambiguous_and_counts_budget(self):
        with tempfile.TemporaryDirectory() as td:
            req={'stage':'V1','arm':'shared','prompt':'p','images':[],'image_hashes':[],'limits':(5000,768),'prefix_signature':'x'}
            ledger=RequestLedger(td,'protocol-b',max_requests=1)
            def crash(r):
                raise RuntimeError('lost response')
            self.assertRaises(RuntimeError,ledger.invoke,req,crash)
            resumed=RequestLedger(td,'protocol-b',max_requests=1)
            self.assertRaises(AmbiguousRequest,resumed.invoke,req,lambda r:'{}')
            self.assertEqual(resumed.issued_count,1)

    def test_identity_change_cannot_resume_same_run(self):
        with tempfile.TemporaryDirectory() as td:
            RequestLedger(td,'old',max_requests=96)
            self.assertRaises(ValueError,RequestLedger,td,'new',96)

    def test_remote_window_file_can_precede_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'window.json').write_text('{"window_start_epoch":1}')
            (Path(td)/'.run.lock').write_text('')
            ledger=RequestLedger(td,'protocol-a',max_requests=96)
            self.assertEqual(ledger.issued_count,0)

    def test_one_query_block_then_resume_remaining_without_extra_requests(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'input';source.mkdir()
            queries=[]
            for i in range(2):
                q=f'q{i}';m=materialize_frames([np.zeros((8,8,3),np.uint8)],0,source/q)
                queries.append({'query_id':q,'prefix_dir':q,'goal':'g','as_of_ms':0,'prefix_signature':m['signature']})
            (source/'queries.json').write_text(json.dumps({'queries':queries}))
            backend=ScriptedBackend(unknown_answers())
            first=run(source,root/'run',['D4','K4','C4'],backend,96,max_queries=1)
            self.assertEqual(first['issued_requests'],10)
            second=run(source,root/'run',['D4','K4','C4'],backend,96,max_queries=2)
            self.assertEqual(second['issued_requests'],20)


if __name__=='__main__':
    unittest.main()
