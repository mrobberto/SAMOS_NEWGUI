"""Immutable SAMOS region archive (no DMD access)."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib, json, os, re

VERSION = re.compile(r'^\d{8}T\d{6}Z_v(\d+)\.(\d+)(?:_[0-9a-f]{8})?$')
LEGACY = re.compile(r'^v(\d+)(?:\.(\d+))?$')

def safe_field_slug(field):
    """Convert a human-readable field label to a safe archive identifier.

    Accept spaces in names, but never path separators, control characters,
    hidden dot-only names, or path traversal. Keep original in the manifest.
    """
    if not isinstance(field, str) or not field.strip():
        raise ValueError(f'Unsafe field name {field!r}: empty name')
    if '/' in field or "\\" in field or any(ord(c) < 32 or ord(c) == 127 for c in field):
        raise ValueError(f'Unsafe field name {field!r}: path separator or control character')
    slug=re.sub(r'\s+', '_', field.strip())
    if slug in ('.','..') or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}',slug):
        raise ValueError(f'Unsafe field name {field!r}: expected letters, numbers, spaces, dots, hyphens, or underscores (max 100 characters)')
    return slug

def archive_mask(root, field, products, metadata=None, utc_now=None):
    """Allocate never-overwritten version for a field and write immutable products.

    A fresh commit ALWAYS creates a fresh version even for identical data. Files are
    staged before destination reservation. A crash after reservation leaves a
    conspicuous INCOMPLETE directory, never an overwritten older mask.
    """
    if not products: raise ValueError('Empty mask products')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}',field):
        raise ValueError(f'Unsafe field name {field!r}')
    for name,data in products.items():
        if name in ('.','..') or Path(name).name!=name or name.startswith('.') or not isinstance(data,bytes):
            raise ValueError('Only flat, nonhidden filename -> bytes products supported')
    base=Path(root)/field
    base.mkdir(parents=True,exist_ok=True)
    now=utc_now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('UTC time must be timezone-aware')
    stamp=now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    # Reserving an exclusive destination is the concurrency safeguard.
    # An existing failed/incomplete reservation also consumes its version.
    for attempt in range(1000):
        existing=[int(m.group(1)) for p in base.iterdir() if p.is_dir() if (m:=VERSION.fullmatch(p.name) or LEGACY.fullmatch(p.name))]
        next_major=max(existing,default=0)+1
        version=f'v{next_major}.0'
        dirname=f'{stamp}_{version}'
        dest=base/dirname
        try: dest.mkdir(exist_ok=False)
        except FileExistsError: continue
        break
    else: raise RuntimeError('Unable to reserve new version')
    incomplete=dest/'INCOMPLETE'
    incomplete.write_text('Archive creation in progress; do not use for calibration.\n')
    try:
        hashes={}
        for name,data in sorted(products.items()):
            with (dest/name).open('xb') as f:
                f.write(data); f.flush(); os.fsync(f.fileno())
            hashes[name]=hashlib.sha256(data).hexdigest()
        manifest={'schema':'SAMOS_IMMUTABLE_MASK_V1', 'field':field,
                  'version':version,'archive_id':dirname,
                  'created_utc':now.astimezone(timezone.utc).isoformat(),
                  'status':'ARCHIVED_NOT_COMMANDED','files_sha256':hashes,
                  'metadata':metadata or {}}
        temp_manifest=dest/'manifest.json.tmp'
        with temp_manifest.open('x',encoding='utf-8') as f:
            json.dump(manifest,f,indent=2,sort_keys=True); f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp_manifest,dest/'manifest.json')
        incomplete.unlink()
        return {'status':'CREATED','path':str(dest),'version':version,'archive_id':dirname,
                'count_files':len(products)}
    except BaseException:
        # Deliberately retain evidence and the consumed version on failure.
        raise

def verify_archive(path):
    dest=Path(path)
    if (dest/'INCOMPLETE').exists(): raise ValueError('Incomplete mask archive')
    manifest=json.loads((dest/'manifest.json').read_text())
    for name,digest in manifest['files_sha256'].items():
        if hashlib.sha256((dest/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Checksum mismatch: {name}')
    return manifest
