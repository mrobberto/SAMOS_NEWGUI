"""Offline-only multi-region SAMOS HTS mask builder.

DMD array indices are [x_mirror (1080), y_mirror (2048)], as used by
SAMOS DMDPage._make_dmd_array. The 1D code runs along the second axis.
No hardware communications occur in this module.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import numpy as np
from scipy.linalg import hadamard
from samos.hadamard.patterns import S_matrix


def build_sequence(centers, kind, order, slit_width, slit_length,
                   shape=(1080, 2048), slit_lengths=None,
                   scan_modes=None, fixed_slits=None):
    """Compose full-field binary masks for Hadamard/slitlet scans plus fixed slits.

    DMD array indices are [x_mirror, y_mirror]. The encoded/stepped axis is y.
    Scan modes: 'hadamard' (S/H row), 'slitlet_scan' (one slit_width strip
    at index row). Fixed slits are dicts with DMD center, length and width.
    Never send arrays to hardware; mask polarity must be validated before use.
    """
    kind = str(kind).upper()
    order, slit_width, slit_length = int(order), int(slit_width), int(slit_length)
    centers = np.asarray(centers, dtype=float)
    if centers.ndim != 2 or centers.shape[1] != 2 or len(centers) == 0:
        raise ValueError('At least one scan region is required')
    if not np.isfinite(centers).all():
        raise ValueError('Non-finite DMD centers')
    if slit_width < 1 or slit_length < 1 or order < 1:
        raise ValueError('Order and pixel dimensions must be positive')
    if kind == 'S':
        matrix = np.asarray(S_matrix(order), dtype=np.uint8)
    elif kind == 'H':
        matrix = hadamard(order).astype(np.int8)
    else:
        raise ValueError('Matrix type must be S or H')
    if matrix.shape != (order, order):
        raise ValueError('Invalid S/H code size')

    slit_lengths = ([slit_length] * len(centers) if slit_lengths is None
                    else [int(v) for v in slit_lengths])
    scan_modes = (['hadamard'] * len(centers) if scan_modes is None
                  else [str(v) for v in scan_modes])
    if len(slit_lengths) != len(centers) or len(scan_modes) != len(centers):
        raise ValueError('Each scan region needs a length and mode')
    if any(mode not in ('hadamard', 'slitlet_scan') for mode in scan_modes):
        raise ValueError('Unknown scan region type')
    if kind == 'H' and 'slitlet_scan' in scan_modes:
        raise ValueError('Slitlet-scan boxes currently require S-matrix mode. '
                         'H A/B subtraction would otherwise cancel the scan signal.')
    if min(slit_lengths) < 1 or max(slit_lengths) > shape[0] or order*slit_width > shape[1]:
        raise ValueError('One or more scan boxes exceed DMD dimensions')

    def bounds(x, y, length, width):
        x0 = int(round(float(x))) - length // 2
        y0 = int(round(float(y))) - width // 2
        b = (x0, y0, x0 + length, y0 + width)
        if not (0 <= b[0] < b[2] <= shape[0] and 0 <= b[1] < b[3] <= shape[1]):
            raise ValueError(f'Region outside active DMD: {b}')
        return b

    scan_bounds = [bounds(x,y,length,order*slit_width)
                   for (x,y),length in zip(centers,slit_lengths)]
    fixed_slits = [] if fixed_slits is None else list(fixed_slits)
    fixed_bounds = []
    normalized_fixed = []
    for i, slit in enumerate(fixed_slits, 1):
        xy = slit.get('dmd_center')
        if xy is None or len(xy) != 2 or not np.isfinite(xy).all():
            raise ValueError(f'Fixed slit {i} has invalid DMD center')
        length, width = int(slit['length']), int(slit['width'])
        if length < 1 or width < 1:
            raise ValueError('Fixed slit dimensions must be positive')
        b = bounds(xy[0], xy[1], length, width)
        fixed_bounds.append(b)
        normalized_fixed.append({'dmd_center':[float(xy[0]),float(xy[1])],
                                 'length':length,'width':width,'bounds':list(b)})
    all_bounds = [('scan',i+1,b) for i,b in enumerate(scan_bounds)] + [
        ('fixed',i+1,b) for i,b in enumerate(fixed_bounds)]
    for i,(atype,aid,a) in enumerate(all_bounds):
        for btype,bid,b in all_bounds[:i]:
            if max(a[0],b[0]) < min(a[2],b[2]) and max(a[1],b[1]) < min(a[3],b[3]):
                raise ValueError(f'{atype} {aid} overlaps {btype} {bid}')

    n_masks = order if kind == 'S' else 2*order
    if int(shape[0]) * int(shape[1]) * n_masks > 512*1024*1024:
        raise ValueError('Sequence exceeds 512 MiB; choose smaller matrix order')
    arrays, descriptions = [], []
    for row_index in range(order):
        for arm in (('S',) if kind == 'S' else ('A','B')):
            arr = np.zeros(shape,dtype=np.uint8)
            code = np.asarray(matrix[row_index], dtype=int)
            if kind == 'H':
                code = (code == (+1 if arm == 'A' else -1)).astype(np.uint8)
            expanded = np.repeat(code, slit_width)
            for mode,(x0,y0,x1,y1) in zip(scan_modes,scan_bounds):
                if mode == 'hadamard':
                    arr[x0:x1, y0:y1] = expanded[None,:]
                else:
                    ya = y0 + row_index * slit_width
                    arr[x0:x1, ya:ya+slit_width] = 1
            for x0,y0,x1,y1 in fixed_bounds:
                arr[x0:x1,y0:y1] = 1
            arrays.append(arr)
            descriptions.append({'row': row_index+1, 'arm': arm,
                                 'slitlet_scan_position':row_index+1})
    metadata = {
        'kind':kind, 'order':order, 'slit_width_mirrors':slit_width,
        'slit_length_mirrors':slit_length, 'slit_lengths_mirrors':slit_lengths,
        'array_shape':list(shape), 'dmd_centers':centers.tolist(),
        'dmd_bounds':[list(v) for v in scan_bounds],
        'scan_modes':scan_modes, 'fixed_slits':normalized_fixed,
        'steps':descriptions,
        'mask_value_convention':'0=background, 1=selected; hardware polarity unverified',
        'fixed_slit_policy':'Fixed slits present in every mask, including both H A/B arms',
        'matrix':matrix.astype(int).tolist(),
    }
    return arrays, metadata


def save_sequence(folder, arrays, metadata, ccd_centers=None, image_path=None,
                  calibration_sha256=None):
    """Save compact mask arrays and manifest in a NEW directory; never load hardware."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    manifest = dict(metadata)
    manifest.update({'created_utc':datetime.now(timezone.utc).isoformat(),
                     'ccd_centers_zero_based':ccd_centers,
                     'image_path':str(image_path) if image_path else None,
                     'calibration_sha256':calibration_sha256,
                     'status':'OFFLINE_ONLY_NOT_COMMANDED', 'masks':[]})
    for idx, (arr, step) in enumerate(zip(arrays, metadata['steps']), 1):
        name = f'hts_{idx:03d}_row{step["row"]:03d}_{step["arm"]}.npy'
        path = folder / name
        with path.open('xb') as f:
            np.save(f, arr, allow_pickle=False)
        manifest['masks'].append({'file':name, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), **step})
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return folder
