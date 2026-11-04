"""Read-only SAMOS DMD operations history; no hardware imports."""
import json
from pathlib import Path

def read_dmd_history(path):
    path=Path(path)
    if not path.is_file():
        return []
    requests=[]; by_id={}; pending={}
    with path.open('r',encoding='utf-8') as handle:
        for lineno,line in enumerate(handle,1):
            if not line.strip(): continue
            try: event=json.loads(line)
            except (ValueError,UnicodeError): continue  # tolerate incomplete final append
            if not isinstance(event,dict): continue
            kind=event.get('event'); detail=event.get('details') or {}
            if not isinstance(detail,dict): continue
            load_id=detail.get('load_id')
            if not isinstance(load_id,str) or not load_id: continue
            if kind=='DMD_LOAD_REQUEST':
                row={'utc':event.get('utc',''), 'mask':detail.get('mask_name') or Path(detail.get('parent_mask') or '').name,
                     'source':detail.get('mask_source_kind',''), 'modified':detail.get('mask_modified'),
                     'created':detail.get('mask_version_created'), 'status':event.get('status','REQUESTED'),
                     'load_id':load_id,'request':event,'result':None}
                requests.append(row);by_id[load_id]=row
                if load_id in pending: row['result']=pending.pop(load_id);row['status']=row['result'].get('status','')
            elif kind=='DMD_LOAD_RESULT':
                if load_id in by_id:
                    by_id[load_id]['result']=event
                    by_id[load_id]['status']=event.get('status','')
                else: pending[load_id]=event
    return list(reversed(requests))
