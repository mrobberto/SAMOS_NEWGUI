"""
This module defines various constants that will be used in multiple places, and preferably
should only be defined once so they can be changed all at once.

Authors
-------

    - Brian York (york@stsci.edu)

Use
---

    This module is intended to be imported and its individual constants used on their own.

Dependencies
------------
    
    None.
"""
from ginga import colors as gcolors
import sys
import tkinter as tk


# Color Information
INDICATOR_LIGHT_ON_COLOR = "#08F903"
INDICATOR_LIGHT_OFF_COLOR = "#194A18"
INDICATOR_LIGHT_PENDING_COLOR = "#F707D3"

r_ulim, g_llim, b_llim = 0.3, 0.6, 0.6
bright_blues = [c for c in gcolors.color_list if (gcolors.color_dict[c][0] <= r_ulim and
                                                  gcolors.color_dict[c][1] >= g_llim and
                                                  gcolors.color_dict[c][2] >= b_llim or
                                                  c == 'blueviolet' or c == 'cadetblue1')]
r_llim, g_ulim, b_ulim = 0.6, 0.5, 0.6
bright_reds = [c for c in gcolors.color_list if (gcolors.color_dict[c][0] >= r_llim and
                                                 gcolors.color_dict[c][1] <= g_ulim and
                                                 gcolors.color_dict[c][2] <= b_ulim)]
r_ulim, g_ullim, b_ulim = 0.5, 0.5, 0.6
bright_greens = [c for c in gcolors.color_list if (gcolors.color_dict[c][0] <= r_ulim and
                                                   gcolors.color_dict[c][1] >= g_llim and
                                                   gcolors.color_dict[c][2] <= b_ulim)]

NICE_COLORS_LIST = bright_blues
NICE_COLORS_LIST.extend(bright_reds)
NICE_COLORS_LIST.extend(bright_greens)

# Font sizes, by system
if sys.platform == "win32":
    BIGFONT = ("Arial", 12, 'bold')
    BIGFONT_20 = ("Arial", 12, 'bold')
    BIGFONT_15 = ("Arial", 10, 'bold')
else:
    BIGFONT = ("Arial", 24)
    BIGFONT_20 = ("Arial", 20)
    BIGFONT_15 = ("Arial", 15)

# Standard logging format
STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s'

# Standard FITS file header entry format
PARAM_ENTRY_FORMAT = '[Entry {}]\nType={}\nKeyword={}\nValue="{}"\nComment="{}\n"'

# TK constants

# Make a frame sticky everywhere (and thus resizing everywhere)
TK_STICKY_ALL = tk.N + tk.S + tk.E + tk.W
