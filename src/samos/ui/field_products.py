"""Publish immutable mask archive products into a field's operational folders.

No telescope or GUI dependencies. Archive remains authoritative; publication is
exclusive and may be retried after a partial failure.
"""
from pathlib import Path
import hashlib
import json
import re


def field_root(source):
    p = Path(source).expanduser().resolve()
    if not p.is_file() or not re.fullmatch(r'.+_RADEC=[0-9.]+[+-][0-9.]+\.reg', p.name, re.I):
        raise ValueError('A loaded, existing RADEC=... .reg source file is required')
    return p.parent.parent if p.parent.name.casefold() in ('radec', 'regionfiles') else p.parent


def publish(archive_dir, source):
    """Publish archive files in RADEC/ and PIXELS/ without overwriting anything.

    If a retry finds an identical complete destination it is accepted. A differing
    existing file is a hard error. Records are NOT modified inside the archive.
    """
    root = field_root(source)
    archive = Path(archive_dir).resolve()
    if (archive / 'INCOMPLETE').exists():
        raise ValueError('Archive is marked INCOMPLETE')
    manifest = json.loads((archive / 'manifest.json').read_text(encoding='utf8'))
    version = manifest['version']
    if not re.fullmatch(r'v\d+\.\d+', version):
        raise ValueError('Invalid mask version')
    products = manifest['files_sha256']
    output = []
    for name, expected in products.items():
        if name.endswith('.reg') and '_PIXEL_' in name:
            folder = root / 'PIXELS'
            basename = name.replace('_PIXEL_', f'_{version}_PIXEL_', 1)
        elif name.endswith('.reg') and '_RADEC=' in name:
            folder = root / 'RADEC'
            basename = name.replace('_RADEC=', f'_{version}_RADEC=', 1)
        else:
            continue
        data = (archive / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Archive checksum mismatch: {name}')
        output.append((folder / basename, data))
    if len(output) != 4:
        raise ValueError('Expected exactly FULL, EVEN, ODD and RADEC region files')
    # Preflight existing files before writing anything.
    for dest, data in output:
        if dest.exists() and dest.read_bytes() != data:
            raise FileExistsError(f'Existing operational file differs: {dest}')
    created = []
    for dest, data in output:
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with dest.open('xb') as f:
                f.write(data)
            created.append(str(dest))
        except FileExistsError:
            if dest.read_bytes() != data:
                raise FileExistsError(f'Concurrent conflicting file: {dest}')
    return {'field_root': str(root), 'files': [str(p) for p,_ in output],
            'created': created, 'version': version}
