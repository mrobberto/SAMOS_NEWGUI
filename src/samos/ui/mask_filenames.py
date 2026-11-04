"""Pure filename helpers; independent of SAMOS GUI and hardware."""
from pathlib import Path
import re
PATTERN = re.compile(r'^(?P<stem>.+)_RADEC=(?P<ra>\d+(?:\.\d+)?)(?P<dec>[+-]\d+(?:\.\d+)?)\.reg$', re.I)
VERSION = re.compile(r'^(?P<target>.+)_v(?P<version>\d+)$', re.I)

def parse_science_region_filename(filename):
    m = PATTERN.fullmatch(Path(filename).name)
    if m is None: raise ValueError('Unrecognized SAMOS RADEC region filename')
    v = VERSION.fullmatch(m['stem'])
    return dict(mask_name=m['stem'], target_name=v['target'] if v else m['stem'],
                version=int(v['version']) if v else None,
                ra_deg=float(m['ra']), dec_deg=float(m['dec']),
                coordinate_token=m['ra']+m['dec'])

def pixel_region_names(filename):
    p = parse_science_region_filename(filename)
    stem, coords=p['mask_name'],p['coordinate_token']
    return {kind:f'{stem}_PIXEL{suffix}={coords}.reg' for kind,suffix in
            [('full',''),('even','_EVEN'),('odd','_ODD')]}
