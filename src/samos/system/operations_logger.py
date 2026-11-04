#!/usr/bin/env python3
"""Append-only operations event API for later SAMOS GUI integration (no hardware I/O)."""
import argparse
import json
import os
import uuid
import hashlib
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

ALLOWED = {'GUI_START','GUI_STOP','DMD_LOAD_REQUEST','DMD_LOAD_RESULT',
           'INSTRUMENT_COMMAND_REQUEST','INSTRUMENT_COMMAND_RESULT',
           'EXPOSURE_ASSOCIATION','OPERATOR_COMMENT','STATE_SNAPSHOT'}


def append_event(path, event, details=None, *, session_id, status=None):
    if event not in ALLOWED: raise ValueError(f'Unknown event type: {event}')
    if not session_id: raise ValueError('session_id is required')
    record={'schema':'samos.operations.v1','event_id':str(uuid.uuid4()),
            'utc':datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z'),
            'session_id':session_id,'event':event,'status':status,'details':details or {}}
    output=Path(path)
    output.parent.mkdir(parents=True,exist_ok=True)
    payload=(json.dumps(record,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')
    # Single os.write with O_APPEND; fsync for durable append. For multi-host writers,
    # use a dedicated serialized logging service rather than sharing this local file.
    fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
    try:
        written=os.write(fd,payload)
        if written!=len(payload): raise OSError('Short append write')
        os.fsync(fd)
    finally:
        os.close(fd)
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--log',required=True)
    p.add_argument('--event',choices=sorted(ALLOWED),required=True)
    p.add_argument('--session',required=True)
    p.add_argument('--status')
    p.add_argument('--details-json',default='{}')
    a=p.parse_args()
    details=json.loads(a.details_json)
    if not isinstance(details,dict):raise ValueError('details-json must be an object')
    print(json.dumps(append_event(a.log,a.event,details,session_id=a.session,status=a.status),indent=2))

if __name__=='__main__':main()


def archive_dmd_request(directory, array, *, load_id):
    """Persist exact post-flip 0/1 mirror array, atomically, before DMD transmission.

    Returns JSON-serializable provenance. Files are never overwritten.
    """
    x=np.asarray(array)
    if x.shape != (1080,2048) or not np.isin(x,[0,1]).all():
        raise ValueError("DMD array must be a binary 1080x2048 image")
    x=np.ascontiguousarray(x.astype(np.uint8,copy=False))
    digest=hashlib.sha256(x.tobytes(order="C")).hexdigest()
    root=Path(directory);root.mkdir(parents=True,exist_ok=True)
    dest=root / ("dmd_"+str(uuid.UUID(load_id))+".npy")
    # Exclusive creation prevents any replacement, including concurrent writers.
    with dest.open('xb') as fh:
        np.save(fh,x,allow_pickle=False)
        fh.flush();os.fsync(fh.fileno())
    return {"file":str(dest),"sha256_array_bytes":digest,"shape":[1080,2048],
            "dtype":"uint8","orientation":"DMD post-flip","load_id":load_id}
