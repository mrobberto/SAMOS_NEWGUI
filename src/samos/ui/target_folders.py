"""Target-aware folder choices for SAMOS file dialogs. No GUI/hardware imports."""
from pathlib import Path

FOLDER_NAMES = {
    'radec': ('RADEC', 'RegionFiles'),
    'pixels': ('PIXELS', 'PIXEL'),
    'gaia': ('GAIA', 'GAIA files', 'Gaia', 'Gaia files', 'gaia'),
}

def field_root(loaded_reg_file):
    """Resolve the field folder from a loaded celestial file; never create dirs."""
    if not loaded_reg_file:
        return None
    p = Path(loaded_reg_file).expanduser()
    if not p.is_file() or 'RADEC=' not in p.name.upper():
        return None
    parent = p.resolve().parent
    return parent.parent if parent.name.casefold() in ('radec', 'regionfiles') else parent

def initial_dir(kind, loaded_reg_file=None, last_dirs=None, fallback=None):
    """First existing field subfolder; then remembered folder; then fallback."""
    if kind not in FOLDER_NAMES:
        raise ValueError('Unsupported dialog kind: '+str(kind))
    root = field_root(loaded_reg_file)
    if root:
        for candidate in FOLDER_NAMES[kind]:
            path = root / candidate
            if path.is_dir():
                return str(path)
        # For a field that has not yet acquired PIXELS, start in field root.
        if kind == 'pixels':
            return str(root)
        if kind == 'radec':
            return str(Path(loaded_reg_file).resolve().parent)
        # For GAIA, defer to remembered/default when no field Gaia folder exists.
    remembered = (last_dirs or {}).get(kind)
    if remembered and Path(remembered).expanduser().is_dir():
        return str(Path(remembered).expanduser())
    if fallback:
        path = Path(fallback).expanduser()
        if path.is_file():
            path = path.parent
        if path.is_dir():
            return str(path)
    return str(root) if root else str(Path.home())

def remember(last_dirs, kind, selected):
    """Record a successful selection only; cancelled chooser leaves memory intact."""
    if selected:
        path = Path(selected).expanduser()
        if path.is_file():
            last_dirs[kind] = str(path.resolve().parent)
        elif path.is_dir():
            last_dirs[kind] = str(path.resolve())
    return last_dirs
