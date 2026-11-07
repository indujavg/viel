import io
from pathlib import Path
import tempfile
import unittest
import zipfile
import numpy as np
from PIL import Image
from backend.faces.dataset import prepare_dataset
from backend.faces.metrics import summarize
from backend.images import png_bytes


def fixture_zip(duplicate=False):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        for identity in range(3):
            for split,n in [('train',3),('test',2)]:
                for index in range(n):
                    color=(identity*60+index*4+(20 if split=='test' else 0),80,100)
                    image=Image.new('RGB',(64,64),color if not duplicate else (0,0,0))
                    z.writestr(f'{split}/person_{identity}/{index}.png',png_bytes(image))
    return stream.getvalue()

class FaceProofTest(unittest.TestCase):
    def test_accepts_separate_dataset_and_records_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            rows=prepare_dataset(fixture_zip(),Path(folder))
            self.assertEqual(len(rows),15)
            self.assertEqual(len({r['sha256'] for r in rows}),15)

    def test_rejects_duplicate_and_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):prepare_dataset(fixture_zip(True),Path(folder))
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,'w') as z:z.writestr('../photo.png',b'x')
            with self.assertRaises(ValueError):prepare_dataset(stream.getvalue(),Path(folder))

    def test_reports_failure_and_weak_baseline_honestly(self):
        self.assertEqual(summarize(['a','a'],['a','a'],['a','a'],'a')['interpretation'],'no-reduction-in-this-test')
        result=summarize(['a','a'],['b','a'],['b','b'],'a')
        self.assertEqual(result['interpretation'],'inconclusive-low-baseline')
        result=summarize(['a','a'],['a','a'],['b','b'],'a')
        self.assertEqual(result['drop_percentage_points'],100)
        self.assertEqual(result['interpretation'],'reduced-recognition-in-this-test')

    def test_encoder_library_compatibility_when_installed(self):
        import importlib.util
        if importlib.util.find_spec('facenet_pytorch') is None:self.skipTest('facenet-pytorch not installed')
        import torch
        from facenet_pytorch import InceptionResnetV1
        with torch.no_grad():
            output=InceptionResnetV1().eval()(torch.zeros(1,3,160,160))
        self.assertEqual(tuple(output.shape),(1,512))
        self.assertTrue(torch.isfinite(output).all())

if __name__=='__main__':unittest.main()
