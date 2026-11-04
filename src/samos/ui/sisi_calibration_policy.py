"""SAMOS SISI calibration-order preflight; no hardware or FITS access.

The quicklook master builder is not modified here. BIAS is necessary for
DARK and short FLAT suites; a DARK master is not required for short FLATs.
"""
from pathlib import Path

MARKER = 'SC3_SISI_CAL_ORDER_GUARD_V1'


def check_calibration_order(exposure_type, bias_checked, dark_checked, ql_dir):
    """Return (allowed, message) for starting a calibration acquisition.

    `ql_dir` is the **real** quicklook directory for hardware START, or the
    **isolated simulation** directory for SIMULATE SISI. No files are changed.
    """
    kind = str(exposure_type).strip().lower()
    if kind not in {'dark', 'flat'}:
        return True, ''
    if not bool(bias_checked):
        return False, (f'{kind.upper()} acquisition: Bias correction is OFF.\n\n'
                       'Take and activate a BIAS suite first, enable the Bias '
                       'checkbox, then start this acquisition. No frames were taken.')
    bias_path = Path(ql_dir) / 'superbias.fits'
    if not bias_path.is_file():
        return False, (f'{kind.upper()} acquisition: no active master BIAS was found at:\n'
                       f'{bias_path}\n\nTake a BIAS suite first. No frames were taken.')
    if kind == 'flat' and bool(dark_checked):
        return False, ('Short FLAT acquisition: Dark correction is selected.\n\n'
                       'For the current short-exposure flat procedure, leave '
                       'Dark OFF and Bias ON. No frames were taken.')
    return True, ''
