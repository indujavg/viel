"""Controlled, limited test: fit two identity classifiers on a fixed independent encoder."""
from pathlib import Path
import hashlib
import importlib.metadata
import numpy as np
from PIL import Image
from .metrics import summarize
from ..images import pixel_metrics


class FaceEvaluator:
    def __init__(self):
        import torch
        from facenet_pytorch import MTCNN, InceptionResnetV1
        self.torch = torch
        self.detector = MTCNN(image_size=160, margin=0, keep_all=True, device='cpu')
        self.encoder = InceptionResnetV1(pretrained='vggface2').eval().to('cpu')
        # Fingerprint the actual loaded weights, not only their marketing name.
        digest = hashlib.sha256()
        for name,value in sorted(self.encoder.state_dict().items()):
            digest.update(name.encode());digest.update(value.cpu().numpy().tobytes())
        self.weight_hash = digest.hexdigest()

    def embed(self, path):
        with Image.open(path) as image:
            faces = self.detector(image.convert('RGB'))
        if faces is None or len(faces) != 1:
            raise ValueError('Each proof photo must contain exactly one detectable face; ambiguous photos are rejected.')
        with self.torch.no_grad():
            value = self.encoder(faces).cpu().numpy()[0]
        if not np.isfinite(value).all():
            raise ValueError('Face encoder returned invalid values.')
        return value

    def evaluate(self, rows, target, runner, mode, cancel, progress):
        from sklearn.linear_model import LogisticRegression
        training = [r for r in rows if r['split']=='train']
        testing = [r for r in rows if r['split']=='test']
        if target not in {r['label'] for r in training}:
            raise ValueError('Target must match a person folder in the ZIP.')
        progress('Encoding clean training and held-out photos')
        def embeddings(records):
            output=[]
            for r in records:
                if cancel.is_set():raise RuntimeError('Experiment cancelled.')
                output.append(self.embed(r['path']))
            return np.stack(output)
        clean_x = embeddings(training)
        test_x = embeddings(testing)
        train_y = [r['label'] for r in training]
        y = [r['label'] for r in testing]
        baseline = LogisticRegression(C=1.0,max_iter=1000,random_state=42).fit(clean_x,train_y)
        # Only target training images are cloaked; held-out photos remain clean.
        target_dir = Path(next(r['path'] for r in training if r['label']==target)).parent
        progress('Running real Fawkes on the target identity training photos')
        runner.run_directory(target_dir,mode,cancel)
        altered_x = clean_x.copy()
        quality=[]
        for i,r in enumerate(training):
            if r['label']!=target:continue
            result=Path(r['path']).with_name(Path(r['path']).stem+'_cloaked.png')
            if not result.is_file():raise ValueError('A training photo could not be cloaked; no proof score is available.')
            with Image.open(r['path']) as original, Image.open(result) as candidate:
                metrics=pixel_metrics(original.convert('RGB'),candidate.convert('RGB'))
            if metrics['max_channel_change']==0:raise ValueError('An unchanged target training image invalidated the run.')
            quality.append(metrics)
            altered_x[i]=self.embed(result)
        progress('Fitting the cloaked-training classifier and evaluating identical held-out photos')
        model=LogisticRegression(C=1.0,max_iter=1000,random_state=42).fit(altered_x,train_y)
        report=summarize(y,baseline.predict(test_x),model.predict(test_x),target)
        report.update({'method':'upstream-fawkes','fawkes_revision':runner_revision(),
            'mode':mode,'cloaking_randomness':'upstream-default-uncontrolled','encoder':'facenet-pytorch/InceptionResnetV1/vggface2',
            'encoder_weights_sha256':self.weight_hash,'classifier':'LogisticRegression(C=1.0, random_state=42)',
            'training_count':len(training),'total_test_count':len(testing),
            'training_quality':quality,'dataset_manifest':[{k:r[k] for k in ('split','label','sha256')} for r in rows],
            'versions':{name:importlib.metadata.version(name) for name in ('torch','facenet-pytorch','scikit-learn')},
            'status':'measured-limited-experiment','human_similarity':'not-assessed',
            'meta_ai_protection':'not-tested'})
        return report


def runner_revision():
    from .fawkes import REVISION
    return REVISION
