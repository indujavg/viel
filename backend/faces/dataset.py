"""Strict input validation for a consented, labelled train/test experiment."""
from io import BytesIO
import hashlib
import re
from pathlib import Path
import zipfile
from ..images import decode_image, png_bytes

MAX_ARCHIVE = 64 * 1024 * 1024
PATTERN = re.compile(r"(train|test)/([A-Za-z0-9_-]{1,32})/([A-Za-z0-9_.-]{1,100}\.(?:png|jpg|jpeg))", re.I)


def prepare_dataset(data: bytes, root: Path):
    if not data or len(data) > MAX_ARCHIVE:
        raise ValueError("Choose a ZIP up to 64 MB.")
    rows, seen, names, total = [], set(), set(), 0
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 150:
                raise ValueError("At most 150 ZIP entries are allowed.")
            for entry in entries:
                if entry.is_dir():
                    continue
                match = PATTERN.fullmatch(entry.filename)
                if not match or entry.filename in names or entry.flag_bits & 1:
                    raise ValueError("Use train/person/photo.jpg and test/person/photo.jpg with simple unique names, without an outer folder.")
                names.add(entry.filename)
                if not 0 < entry.file_size <= 10 * 1024 * 1024:
                    raise ValueError("Each image must be nonempty and at most 10 MB.")
                total += entry.file_size
                if total > MAX_ARCHIVE:
                    raise ValueError("Decoded archive files must total at most 64 MB.")
                image = decode_image(archive.read(entry))
                digest = hashlib.sha256(image.tobytes() + str(image.size).encode()).hexdigest()
                if digest in seen:
                    raise ValueError("Duplicate decoded photos are not allowed, including across train and test.")
                seen.add(digest)
                split, label, _ = match.groups()
                if split not in ('train','test'):
                    raise ValueError('Use lowercase train and test folder names.')
                destination = root / split / label / f'{len(rows):03d}.png'
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(png_bytes(image))
                rows.append({'split':split,'label':label,'path':str(destination),'sha256':digest})
    except (zipfile.BadZipFile, RuntimeError) as error:
        raise ValueError("This ZIP could not be read.") from error
    labels = sorted({r['label'] for r in rows})
    if not 3 <= len(labels) <= 10 or len(rows) > 60:
        raise ValueError("Use 3–10 identities and at most 60 photos in total.")
    for label in labels:
        for split, minimum in [('train',3),('test',2)]:
            if sum(r['label']==label and r['split']==split for r in rows) < minimum:
                raise ValueError(f'{label}: provide at least 3 training photos and 2 separate test photos.')
    return rows
