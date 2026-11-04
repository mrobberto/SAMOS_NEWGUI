"""Geometry-only identity tracking for SAMOS GUI (no DMD or I/O side effects)."""
import hashlib
import json


def geometry_signature(regions, digits=3):
    """Canonical signature for rectangular astropy PIXEL regions.

    This is an observational comparison, not a DMD bitmap signature.
    Coordinates/dimensions are rounded to 0.001 pixel; rotations to 0.001 deg.
    Region order and visual style are ignored. Never assume unsupported shapes match.
    """
    rows = []
    for region in regions:
        if not all(hasattr(region, key) for key in ('center','width','height','angle')):
            raise ValueError('Unsupported mask region shape: '+type(region).__name__)
        ang = float(region.angle.to_value('deg')) % 180.0
        if abs(ang-180.0) < 10**(-digits):
            ang=0.0
        rows.append((round(float(region.center.x), digits),
                     round(float(region.center.y), digits),
                     round(float(region.width), digits),
                     round(float(region.height), digits),
                     round(ang, digits)))
    rows.sort()
    if not rows:
        raise ValueError('No slit rectangles available for identity comparison')
    return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode('ascii')).hexdigest()


def change_status(original_signature, current_regions):
    if not original_signature:
        return 'UNKNOWN'
    return 'UNCHANGED' if geometry_signature(current_regions) == original_signature else 'MODIFIED'
