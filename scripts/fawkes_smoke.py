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
from fawkes_weights import fetch_weights
fetch_weights(model_dir, names=('extractor_2',))
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
