"""Real-model cloak smoke test on skimage's NASA astronaut sample; no efficacy claim."""
from pathlib import Path
import hashlib
import json
import os
import tempfile
import urllib.request
import numpy as np
from PIL import Image
from skimage import data
import fawkes

model_dir=Path(fawkes.__file__).parent/'model'
model_dir.mkdir(exist_ok=True)
for name,expected in {'extractor_2':'ce703d481db2b83513bbdafa27434703'}.items():
    target=model_dir/(name+'.h5')
    with urllib.request.urlopen('https://mirror.cs.uchicago.edu/fawkes/files/'+name+'.h5',timeout=120) as response:
        content=response.read()
    if hashlib.md5(content).hexdigest()!=expected:raise RuntimeError('Model checksum mismatch')
    target.write_bytes(content)
os.environ['CUDA_VISIBLE_DEVICES']=''
from fawkes.protection import Fawkes
with tempfile.TemporaryDirectory() as folder:
    original=Image.fromarray(data.astronaut())
    source=Path(folder)/'astronaut.png';original.save(source)
    protector=Fawkes('extractor_2',None,1,mode='low')
    protector.run_protection([str(source)],format='png')
    result=source.with_name('astronaut_cloaked.png')
    if not result.exists():raise RuntimeError('Upstream Fawkes did not produce an image')
    with Image.open(result) as candidate:
        if candidate.size!=original.size:raise RuntimeError('Unexpected dimensions')
        maximum=int(np.abs(np.asarray(candidate).astype('int16')-np.asarray(original).astype('int16')).max())
        if maximum==0:raise RuntimeError('Unchanged result')
    print(json.dumps({'real_model_cloak_smoke':'passed','max_channel_change':maximum,
                     'recognition_protection':'not-tested','image':'skimage NASA astronaut sample'}))
