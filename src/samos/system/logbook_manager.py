"""RC1 logbook file helpers. No SAMOS imports or hardware access."""
from pathlib import Path
from datetime import datetime, timezone
import csv

def make_new(pathdir, prefix, suffix):
    pathdir=Path(pathdir);pathdir.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    for i in range(100):
        path=pathdir / f'{prefix}_{stamp}_{i:02d}{suffix}'
        try:
            with path.open('x', encoding='utf-8',newline=''):
                pass
            return path
        except FileExistsError:continue
    raise FileExistsError('Unable to allocate unique logbook')

def science_header(path, db):
    now=datetime.now(timezone.utc)
    with Path(path).open('a',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['SAMOS SCIENCE LOGBOOK',now.isoformat()])
        for title,key in [('Telescope','POTN_Telescope'),('Program ID','POTN_Program'),('Proposal Title','POTN_Title'),('PI','POTN_PI'),('Observer','POTN_Observer'),('Telescope Operator','POTN_Telescope_Operator')]:
            w.writerow([title,db.get_value(key)])
        w.writerow(['Date','Local Time','Target','Filter','Repeats','Exposure Time','Filename','Mask Name','Grating','Sp. Exp.T','Sp. Filename','Comment'])

def append_science(path, values):
    if len(values)!=12:raise ValueError('Expected twelve columns')
    with Path(path).open('a',newline='',encoding='utf-8') as f:csv.writer(f).writerow(values)
