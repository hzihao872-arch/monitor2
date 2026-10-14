import tempfile
import unittest
from pathlib import Path

from research.prerequisite_monitor.change_first_development_20261008.collect_and_seal import seal,verify_seal


class SealTests(unittest.TestCase):
    def test_archive_verifies_every_result_and_detects_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);run=root/'r1';run.mkdir();(run/'requests.jsonl').write_text('raw')
            arc=root/'r1.tar.gz';seal(run,arc)
            self.assertTrue(verify_seal(arc)['valid'])
            bad=root/'bad.tar.gz';bad.write_bytes(arc.read_bytes()+b'x')
            self.assertFalse(verify_seal(bad)['valid'])


if __name__=='__main__':unittest.main()
