"""Use the same real Arial family as the PowerPoint-authored overview.

Install Arial locally, or set GLMEXT_FONT_DIR to a private directory containing
the regular, bold, italic and bold-italic TTF files. Font files are not distributed
in this repository. Missing Arial is an error, never a silent font substitution.
"""
import os
from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager


def use_arial(size=None):
    directory = os.environ.get('GLMEXT_FONT_DIR')
    if directory:
        for path in sorted(Path(directory).glob('*.ttf')):
            font_manager.fontManager.addfont(str(path))
    resolved = {}
    for weight, style in [('normal', 'normal'), ('bold', 'normal'),
                          ('normal', 'italic'), ('bold', 'italic')]:
        props = font_manager.FontProperties(family='Arial', weight=weight, style=style)
        try:
            path = font_manager.findfont(props, fallback_to_default=False)
        except ValueError as exc:
            raise RuntimeError('Arial is required: install it or set GLMEXT_FONT_DIR '
                               'to a private directory with Arial TTF files.') from exc
        if font_manager.FontProperties(fname=path).get_name() != 'Arial':
            raise RuntimeError('Unexpected substitute for Arial: ' + path)
        resolved[(weight, style)] = path
    mpl.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial'],
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    if size is not None:
        mpl.rcParams.update({key: size for key in (
            'font.size', 'axes.titlesize', 'axes.labelsize', 'legend.fontsize',
            'xtick.labelsize', 'ytick.labelsize')})
    return resolved
