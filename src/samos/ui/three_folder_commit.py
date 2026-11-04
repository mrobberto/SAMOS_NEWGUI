"""SAMOS three-folder mask commit, no hardware operations.

Build products with existing tested mask_preview.save_preview in a temporary area;
commit exclusively into RADEC, PIXELS, MANIFESTS. JSON manifest is published
last so an interrupted transaction is never advertised as complete.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from datetime import datetime, timezone

_SOURCE = re.compile(r'^(.+?)_RADEC=([0-9.]+)([+-][0-9.]+)\.reg$', re.I)
_VERSION = re.compile(r'_v(\d+)\.\d+(?:_PIXEL_|_RADEC=|\.)')

def _safe_root(source):
    src = Path(source).expanduser().resolve(strict=True)
    if not src.is_file() or not _SOURCE.fullmatch(src.name):
        raise ValueError('Load an existing TARGET_RADEC=RA+DEC.reg before committing')
    if src.parent.name.casefold() in ('radec', 'regionfiles'):
        root = src.parent.parent
    else:
        root = src.parent
    return src, root

def _version_used(root, slug):
    nums=[]
    for d in ('RADEC','PIXELS','MANIFESTS'):
        folder=root/d
        if not folder.is_dir(): continue
        for p in folder.iterdir():
            if p.name.startswith(slug+'_v'):
                m=_VERSION.search(p.name)
                if m: nums.append(int(m.group(1)))
    # Account for previous MASK_ARCHIVE commits; never reuse old version numbers.
    for d in ('MASK_ARCHIVE','SAMOS_MASK_ARCHIVE'):
        folder=root/d/slug
        if folder.is_dir():
            for p in folder.iterdir():
                m=re.search(r'_v(\d+)\.\d+',p.name)
                if m: nums.append(int(m.group(1)))
    return max(nums,default=0)

def _write_exclusive(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

def save_three_folders(pixel_regions, image_wcs, original_filename):
    """Commit a mask and return save_preview-style result.

    Requires write access to source field. Manifest is final commit marker.
    On Python-visible exceptions, deletes only files created by this call;
    a process crash can leave unreferenced .reg products to be reviewed.
    """
    from .mask_preview import save_preview
    from .archive_core import safe_field_slug
    src,root=_safe_root(original_filename)
    field=safe_field_slug(_SOURCE.fullmatch(src.name).group(1))
    # A private, short-lived build directory does not become part of field tree.
    with tempfile.TemporaryDirectory(prefix='samos-mask-staging-') as tmp:
        built=save_preview(pixel_regions,image_wcs,str(src),Path(tmp))
        source_dir=Path(built['path'])
        old=json.loads((source_dir/'manifest.json').read_text(encoding='utf8'))
        source_files=old['files_sha256']
        lock=root/'MANIFESTS'/f'.{field}.commit.lock'
        lock.parent.mkdir(parents=True,exist_ok=True)
        try:
            lock.mkdir()  # exclusive reservation, no concurrent commit for this target
        except FileExistsError:
            raise RuntimeError(f'Mask commit already in progress: {lock}')
        created=[]
        try:
            version=f'v{_version_used(root,field)+1}.0'
            now=datetime.now(timezone.utc)
            relative={}
            hashes={}
            for basename in sorted(source_files):
                if basename.endswith('.reg') and '_PIXEL_' in basename:
                    newname=basename.replace('_PIXEL_',f'_{version}_PIXEL_',1)
                    rel=Path('PIXELS')/newname
                elif basename.endswith('.reg') and '_RADEC=' in basename:
                    newname=basename.replace('_RADEC=',f'_{version}_RADEC=',1)
                    rel=Path('RADEC')/newname
                elif basename=='slit_manifest.csv':
                    rel=Path('MANIFESTS')/f'{field}_{version}.csv'
                else:
                    raise ValueError(f'Unexpected archive product: {basename}')
                data=(source_dir/basename).read_bytes()
                if hashlib.sha256(data).hexdigest()!=source_files[basename]:
                    raise ValueError(f'Staged archive checksum differs: {basename}')
                _write_exclusive(root/rel,data)
                created.append(root/rel)
                relative[basename]=rel.as_posix()
                hashes[rel.as_posix()]=hashlib.sha256(data).hexdigest()
            if len(relative)!=5:
                raise ValueError(f'Expected five products, got {len(relative)}')
            meta={
                'schema':'SAMOS_THREE_FOLDER_MASK_V1',
                'field':field,
                'version':version,
                'created_utc':now.isoformat(),
                'status':'ARCHIVED_NOT_COMMANDED',
                'source_region_file':src.name,
                'files':relative,
                'files_sha256':hashes,
                'metadata':old.get('metadata',{}),
            }
            manifest_path=root/'MANIFESTS'/f'{field}_{version}.json'
            _write_exclusive(manifest_path,(json.dumps(meta,indent=2,sort_keys=True)+'\n').encode('utf8'))
            created.append(manifest_path)
            return {'status':'CREATED','path':str(manifest_path),'version':version,
                    'count':built['count'],'signature':built['signature'],
                    'field_root':str(root)}
        except BaseException:
            for p in reversed(created):
                try: p.unlink()
                except OSError: pass
            raise
        finally:
            try: lock.rmdir()
            except OSError: pass

def verify_manifest(manifest_file):
    p=Path(manifest_file)
    data=json.loads(p.read_text(encoding='utf8'))
    root=p.parent.parent
    for rel,digest in data['files_sha256'].items():
        resolved=(root/rel).resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError('Manifest file escapes field directory')
        if hashlib.sha256(resolved.read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Checksum mismatch: {rel}')
    return data
