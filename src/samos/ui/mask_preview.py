"""Offline-only science-region preview archive. Does not create DMD commands."""
import csv
import hashlib
import json
import re
from pathlib import Path
from regions import Regions


def save_preview(pixel_regions, image_wcs, original_filename, archive_root):
    if image_wcs is None:
        raise ValueError('No valid image WCS; refusing science sky export')
    if not pixel_regions:
        raise ValueError('No apertures available')
    match = re.fullmatch(r'(.+?)_RADEC=([0-9.]+)([+-][0-9.]+)\.reg', Path(original_filename).name, flags=re.I)
    if not match:
        raise ValueError('A science reference filename TARGET_RADEC=RA+DEC.reg is required')
    field, ra0, dec0 = match.groups()
    # Human-facing field names legitimately contain spaces (e.g. RMC 136-T00).
    # Keep the original in provenance; use a restricted identifier for folders/files.
    from .archive_core import safe_field_slug
    field_slug = safe_field_slug(field)
    # Canvas order is deliberately ignored; sort by current sky RA at PREVIEW time.
    items=[]
    for reg in pixel_regions:
        sky=reg.to_sky(image_wcs)
        ra=float(sky.center.ra.deg); dec=float(sky.center.dec.deg)
        items.append((ra,dec,float(reg.center.x),float(reg.center.y),reg,sky))
    items.sort(key=lambda t:t[:4])
    for a,b in zip(items,items[1:]):
        if a[:4]==b[:4]:
            raise ValueError('Indistinguishable duplicate apertures')
    rows=[]
    for i,(ra,dec,x,y,pix,sky) in enumerate(items):
        rows.append({'SLITID':f'SLIT{i:03d}','TARGETID':f'LOCAL{i:03d}',
                     'TRACESET':'EVEN' if i%2==0 else 'ODD', 'SET_RANK':i//2,
                     'RA_DEG':format(ra,'.15g'),'DEC_DEG':format(dec,'.15g'),
                     'X_GINGA_0':format(x,'.15g'),'Y_GINGA_0':format(y,'.15g')})
    import tempfile
    from .archive_core import archive_mask
    with tempfile.TemporaryDirectory(prefix='samos-mask-build-') as tmp:
        temp=Path(tmp)
        idx={'FULL':list(range(len(items))), 'EVEN':list(range(0,len(items),2)),
             'ODD':list(range(1,len(items),2))}
        files={}
        for label,selected in idx.items():
            name=f'{field_slug}_PIXEL_{label}.reg'
            if selected:
                path=temp/name
                Regions([items[i][4] for i in selected]).write(path,format='ds9',overwrite=False)
                files[name]=path.read_bytes()
            else:
                files[name]=b'# Region file format: DS9 version 4.1\nimage\n'
        skyname=f'{field_slug}_RADEC={ra0}{dec0}.reg'
        skypath=temp/skyname
        Regions([v[5] for v in items]).write(skypath,format='ds9',overwrite=False)
        files[skyname]=skypath.read_bytes()
        table=temp/'slit_manifest.csv'
        with table.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        files['slit_manifest.csv']=table.read_bytes()
        signature=mask_signature([v[4] for v in items], image_wcs)
        result=archive_mask(archive_root,field_slug,files,metadata={
            'field_display_name':field,
            'field_folder_name':field_slug,
            'slit_count':len(rows), 'even_count':len(idx['EVEN']),
            'odd_count':len(idx['ODD']), 'signature':signature,
            'source_region_file':Path(original_filename).name,
            'comment':'Snapshot of current edited science regions; no DMD command issued'})
        return {**result,'count':len(rows),'signature':signature}


def mask_signature(pixel_regions, image_wcs):
    """Stable geometry fingerprint independent of Ginga object order/tags.

    It covers positions and rectangle dimensions in native data pixels, as well
    as the WCS sky positions used to determine RA order.
    """
    import math
    entries=[]
    for reg in pixel_regions:
        if not hasattr(reg, 'width') or not hasattr(reg, 'height'):
            raise ValueError('Only rectangular science slits supported')
        sky=reg.to_sky(image_wcs)
        vals=(float(sky.center.ra.deg),float(sky.center.dec.deg),
              float(reg.center.x),float(reg.center.y),
              float(reg.width),float(reg.height),float(getattr(reg,'angle',0).to_value('deg') if hasattr(getattr(reg,'angle',0),'to_value') else 0))
        if not all(math.isfinite(v) for v in vals):
            raise ValueError('Nonfinite region geometry')
        entries.append([round(v,9) for v in vals])
    entries.sort()
    return hashlib.sha256(json.dumps(entries,separators=(',',':')).encode()).hexdigest()
