"""Read-only DMD mask geometry audit based on the LIVE GUI slit objects.
Does not access DMD controller. Supports orthonormal rectangles and diagnostic rotated-aperture rasterization.
"""
import hashlib, json
from pathlib import Path
import numpy as np

def _sha(a):
    a=np.asarray(a,dtype=np.uint8,order='C')
    return hashlib.sha256(str(tuple(a.shape)).encode()+b'\0'+a.tobytes()).hexdigest()

def validate_gui_masks(page, objects, converter, *, root):
    orthonormal = bool(int(page.force_orthonormal.get()))
    if not objects: raise ValueError('No slit objects')
    # Ginga's Box uses kind='box'; some imported regions use kind='rectangle'.
    # Both expose get_llur() and define supported axis-aligned slit geometry.
    allowed = {'box', 'rectangle'}
    unsupported = [(str(getattr(ob, 'tag', '<untagged>')), str(getattr(ob, 'kind', None)))
                   for ob in objects if getattr(ob, 'kind', None) not in allowed]
    if unsupported:
        raise ValueError(
            'Canvas includes non-slit objects (tag, kind): ' + repr(unsupported[:12]) +
            '. Use Slits Only / clear auxiliary markers, then rerun; no DMD command was sent.'
        )
    # Stored rotations are meaningful; never modify live Ginga objects.
    wcs=getattr(page.PAR,'wcs',None)
    if wcs is None: raise ValueError('A valid image WCS is required for RA ordering')
    # These are the exact active Ginga objects, not the original DS9 proposal.
    rows=[]
    for ob in objects:
        x0,y0,x1,y1=[float(q) for q in ob.get_llur()]
        if not all(np.isfinite(q) for q in (x0,y0,x1,y1)):raise ValueError('Nonfinite slit extent')
        if x1<=x0 or y1<=y0: raise ValueError('Zero-size rectangle')
        ra,dec=wcs.all_pix2world([float(ob.x)],[float(ob.y)],0)
        rows.append((float(ra[0]),float(dec[0]),float(ob.x),float(ob.y),ob))
    rows.sort(key=lambda q:q[:4])
    masks=[np.ones((1080,2048),dtype=np.uint8) for _ in range(3)]
    occupied=np.full((1080,2048),-1,dtype=np.int32)
    overlaps=[]
    report=[]
    for idx,(ra,dec,x,y,ob) in enumerate(rows):
        rotation=float(getattr(ob,'rot_deg',0.0))
        if not np.isfinite(rotation):
            raise ValueError(f'SLIT{idx:03d}: nonfinite rotation')
        # Preserve the saved center and dimensions regardless of effective command mode.
        record={'SLITID':f'SLIT{idx:03d}', 'TRACESET':'EVEN' if idx%2==0 else 'ODD',
                'ra_deg':ra,'dec_deg':dec,'x_ginga':x,'y_ginga':y,
                'display_rotation_deg':rotation, 'canvas_tag':str(getattr(ob,'tag','')),
                'effective_rotation_deg':0.0 if orthonormal else rotation}
        slit_pixels=np.zeros((1080,2048),dtype=bool)
        if orthonormal:
            # get_llur() for a rotated Ginga box is a bounding envelope on some
            # Ginga versions. Compute unrotated edges from xradius/yradius instead.
            if not hasattr(ob,'xradius') or not hasattr(ob,'yradius'):
                if abs(rotation)>1e-10:
                    raise ValueError(f'SLIT{idx:03d}: no box radii for safe orthonormal geometry')
                ccd_x0,ccd_y0,ccd_x1,ccd_y1=map(float,ob.get_llur())
            else:
                rx,ry=float(ob.xradius),float(ob.yradius)
                if rx<=0 or ry<=0 or not np.isfinite(rx+ry):
                    raise ValueError(f'SLIT{idx:03d}: invalid box radii')
                ccd_x0,ccd_y0,ccd_x1,ccd_y1=x-rx,y-ry,x+rx,y+ry
            dmd_y1,dmd_x1=converter(ccd_x0,ccd_y0,page.PAR.dmd_wcs)
            dmd_y2,dmd_x2=converter(ccd_x1,ccd_y1,page.PAR.dmd_wcs)
            y1,x1=int(np.floor(dmd_y1)),int(np.floor(dmd_x1))
            y2,x2=int(np.ceil(dmd_y2)),int(np.ceil(dmd_x2))
            if not (0<=y1<=y2<1080 and 0<=x1<=x2<2048):
                raise ValueError(f'SLIT{idx:03d}: invalid/out-of-bounds DMD rectangle {(y1,x1,y2,x2)}')
            slit_pixels[y1:y2+1,x1:x2+1]=True
            record.update(dmd_row0=y1,dmd_row1=y2,dmd_col0=x1,dmd_col1=x2)
        else:
            # Diagnostic rasterization of the real rotated Ginga footprint.
            # This is NOT asserted equivalent to the production cutout_shape algorithm,
            # which applies its own rounding and edge painting.
            if not hasattr(ob,'xradius') or not hasattr(ob,'yradius'):
                raise ValueError(f'SLIT{idx:03d}: rotated audit requires Ginga box radii')
            rx,ry=float(ob.xradius),float(ob.yradius)
            if rx<=0 or ry<=0 or not np.isfinite(rx+ry):
                raise ValueError(f'SLIT{idx:03d}: invalid box radii')
            ang=np.deg2rad(rotation)
            c,sn=np.cos(ang),np.sin(ang)
            halfx=abs(rx*c)+abs(ry*sn)
            halfy=abs(rx*sn)+abs(ry*c)
            xs=np.arange(int(np.floor(x-halfx)),int(np.ceil(x+halfx))+1)
            ys=np.arange(int(np.floor(y-halfy)),int(np.ceil(y+halfy))+1)
            xx,yy=np.meshgrid(xs,ys,indexing='xy')
            dx=xx-x;dy=yy-y
            u= c*dx+sn*dy;v=-sn*dx+c*dy
            inside=(abs(u)<=rx)&(abs(v)<=ry)
            if not inside.any():
                raise ValueError(f'SLIT{idx:03d}: empty rasterized footprint')
            yp,xp=converter(xx[inside],yy[inside],page.PAR.dmd_wcs)
            drow=np.rint(yp).astype(int);dcol=np.rint(xp).astype(int)
            if np.any((drow<0)|(drow>=1080)|(dcol<0)|(dcol>=2048)):
                raise ValueError(f'SLIT{idx:03d}: projected aperture crosses DMD boundary')
            slit_pixels[drow,dcol]=True
            record.update(dmd_row0=int(drow.min()),dmd_row1=int(drow.max()),
                          dmd_col0=int(dcol.min()),dmd_col1=int(dcol.max()))
        prior=occupied[slit_pixels]
        for other_idx in sorted(set(int(n) for n in prior if n>=0)):
            shared=slit_pixels & (occupied==other_idx)
            coords=np.argwhere(shared)
            overlaps.append({'slit_a':f'SLIT{other_idx:03d}', 'slit_b':f'SLIT{idx:03d}',
                             'shared_mirrors':int(len(coords)),
                             'shared_dmd_row_col':coords[:50].tolist(),
                             'truncated':bool(len(coords)>50)})
        occupied[slit_pixels & (occupied<0)]=idx
        masks[0][slit_pixels]=0
        masks[1+idx%2][slit_pixels]=0
        record['selected_mirrors']=int(slit_pixels.sum())
        report.append(record)
    full,even,odd=masks
    union_ok=bool(np.array_equal(full==0,(even==0)|(odd==0)))
    partition_overlap_count=int(np.sum((even==0)&(odd==0)))
    if not union_ok: raise AssertionError('DMD union invariant failure')
    # Parity intersection can occur for competing apertures: report rather than fail
    # before the diagnostic artifacts can be preserved.

    # Never call collect_slit_shape() for rotated input: in production it can
    # change obj.rot_deg, and the generic rasterizer is a different algorithm.
    # We report geometry invariants without claiming a production-array match.
    comparison='NOT_RUN_NONMUTATING'
    gui_objects=page.canvas.get_objects()
    if set(id(o) for o in gui_objects)!=set(id(o) for o in objects):
        raise ValueError('Canvas contains extra objects; audit requires exactly the active slit selection')
    dest=Path(root).expanduser().resolve()
    dest.mkdir(parents=True,exist_ok=True)
    import datetime,uuid
    dirname='R136_DMD_DRYRUN_'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8]
    target=dest/dirname
    target.mkdir(exist_ok=False)
    try:
        for name,a in zip(('FULL','EVEN','ODD'),masks):
            np.save(target/(name+'.npy'),a,allow_pickle=False)
        with (target/'slits.json').open('x') as f: json.dump(report,f,indent=2)
        with (target/'overlaps.json').open('x') as f: json.dump(overlaps,f,indent=2)
        summary={'status':'WARNING_APERTURE_OVERLAP_NOT_COMMANDED' if overlaps else 'OFFLINE_NOT_COMMANDED',
                 'overlap_pairs':overlaps, 'overlap_pair_count':len(overlaps),
                 'even_odd_shared_mirrors':partition_overlap_count,
                 'partition_union_ok':union_ok, 'slits':len(report),
                 'even_slits':sum(r['TRACESET']=='EVEN' for r in report),
                 'odd_slits':sum(r['TRACESET']=='ODD' for r in report),
                 'full_selected_mirrors':int(np.sum(full==0)),
                 'even_selected_mirrors':int(np.sum(even==0)),
                 'odd_selected_mirrors':int(np.sum(odd==0)),
                 'gui_full_matches':None,'production_comparison':comparison,
                 'force_orthonormal':orthonormal,'array_orientation':'PRE_DRIVER_FLIP',
                 'array_sha256':{name:_sha(a) for name,a in zip(('FULL','EVEN','ODD'),masks)},
                 'caveat':'Independent diagnostic rasterization; production FULL bitmap match NOT tested. Overlap does not establish a physical collision; review per-slit footprints.'}
        with (target/'summary.json').open('x') as f:json.dump(summary,f,indent=2)
        return str(target),summary
    except BaseException:
        import shutil;shutil.rmtree(target);raise
