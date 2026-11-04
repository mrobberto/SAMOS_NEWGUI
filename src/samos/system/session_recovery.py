"""Persist only active observing-log paths; no instrument commands.

The manifest lives alongside output, outside volatile process state. An absent or
invalid logbook is never silently replaced. This module makes no GUI calls.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

NAME = 'observing_session.json'


def manifest_path(output_dir):
    return Path(output_dir).expanduser().resolve() / NAME


def _within(path, base):
    try:
        Path(path).resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def save(output_dir, night, science=None, engineering=None):
    """Atomically store validated active log paths without creating missing logs."""
    base = Path(output_dir).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    dest = manifest_path(base)
    record = {'schema': 1, 'night': str(night),
              'saved_utc': datetime.now(timezone.utc).isoformat(),
              'science_log': None, 'engineering_log': None}
    # A user may explicitly resume a logbook stored outside the output tree.
    for kind, candidate, suffix in [('science_log', science, '.csv'),
                                     ('engineering_log', engineering, ('.log', '.txt'))]:
        if not candidate:
            continue
        p = Path(candidate).expanduser().resolve()
        if p.is_file() and p.suffix.lower() in ((suffix,) if isinstance(suffix, str) else suffix):
            record[kind] = str(p)
    fd, temp = tempfile.mkstemp(prefix='.observing_session_', suffix='.tmp', dir=base)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, dest)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return dest


def load(output_dir, night):
    """Return existing logs for same night; tolerate corruption/stale paths."""
    base = Path(output_dir).expanduser().resolve()
    try:
        doc = json.loads(manifest_path(base).read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(doc, dict) or doc.get('schema') != 1 or doc.get('night') != str(night):
        return {}
    found = {}
    for key, suffixes in (('science_log', ('.csv',)), ('engineering_log', ('.log', '.txt'))):
        value = doc.get(key)
        if isinstance(value, str) and value:
            p = Path(value).expanduser().resolve()
            if p.is_file() and p.suffix.lower() in suffixes:
                found[key] = p
    return found
