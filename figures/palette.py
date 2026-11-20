"""The one palette every figure uses.

Hue is reserved for the two candidates and their overlap: orange is always Smith, blue always Rigdon, plum always
"compatible with both". The Book of Mormon is always black. Everything else (other authors, layers, folds, generic
illustrations) is neutral grey, told apart by labels, fill (solid = the model learned it; hollow = it never did) or
shape. Checked with the dataviz palette validator (light surface, all pairs, colour-blind simulation).
"""
INK, INK2, MUTED = "#1f1f1d", "#5f5e58", "#8a8984"       # text: primary, secondary, tertiary
RULE, GRID, SURF = "#c9c7c0", "#ebe9e4", "#fcfcfb"       # axes, gridlines, background
BAND, BOX = "#f4f3ef", "#f4f3ef"                         # row bands, panel boxes

SMITH, RIGDON, BOTH, NEITHER = "#eb6834", "#2a78d6", "#8e2d7a", "#e3e1db"
SMITH_PALE, RIGDON_PALE = "#fbd9c9", "#d6e6fa"
TARGET = INK                                              # the Book of Mormon

GREY_DARK, GREY, GREY_LIGHT, GREY_PALE = "#5f5e58", "#9a9992", "#c9c7c0", "#e6e4de"   # neutral roles, dark to pale
GREY_RAMP = ["#f4f3ef", "#e3e1db", "#c9c7c0", "#a3a199", "#76746d", "#4a4944"]     # sequential share, light to dark
