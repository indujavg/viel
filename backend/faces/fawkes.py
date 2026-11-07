"""Run actual pinned upstream Fawkes in an isolated legacy Python environment."""
from pathlib import Path
import os
import subprocess
import tempfile
import threading
import time
import hashlib
from PIL import Image
from ..images import png_bytes, pixel_metrics

REVISION = 'aedaa82d22504c4e7dbc86de869a6e0d943a5f2a'
MODES = ('low','mid','high')


class FawkesRunner:
    def __init__(self, python=None, source=None):
        self.python = python or os.environ.get('VIEL_FAWKES_PYTHON','')
        self.source = Path(source or os.environ.get('VIEL_FAWKES_SOURCE','/content/fawkes'))
        if not self.python or not Path(self.python).is_file():
            raise RuntimeError('Set VIEL_FAWKES_PYTHON to the isolated Python 3.8 executable.')
        revision = subprocess.check_output(['git','-C',str(self.source),'rev-parse','HEAD'],text=True).strip()
        if revision != REVISION:
            raise RuntimeError('Fawkes source revision does not match the reviewed revision.')
        subprocess.run([self.python,'-c','import tensorflow, keras, fawkes'],check=True,
                       cwd=self.source,timeout=90,stdout=subprocess.DEVNULL)

    def run_directory(self, directory: Path, mode: str, cancel: threading.Event):
        if mode not in MODES:
            raise ValueError('Choose low, mid, or high.')
        # CPU avoids legacy TensorFlow/CUDA incompatibility in current Colab.
        env = {**os.environ,'CUDA_VISIBLE_DEVICES':'','TF_CPP_MIN_LOG_LEVEL':'3'}
        command = [self.python,str(self.source/'fawkes/protection.py'),'-d',str(directory),
                   '--mode',mode,'--gpu','','--batch-size','1','--format','png']
        with tempfile.TemporaryFile() as log:
            process = subprocess.Popen(command,cwd=self.source,env=env,stdout=log,stderr=subprocess.STDOUT)
            started = time.monotonic()
            try:
                while process.poll() is None:
                    if cancel.wait(0.25) or time.monotonic()-started > 1800:
                        raise RuntimeError('Fawkes cancelled or exceeded 30 minutes.')
                if process.returncode:
                    raise RuntimeError('Upstream Fawkes failed. Check the isolated installation and model downloads.')
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:process.kill();process.wait()

    def protect(self, image, mode, cancel):
        with tempfile.TemporaryDirectory(prefix='viel-face-') as folder:
            root = Path(folder)
            (root/'input.png').write_bytes(png_bytes(image))
            self.run_directory(root,mode,cancel)
            output = root/'input_cloaked.png'
            if not output.is_file():
                raise ValueError('Fawkes produced no cloak. A detectable face is required.')
            with Image.open(output) as opened:
                result = opened.convert('RGB')
            metrics = pixel_metrics(image,result)
            if metrics['max_channel_change'] == 0:
                raise ValueError('Fawkes returned unchanged pixels; no cloak is available.')
            data = png_bytes(result)
            return data, {'method':'upstream-fawkes','revision':REVISION,'mode':mode,
                'status':'experimental-unverified','protection_test':'not-run',
                'output_sha256':hashlib.sha256(data).hexdigest(),**metrics}
