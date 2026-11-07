"""Install the isolated upstream Fawkes runtime, without uploading any photos."""
from io import BytesIO
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import urllib.request

ROOT=Path('/content')
SOURCE=ROOT/'fawkes'
ENV=ROOT/'viel-fawkes-py38'
REVISION='aedaa82d22504c4e7dbc86de869a6e0d943a5f2a'


def command(*args,**kwargs):
    subprocess.run([str(a) for a in args],check=True,**kwargs)


def install():
    binary=ROOT/'viel-micromamba'
    if not binary.exists():
        with urllib.request.urlopen('https://micro.mamba.pm/api/micromamba/linux-64/latest',timeout=60) as response:
            archive=tarfile.open(fileobj=BytesIO(response.read()),mode='r:bz2')
            member=archive.extractfile('bin/micromamba')
            if member is None:raise RuntimeError('Micromamba download is missing its executable.')
            binary.write_bytes(member.read());binary.chmod(0o755)
    if not (ENV/'bin/python').exists():
        command(binary,'create','-y','-p',ENV,'-c','conda-forge','python=3.8','pip<25')
    python=ENV/'bin/python'
    command(python,'-m','pip','install','tensorflow==2.4.1','keras==2.4.3','numpy==1.19.5',
            'Pillow==9.5.0','mtcnn==0.1.1','opencv-python==4.5.5.64','protobuf==3.20.3',
            'scipy==1.10.1','bleach==6.1.0','setuptools<70')
    if not SOURCE.exists():command('git','clone','https://github.com/Shawn-Shan/fawkes.git',SOURCE)
    command('git','-C',SOURCE,'checkout','--detach',REVISION)
    command(python,'-m','pip','install','--no-deps','-e',SOURCE)
    model_dir=SOURCE/'fawkes/model';model_dir.mkdir(exist_ok=True)
    hashes={'extractor_2':'ce703d481db2b83513bbdafa27434703','extractor_0':'94854151fd9077997d69ceda107f9c6b'}
    for name,expected in hashes.items():
        destination=model_dir/f'{name}.h5'
        if not destination.exists() or hashlib.md5(destination.read_bytes()).hexdigest()!=expected:
            print(f'Downloading upstream Fawkes weights: {name}')
            with urllib.request.urlopen(f'https://mirror.cs.uchicago.edu/fawkes/files/{name}.h5',timeout=120) as response:
                data=response.read()
            if hashlib.md5(data).hexdigest()!=expected:raise RuntimeError('Upstream model checksum mismatch.')
            destination.write_bytes(data)
    command(sys.executable,'-m','pip','install','fastapi>=0.115,<1','uvicorn[standard]>=0.34,<1',
            'Pillow>=11,<13','numpy>=2,<3','scikit-learn>=1.5,<2','requests>=2.32,<3')
    # Current Colab supplies matched torch/torchvision. Check compatibility below;
    # do not downgrade the host runtime to facenet-pytorch's older declared pins.
    command(sys.executable,'-m','pip','install','--no-deps','facenet-pytorch==2.6.0')
    command(sys.executable,'-c',"import torch; from facenet_pytorch import InceptionResnetV1; m=InceptionResnetV1().eval(); print(m(torch.zeros(1,3,160,160)).shape)")
    return python

if __name__=='__main__':
    install()
    print('Fawkes dependencies installed. Start the service in the next notebook cell.')
