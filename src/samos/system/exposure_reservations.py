"""Crash-safe, per-night SISI exposure number reservations. No hardware imports."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re

RAW = re.compile(r'^SISI_\d{8}_\d{6}_(\d{4,})_[A-Za-z0-9-]+_(?:SCI|BIA|DAR|FLA|BUF|CAL|TST)\.fits$')
RES = re.compile(r'^(\d{4,})\.json$')
DIRECTORY = '.sisi_exposure_reservations'

def latest_number(fits_dir):
    folder = Path(fits_dir)
    high = 0
    for path in folder.glob('SISI_*.fits'):
        match = RAW.fullmatch(path.name)
        if match:
            high = max(high, int(match.group(1)))
    for path in (folder / DIRECTORY).glob('*.json'):
        match = RES.fullmatch(path.name)
        if match:
            high = max(high, int(match.group(1)))
    return high

def next_number(fits_dir):
    return latest_number(fits_dir) + 1

def reserve(fits_dir, number, *, object_name='', exposure_type='', sequence_index=None):
    """Reserve number before command dispatch, never overwrite; gaps are intentional."""
    folder = Path(fits_dir)
    number = int(number)
    if number < 1:
        raise ValueError('Invalid exposure number')
    # Reject already-used numbers even if caller's GUI counter is stale.
    if number <= latest_number(folder):
        raise FileExistsError(f'Exposure {number} already used or reserved; refresh Next Exposure Nr.')
    reservation_dir = folder / DIRECTORY
    reservation_dir.mkdir(parents=True, exist_ok=True)
    path = reservation_dir / f'{number:04d}.json'
    payload = {'schema': 1, 'number': number, 'reserved_utc': datetime.now(timezone.utc).isoformat(),
               'object_name': str(object_name), 'exposure_type': str(exposure_type),
               'sequence_index': sequence_index, 'status': 'RESERVED'}
    # Exclusive create is important even when another GUI instance runs.
    with path.open('x', encoding='utf-8') as fp:
        json.dump(payload, fp, sort_keys=True)
        fp.write('\n')
        fp.flush()
        os.fsync(fp.fileno())
    return path
