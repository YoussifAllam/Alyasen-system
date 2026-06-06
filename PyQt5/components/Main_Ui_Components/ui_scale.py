"""
Central UI scale for the PyQt5 desktop app (Windows).

Layout and widgets are designed for 1920×1080 at 100% Windows display
scaling. Call :func:`configure_qt_scaling` before ``QApplication`` is
created, then :func:`init_scale` immediately after.
"""

from __future__ import annotations

import os
import re
from typing import Optional, Union

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget

# Baseline reference (Windows 1080p @ 100%)
REF_WIDTH = 1920
REF_HEIGHT = 1080
REF_FONT_PT = 10
MIN_FONT_PT = 7

MIN_SCALE = 0.75
MAX_SCALE = 1.5

_scale: float = 1.0

_PX_RE = re.compile(r"(\d+)px")


def configure_qt_scaling() -> None:
    """Disable Qt automatic scaling; the app applies one manual factor."""
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "0")
    os.environ.setdefault("QT_SCALE_FACTOR", "1")


def compute_scale_factor(screen=None) -> float:
    """
    Scale relative to 1920×1080 using the screen's available geometry.

    Uses Windows logical pixels (``availableGeometry``). Qt auto HiDPI is
    off, so we do not apply Linux-style ``logicalDotsPerInch`` adjustments.
    """
    app = QApplication.instance()
    if screen is None:
        if app is None:
            return 1.0
        screen = app.primaryScreen()
    if screen is None:
        return 1.0

    geo = screen.availableGeometry()
    w_ratio = geo.width() / REF_WIDTH
    h_ratio = geo.height() / REF_HEIGHT
    scale = min(w_ratio, h_ratio)
    return max(MIN_SCALE, min(scale, MAX_SCALE))


def init_scale(app: QApplication) -> float:
    """Compute scale from the primary screen, set the app font, and store it."""
    global _scale
    _scale = compute_scale_factor(app.primaryScreen())
    _apply_app_font(app, _scale)
    return _scale


def get_scale() -> float:
    """Return the active scale factor (1.0 at the 1920×1080 baseline)."""
    return _scale


def scale_int(px: int) -> int:
    """Scale a pixel length designed at the 1920×1080 baseline."""
    if px == 0:
        return 0
    return max(1, round(px * _scale))


def scale_size(size: Union[QSize, int], height: Optional[int] = None) -> QSize:
    """Scale a ``QSize`` or a (width, height) pair."""
    if isinstance(size, QSize):
        return QSize(scale_int(size.width()), scale_int(size.height()))
    if height is None:
        raise TypeError("height is required when the first argument is an int")
    return QSize(scale_int(size), scale_int(height))


def scaled_stylesheet(qss: str) -> str:
    """Replace integer ``Npx`` lengths in QSS with scaled values."""
    return _PX_RE.sub(lambda m: f"{scale_int(int(m.group(1)))}px", qss)


def apply_screen_dialog_geometry(
    dialog: QWidget,
    *,
    min_width_ratio: float = 0.5,
    min_height_ratio: float = 0.5,
    width_ratio: float = 0.7,
    height_ratio: float = 0.75,
) -> None:
    """Size a dialog from the primary screen (Windows logical pixels)."""
    app = QApplication.instance()
    if app is None:
        return
    screen = app.primaryScreen()
    if screen is None:
        return
    geo = screen.availableGeometry()
    dialog.setMinimumSize(
        int(geo.width() * min_width_ratio),
        int(geo.height() * min_height_ratio),
    )
    dialog.resize(
        int(geo.width() * width_ratio),
        int(geo.height() * height_ratio),
    )


def apply_form_dialog_geometry(dialog: QWidget) -> None:
    """Medium form dialogs (edit/add, ~500px baseline)."""
    apply_screen_dialog_geometry(
        dialog,
        min_width_ratio=0.4,
        min_height_ratio=0.45,
        width_ratio=0.5,
        height_ratio=0.55,
    )


def apply_compact_dialog_geometry(dialog: QWidget) -> None:
    """Small confirmation / short forms (~400px baseline)."""
    apply_screen_dialog_geometry(
        dialog,
        min_width_ratio=0.35,
        min_height_ratio=0.3,
        width_ratio=0.4,
        height_ratio=0.4,
    )


def _apply_app_font(app: QApplication, scale: float) -> None:
    font = app.font()
    font.setPointSize(max(MIN_FONT_PT, round(REF_FONT_PT * scale)))
    app.setFont(font)
