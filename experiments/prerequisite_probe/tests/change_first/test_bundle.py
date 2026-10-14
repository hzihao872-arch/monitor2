import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np

from experiments.prerequisite_probe.change_first_monitor.prefix import materialize_frames
from research.prerequisite_monitor.change_first_development_20261008.build_bundle import build_bundle
from research.prerequisite_monitor.change_first_development_20261008.verify_bundle import verify_bundle


class BundleTests(unittest.TestCase):
    def test_private_data_excluded_and_tamper_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            import json
            p=root/'pilot'; materialize_frames([np.zeros((16,16,3),np.uint8)],0,p/'qabc')
            (p/'queries.json').write_text(json.dumps({'queries':[{'query_id':'qabc','prefix_dir':'qabc','goal':'g','as_of_ms':0,
              'prefix_signature':json.loads((p/'qabc'/'manifest.json').read_text())['signature']}]}))
            (root/'private_eval').mkdir(); (root/'private_eval'/'secret.txt').write_text('truth')
            bundle=root/'x.zip'; build_bundle(p,bundle)
            self.assertTrue(verify_bundle(bundle)['valid'])
            with zipfile.ZipFile(bundle) as z:
                self.assertFalse(any('private_eval' in n or 'secret' in n for n in z.namelist()))
            bad=root/'bad.zip'
            with zipfile.ZipFile(bundle) as src,zipfile.ZipFile(bad,'w') as dst:
                for name in src.namelist():
                    data=src.read(name)
                    if name.endswith('.png'):data+=b'x'
                    dst.writestr(name,data)
            self.assertFalse(verify_bundle(bad)['valid'])

            sneaky=root/'sneaky.zip'
            with zipfile.ZipFile(bundle) as src,zipfile.ZipFile(sneaky,'w') as dst:
                manifest=json.loads(src.read('bundle_manifest.json'))
                extra=b'private truth'
                import hashlib
                manifest['members']['notes.txt']={'sha256':hashlib.sha256(extra).hexdigest(),'bytes':len(extra)}
                for name in src.namelist():
                    dst.writestr(name,json.dumps(manifest).encode() if name=='bundle_manifest.json' else src.read(name))
                dst.writestr('notes.txt',extra)
            self.assertFalse(verify_bundle(sneaky)['valid'])

    def test_manifest_with_private_extra_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'pilot';m=materialize_frames([np.zeros((16,16,3),np.uint8)],0,p/'qabc')
            import json
            (p/'queries.json').write_text(json.dumps({'queries':[{'query_id':'qabc','prefix_dir':'qabc','goal':'g',
              'as_of_ms':0,'prefix_signature':m['signature']}]}))
            m['truth']='secret'
            (p/'qabc'/'manifest.json').write_text(json.dumps(m))
            self.assertRaises(ValueError,build_bundle,p,root/'bad.zip')


if __name__=='__main__':unittest.main()
