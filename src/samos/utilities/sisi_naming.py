"""Pure SISI filename functions. No SAMOS imports or hardware operations."""
from datetime import datetime, timezone
from pathlib import Path
import re

SUFFIX = {'Science':'SCI','Bias':'BIA','Dark':'DAR','Flat':'FLA','Buffer':'BUF','Calibration':'CAL','Test':'TST'}

def safe_object_name(value):
    name = re.sub(r'[^A-Za-z0-9-]+', '-', str(value).strip()).strip('-')
    return name or 'UNNAMED'

def exposure_basename(utc_start, exposure_number, object_name, exposure_type):
    if utc_start.tzinfo is None or utc_start.utcoffset() is None:
        raise ValueError('UTC timestamp must be timezone aware')
    if not isinstance(exposure_number, int) or exposure_number < 1:
        raise ValueError('Exposure number must be a positive integer')
    try:
        suffix = SUFFIX[exposure_type]
    except KeyError:
        raise ValueError(f'Unsupported exposure type: {exposure_type}') from None
    stamp = utc_start.astimezone(timezone.utc).strftime('%Y%m%d_%H%M%S')
    return f'SISI_{stamp}_{exposure_number:04d}_{safe_object_name(object_name)}_{suffix}.fits'

_FILENAME = re.compile(r'^SISI_(\d{8})_(\d{6})_(\d{4,})_([A-Za-z0-9-]+)_(SCI|BIA|DAR|FLA|BUF|CAL|TST)\.fits$')

def next_exposure_number(folder, minimum=1):
    """Inspect only recognized SISI raw frame names, not coadds or legacy files."""
    high = minimum - 1
    for path in Path(folder).glob('SISI_*.fits'):
        match = _FILENAME.fullmatch(path.name)
        if match:
            high = max(high, int(match.group(3)))
    return high + 1


def ensure_new_name(folder, filename):
    """Fail if destination already exists; caller must use exclusive file creation."""
    path = Path(folder) / filename
    if path.exists():
        raise FileExistsError(str(path))
    return path
