"""Fetch exact upstream Fawkes weights; never accept a different model on failure."""
import hashlib
import os
from pathlib import Path
import shutil
import urllib.request

HASHES={'extractor_2':'ce703d481db2b83513bbdafa27434703',
        'extractor_0':'94854151fd9077997d69ceda107f9c6b'}
OFFICIAL_BASES=('https://mirror.cs.uchicago.edu/fawkes/files/',
                'https://sandlab.cs.uchicago.edu/fawkes/files/')


def fetch_weights(destination, names=('extractor_2','extractor_0')):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    for name in names:
        expected=HASHES[name]
        target=destination/(name+'.h5')
        if target.exists() and hashlib.md5(target.read_bytes()).hexdigest()==expected:
            continue
        local=os.environ.get('VIEL_FAWKES_WEIGHTS')
        if local:
            candidate=Path(local)/(name+'.h5')
            if not candidate.is_file() or hashlib.md5(candidate.read_bytes()).hexdigest()!=expected:
                raise RuntimeError('Provided Fawkes weights are missing or fail the upstream checksum: '+name)
            if candidate.resolve()!=target.resolve():shutil.copyfile(candidate,target)
            continue
        failures=[]
        for base in OFFICIAL_BASES:
            try:
                print('Fetching verified upstream weights:',base+name+'.h5',flush=True)
                with urllib.request.urlopen(base+name+'.h5',timeout=60) as response:
                    content=response.read()
                if hashlib.md5(content).hexdigest()!=expected:
                    raise ValueError('upstream checksum mismatch')
                target.write_bytes(content)
                break
            except Exception as error:
                failures.append(type(error).__name__+': '+str(error))
        else:
            raise RuntimeError('Official Fawkes weights unavailable for '+name+'; '+ '; '.join(failures))
