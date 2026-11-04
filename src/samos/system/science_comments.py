"""Edit only science-logbook Comment cells, with stale-file and atomic-write guards.

No SAMOS dependencies. Original 12-column science exposure rows remain intact.
"""
import csv
import hashlib
import io
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone

HEADER = ('Date','Local Time','Target','Filter','Repeats','Exposure Time',
          'Filename','Mask Name','Grating','Sp. Exp.T','Sp. Filename','Comment')


def _decode(data):
    text = data.decode('utf-8-sig')
    return list(csv.reader(io.StringIO(text, newline='')))


def read_science(path):
    path = Path(path)
    raw = path.read_bytes()
    rows = _decode(raw)
    if list(HEADER) not in rows:
        raise ValueError('This is not a recognized 12-column SAMOS science logbook')
    header_index = rows.index(list(HEADER))
    candidates = [(i, row) for i, row in enumerate(rows[header_index + 1:], header_index + 1)
                  if len(row) == 12 and row[6].strip() and row[2] != 'CONFIG_EVENT']
    return hashlib.sha256(raw).hexdigest(), rows, candidates


def update_comment(path, row_index, new_comment, expected_sha):
    """Replace only column 11. Refuse concurrent changes, metadata, missing exposures."""
    path = Path(path)
    new_comment = str(new_comment)
    if len(new_comment) > 20000:
        raise ValueError('Comment exceeds 20,000 characters')
    # Permit multiline CSV cells, but not NUL bytes.
    if '\x00' in new_comment:
        raise ValueError('NUL character in comment')
    with path.open('rb') as src:
        raw = src.read()
        mode = os.fstat(src.fileno()).st_mode & 0o777
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise RuntimeError('Logbook changed since it was opened. Refresh before editing.')
    rows = _decode(raw)
    if list(HEADER) not in rows or row_index <= rows.index(list(HEADER)):
        raise ValueError('Invalid science logbook row')
    if not (0 <= row_index < len(rows) and len(rows[row_index]) == 12 and
            rows[row_index][6].strip() and rows[row_index][2] != 'CONFIG_EVENT'):
        raise ValueError('Only an existing exposure row can be annotated')
    old_comment = rows[row_index][11]
    if old_comment == new_comment:
        return False
    rows[row_index][11] = new_comment
    # A backup is created before every edit. Never overwrite an earlier backup.
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = path.with_name(path.name + '.comments_' + stamp + '.bak')
    with backup.open('xb') as out:
        out.write(raw)
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as out:
            writer = csv.writer(out, lineterminator='\n')
            writer.writerows(rows)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temp, mode)
        # Refuse overwriting changes made by another process during preparation.
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise RuntimeError('Logbook changed while editing; no replacement performed.')
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return True
