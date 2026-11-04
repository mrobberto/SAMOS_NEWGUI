"""Pure/file-only SEND identity preparation. No controller or GUI dependencies."""
from pathlib import Path
import re, json, hashlib, os, tempfile
from datetime import datetime, timezone

VERSION = re.compile(r'_v(\d+)\.\d+(?=_PIXEL_)', re.I)
ROLE = re.compile(r'_PIXEL_(FULL|EVEN|ODD)(?:=|\.|$)', re.I)

def role_of(filename):
    m = ROLE.search(Path(filename).name)
    return m.group(1).upper() if m else 'FULL'

def versioned_pixel_name(source, root):
    src = Path(source)
    role=role_of(src.name)
    base=re.sub(r'_PIXEL_(?:FULL|EVEN|ODD)(?:=.*)?\.reg$', '', src.name, flags=re.I)
    base=re.sub(r'_v\d+\.\d+$', '', base, flags=re.I)
    if base == src.name or not base:
        raise ValueError('Not a recognized _PIXEL_FULL/EVEN/ODD .reg filename')
    indices=[]
    for directory in ('PIXELS','RADEC','MANIFESTS'):
        d=Path(root)/directory
        if not d.is_dir(): continue
        for p in d.iterdir():
            if p.name.startswith(base+'_v'):
                m=re.search(r'_v(\d+)\.\d+',p.name)
                if m: indices.append(int(m.group(1)))
    m=re.search(r'_v(\d+)\.\d+',src.name)
    if m: indices.append(int(m.group(1)))
    return f'{base}_v{max(indices,default=0)+1}.0_PIXEL_{role}.reg'

def save_modified_pixel(regions, source):
    """Immutable PIXEL version from current rectangles; no RADEC/WCS needed."""
    from regions import Regions
    src=Path(source).expanduser().resolve(strict=True)
    root=src.parent.parent if src.parent.name.casefold()=='pixels' else src.parent
    target=root/'PIXELS'; manifests=root/'MANIFESTS'
    target.mkdir(parents=True,exist_ok=True); manifests.mkdir(parents=True,exist_ok=True)
    if not regions: raise ValueError('No slit rectangles')
    with tempfile.TemporaryDirectory(prefix='samos-pixel-send-') as t:
        p=Path(t)/'mask.reg'; Regions(regions).write(str(p),format='ds9'); payload=p.read_bytes()
    # Lock guards against concurrent version allocation.
    import hashlib as _h
    lock=manifests/('.'+_h.sha256(str(src).encode()).hexdigest()[:16]+'.send.lock')
    lock.mkdir()   # fail closed on concurrent operation
    created=[]
    try:
        name=versioned_pixel_name(src,root)
        dest=target/name
        with dest.open('xb') as f:
            f.write(payload); f.flush(); os.fsync(f.fileno())
        created.append(dest)
        meta={'schema':'SAMOS_PIXEL_SEND_V1','source_region_file':src.name,
              'source_region_path':str(src),'pixel_region':f'../PIXELS/{name}',
              'sha256':hashlib.sha256(payload).hexdigest(),
              'created_utc':datetime.now(timezone.utc).isoformat(),
              'role':role_of(name),'slit_count':len(regions),
              'status':'PREPARED_NOT_COMMANDED'}
        manifest=manifests/(dest.stem+'.json')
        with manifest.open('xb') as f:
            f.write((json.dumps(meta,indent=2,sort_keys=True)+'\n').encode())
            f.flush(); os.fsync(f.fileno())
        created.append(manifest)
        return {'path':str(dest),'manifest':str(manifest),'created':True,'source_kind':'PIXEL'}
    except BaseException:
        for p in reversed(created):
            try:p.unlink()
            except OSError:pass
        raise
    finally:
        lock.rmdir()

def science_full_from_manifest(manifest_file):
    p=Path(manifest_file)
    data=json.loads(p.read_text())
    matches=[v for v in data['files'].values() if '_PIXEL_FULL' in v.upper() and v.lower().endswith('.reg')]
    if len(matches)!=1: raise ValueError('Cannot identify unique PIXEL_FULL product')
    result=(p.parent.parent/matches[0]).resolve(strict=True)
    if not result.is_relative_to(p.parent.parent.resolve()): raise ValueError('Unsafe mask path')
    return str(result)
