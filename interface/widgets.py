"""Custom widgets: glass panels, holographic avatar, gauges, chat view, quick tiles."""
import html
import math

from PySide6.QtCore import QPointF, QPropertyAnimation, QRectF, Qt, QTimer, Property
from PySide6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath,
                           QPen, QRadialGradient)
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget)

from interface import theme


class GlassPanel(QFrame):
    """Translucent rounded panel with a neon border and a cyan title bar."""

    def __init__(self, title: str = "", parent=None, compact: bool = False):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self._glow = 0.0
        self._compact = compact
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12 if compact else 16, 8 if compact else 12,
                                 12 if compact else 16, 10 if compact else 14)
        outer.setSpacing(6 if compact else 10)
        header = QHBoxLayout()
        header.setSpacing(6)
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("PanelTitle")
        header.addWidget(self.title_label)
        header.addStretch(1)
        self.header = header
        outer.addLayout(header)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        outer.addLayout(self.body, 1)

    def add(self, widget, stretch: int = 0):
        self.body.addWidget(widget, stretch)
        return widget

    def add_layout(self, layout, stretch: int = 0):
        self.body.addLayout(layout, stretch)
        return layout

    def add_action(self, widget, stretch: int = 0):
        """Adds a small control to the right side of the panel header."""
        self.header.addWidget(widget, stretch)
        return widget

    def set_glow(self, value: float):
        self._glow = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        path = QPainterPath()
        path.addRoundedRect(rect, theme.RADIUS, theme.RADIUS)

        fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
        fill.setColorAt(0.0, QColor(14, 30, 50, 200))
        fill.setColorAt(1.0, QColor(6, 14, 26, 175))
        painter.fillPath(path, QBrush(fill))

        border = QColor(theme.CYAN)
        border.setAlpha(int(55 + 120 * self._glow))
        pen = QPen(border, 1.2 + self._glow)
        painter.setPen(pen)
        painter.drawPath(path)

        accent = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.top())
        accent.setColorAt(0.0, QColor(0, 229, 255, 160))
        accent.setColorAt(0.6, QColor(47, 107, 255, 40))
        accent.setColorAt(1.0, QColor(0, 229, 255, 0))
        painter.setPen(QPen(QBrush(accent), 1.6))
        painter.drawLine(QPointF(rect.left() + 12, rect.top() + 1),
                         QPointF(rect.right() - 12, rect.top() + 1))
        painter.end()


class HoloAvatar(QWidget):
    """Animated holographic HEMA presence. States: idle, thinking, error, listening."""

    STATES = {"idle": theme.CYAN, "thinking": theme.VIOLET, "error": theme.DANGER,
              "listening": theme.OK}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._phase = 0.0
        self._state = "idle"
        self._caption = "HEMA ONLINE"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def _tick(self):
        self._phase = (self._phase + 0.035) % (2 * math.pi)
        self.update()

    def set_state(self, state: str, caption: str = None):
        self._state = state if state in self.STATES else "idle"
        self._caption = caption or {"idle": "HEMA ONLINE", "thinking": "PROCESSING",
                                    "error": "OFFLINE", "listening": "LISTENING"}[self._state]
        self.update()

    @property
    def state(self) -> str:
        return self._state

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        ink = QColor(self.STATES[self._state])
        caption_height = 26
        side = min(self.width(), self.height() - caption_height)
        cx, cy = self.width() / 2, (self.height() - caption_height) / 2
        radius = side * 0.34

        halo = QRadialGradient(QPointF(cx, cy), radius * 2.0)
        c0 = QColor(ink); c0.setAlpha(120)
        c1 = QColor(ink); c1.setAlpha(0)
        halo.setColorAt(0.0, c0)
        halo.setColorAt(1.0, c1)
        painter.setBrush(QBrush(halo))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius * 2.0, radius * 2.0)

        for i, (scale, alpha, speed) in enumerate(((1.55, 40, 1.0), (1.32, 70, -1.4), (1.12, 110, 2.0))):
            pen = QPen(QColor(ink.red(), ink.green(), ink.blue(), alpha), 1.6)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            r = radius * scale
            start = int(math.degrees(self._phase * speed + i)) * 16
            painter.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), start, 110 * 16)
            painter.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), start + 180 * 16, 70 * 16)

        core = QRadialGradient(QPointF(cx, cy - radius * 0.15), radius * 1.25)
        bright = QColor(ink); bright.setAlpha(215)
        deep = QColor(theme.BLUE); deep.setAlpha(60)
        core.setColorAt(0.0, bright)
        core.setColorAt(0.55, QColor(ink.red(), ink.green(), ink.blue(), 90))
        core.setColorAt(1.0, deep)
        painter.setBrush(QBrush(core))
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1.2))
        painter.drawEllipse(QPointF(cx, cy - radius * 0.15), radius * 0.62, radius * 0.62)

        # inner hexagon + moving scanline give the core some structure
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 95), 1.0))
        hexagon = QPainterPath()
        hex_r = radius * 0.34
        for i in range(6):
            angle = math.radians(60 * i - 90)
            point = QPointF(cx + hex_r * math.cos(angle),
                            cy - radius * 0.15 + hex_r * math.sin(angle))
            hexagon.moveTo(point) if i == 0 else hexagon.lineTo(point)
        hexagon.closeSubpath()
        painter.drawPath(hexagon)

        scan_y = cy - radius * 0.15 + math.sin(self._phase * 0.8) * radius * 0.5
        scan = QColor(255, 255, 255, 55)
        painter.setPen(QPen(scan, 1.0))
        half = (radius ** 2 - (scan_y - (cy - radius * 0.15)) ** 2) ** 0.5 * 0.8
        painter.drawLine(QPointF(cx - half, scan_y), QPointF(cx + half, scan_y))

        painter.setPen(Qt.NoPen)
        bars = 22
        amp = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(self._phase * 2))
        for i in range(bars):
            h = abs(math.sin(self._phase * 3 + i * 0.55)) * 16 * amp + 4
            if self._state == "thinking":
                h = max(h, abs(math.sin(self._phase * 7 + i)) * 22 + 5)
            x = cx - (bars * 5) / 2 + i * 5
            painter.setBrush(QColor(ink.red(), ink.green(), ink.blue(), 170))
            painter.drawRoundedRect(QRectF(x, cy + radius * 1.15 - h, 3, h), 1.5, 1.5)

        painter.setPen(QColor(theme.TEXT))
        f = QFont(self.font())
        f.setPointSize(max(9, int(side * 0.045)))
        f.setBold(True)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 3)
        painter.setFont(f)
        painter.drawText(QRectF(0, self.height() - caption_height + 4, self.width(),
                                caption_height),
                         Qt.AlignHCenter, self._caption)
        painter.end()


class StatGauge(QWidget):
    """Circular percentage gauge with a label and a (elided) detail line."""

    def __init__(self, label: str, unit: str = "%", warn_at: float = 65.0,
                 danger_at: float = 85.0, parent=None):
        super().__init__(parent)
        self._label = label
        self._unit = unit
        self._value = 0.0
        self._detail = "--"
        self._warn_at = warn_at
        self._danger_at = danger_at
        self.setMinimumSize(112, 116)

    def set_value(self, value, detail: str = None):
        self._value = float(value) if value is not None else 0.0
        self._detail = detail if detail is not None else ("n/a" if value is None else f"{self._value:.0f}{self._unit}")
        self.update()

    def _elide(self, painter, text: str, width: float) -> str:
        metrics = painter.fontMetrics()
        return metrics.elidedText(text, Qt.ElideRight, max(10, int(width)))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        side = min(self.width() - 16, self.height() - 40)
        rect = QRectF((self.width() - side) / 2, 6, side, side)
        painter.setPen(QPen(QColor(255, 255, 255, 28), 7, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225 * 16, -270 * 16)
        ink = QColor(theme.CYAN)
        if self._danger_at is not None and self._value >= self._danger_at:
            ink = QColor(theme.DANGER)
        elif self._warn_at is not None and self._value >= self._warn_at:
            ink = QColor(theme.WARN)
        painter.setPen(QPen(ink, 7, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225 * 16, int(-270 * 16 * min(100.0, self._value) / 100.0))

        f = QFont(self.font()); f.setPointSize(10); f.setBold(True)
        painter.setFont(f)
        painter.setPen(QColor(theme.TEXT))
        painter.drawText(rect, Qt.AlignCenter, f"{self._value:.0f}{self._unit}")

        small = QFont(self.font()); small.setPointSize(7)
        painter.setFont(small)
        painter.setPen(QColor(theme.TEXT_DIM))
        label_rect = QRectF(2, self.height() - 30, self.width() - 4, 12)
        painter.drawText(label_rect, Qt.AlignHCenter,
                         self._elide(painter, self._label, label_rect.width()))
        detail_rect = QRectF(2, self.height() - 17, self.width() - 4, 12)
        painter.drawText(detail_rect, Qt.AlignHCenter,
                         self._elide(painter, self._detail, detail_rect.width()))
        painter.end()


class ChatView(QTextBrowser):
    """Chat transcript with glass bubbles and streaming support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(False)
        self._html = []
        self._stream_open = False
        self._stream_buffer = ""
        self._placeholder = "No messages yet - say hello, or type /help."
        self._render()

    @staticmethod
    def _bubble(kind: str, text: str) -> str:
        if kind == "user":
            accent, who, align = theme.CYAN, "YOU", "right"
            bubble_bg, text_color = "rgba(0,229,255,0.16)", theme.TEXT
        elif kind == "error":
            accent, who, align = theme.DANGER, "SYSTEM", "left"
            bubble_bg, text_color = "rgba(255,77,109,0.18)", theme.TEXT
        else:
            accent, who, align = theme.VIOLET, "HEMA", "left"
            bubble_bg, text_color = "rgba(47,107,255,0.22)", theme.TEXT
        safe = html.escape(text).replace(chr(10), "<br>")
        return (
            '<table width="100%" cellspacing="0" cellpadding="0" border="0">'
            f'<tr><td align="{align}" style="color:{accent}; font-size:10px; '
            f'letter-spacing:2px; padding-bottom:2px;">{who}</td></tr>'
            f'<tr><td align="{align}">'
            '<table cellspacing="0" cellpadding="7" border="0" '
            f'style="background-color:{bubble_bg};">'
            f'<tr><td style="color:{text_color}; font-family:Consolas, monospace; '
            f'font-size:12px;">{safe}</td></tr></table>'
            '</td></tr>'
            '<tr><td style="font-size:6px;">&nbsp;</td></tr>'
            '</table>'
        )

    def _wrap(self, body: str) -> str:
        hint = ""
        if not self._html and not body.strip():
            hint = ('<div style="color:#5d7f92; margin-top:18px;">'
                    + html.escape(self._placeholder) + '</div>')
        return ('<html><body style="background:transparent; color:#d8f6ff;">'
                + "".join(self._html) + body + hint + "</body></html>")

    def _render(self) -> None:
        self.setHtml(self._wrap(""))
        self._scroll_end()

    def set_placeholder(self, text: str) -> None:
        self._placeholder = text
        self._render()

    def add(self, kind: str, text: str):
        if self._stream_open:
            self.end_stream()
        self._html.append(self._bubble(kind, text))
        self._stream_open = False
        self.setHtml(self._wrap(""))
        self._scroll_end()

    def begin_stream(self) -> None:
        self._stream_open = True
        self._stream_buffer = ""
        self.setHtml(self._wrap(self._bubble("assistant", "")))
        self._scroll_end()

    def append_stream(self, chunk: str) -> None:
        if not self._stream_open:
            self.begin_stream()
        self._stream_buffer += chunk
        self.setHtml(self._wrap(self._bubble("assistant", self._stream_buffer)))
        self._scroll_end()

    def end_stream(self, suffix: str = "") -> str:
        text = self._stream_buffer + suffix
        self._stream_open = False
        if text.strip():
            self._html.append(self._bubble("assistant", text))
        self.setHtml(self._wrap(""))
        self._scroll_end()
        return text

    def clear_all(self) -> None:
        """Empties the visible transcript (stored history is untouched)."""
        self._html = []
        self._stream_open = False
        self._stream_buffer = ""
        self._render()

    def is_empty(self) -> bool:
        return not self._html and not self._stream_open

    def transcript(self) -> str:
        import re
        return re.sub(r"<[^>]+>", " ", "".join(self._html))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scroll_end()

    def _scroll_end(self):
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())


class QuickTile(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(f"{icon}   {label}")
        self.setObjectName("QuickTile")
        self.setMinimumHeight(46)
        self.setCursor(Qt.PointingHandCursor)


class LogoMark(QWidget):
    """Small neon hexagon mark used in the top navigation."""

    def __init__(self, size: int = 36, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        side = min(self.width(), self.height()) - 2
        centre = QPointF(self.width() / 2, self.height() / 2)
        path = QPainterPath()
        for i in range(6):
            angle = math.radians(60 * i - 30)
            point = QPointF(centre.x() + side / 2 * math.cos(angle),
                            centre.y() + side / 2 * math.sin(angle))
            path.moveTo(point) if i == 0 else path.lineTo(point)
        path.closeSubpath()
        fill = QLinearGradient(0, 0, side, side)
        fill.setColorAt(0.0, QColor(theme.BLUE))
        fill.setColorAt(1.0, QColor(theme.CYAN))
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(QColor(theme.CYAN), 1.2))
        painter.drawPath(path)
        painter.setPen(QColor("#031018"))
        f = QFont(self.font())
        f.setPointSize(max(8, int(side * 0.38)))
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(self.rect(), Qt.AlignCenter, "H")
        painter.end()


class StatusDot(QWidget):
    """Small state indicator: online (cyan), busy (violet), offline (red)."""

    COLORS = {"online": theme.OK, "busy": theme.VIOLET, "offline": theme.DANGER,
              "idle": theme.TEXT_DIM}

    def __init__(self, size: int = 9, parent=None):
        super().__init__(parent)
        self._state = "idle"
        self.setFixedSize(size + 6, size + 6)

    def set_state(self, state: str):
        self._state = state if state in self.COLORS else "idle"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        ink = QColor(self.COLORS[self._state])
        halo = QColor(ink); halo.setAlpha(55)
        centre = QPointF(self.width() / 2, self.height() / 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(centre, self.width() / 2, self.height() / 2)
        painter.setBrush(ink)
        painter.drawEllipse(centre, self.width() / 4, self.height() / 4)
        painter.end()


class NavButton(QPushButton):
    """Sidebar navigation item with a glyph, a label and an active accent bar."""

    def __init__(self, glyph: str, label: str, parent=None):
        super().__init__(f"{glyph}   {label}", parent)
        self.setObjectName("NavButton")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(38)
        self.setToolTip(label)


class MeterRow(QWidget):
    """Compact label + bar + value row for CPU / memory / disk."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._value = 0.0
        self._detail = "--"
        self._bar = QWidget(self)
        self._bar.setObjectName("MeterBar")
        self._bar.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(40)
        self.setMaximumHeight(44)

    def set_value(self, percent, detail: str):
        self._value = 0.0 if percent is None else max(0.0, min(100.0, float(percent)))
        self._detail = detail
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        width = self.width()
        small = QFont(self.font()); small.setPointSize(8); small.setBold(True)
        painter.setFont(small)
        painter.setPen(QColor(theme.TEXT_DIM))
        painter.drawText(QRectF(0, 0, width * 0.5, 14), Qt.AlignLeft, self._label.upper())
        value_font = QFont(self.font()); value_font.setPointSize(8)
        painter.setFont(value_font)
        painter.setPen(QColor(theme.TEXT))
        detail = painter.fontMetrics().elidedText(self._detail, Qt.ElideRight,
                                                  int(width * 0.6))
        painter.drawText(QRectF(width * 0.4, 0, width * 0.6, 14), Qt.AlignRight, detail)

        track = QRectF(0, 19, width, 6)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 26))
        painter.drawRoundedRect(track, 3, 3)
        ink = QColor(theme.CYAN)
        if self._value >= 88:
            ink = QColor(theme.DANGER)
        elif self._value >= 70:
            ink = QColor(theme.WARN)
        filled = QRectF(0, 19, max(3.0, width * self._value / 100.0), 6)
        gradient = QLinearGradient(filled.topLeft(), filled.topRight())
        gradient.setColorAt(0.0, QColor(theme.BLUE))
        gradient.setColorAt(1.0, ink)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(filled, 3, 3)
        painter.end()


def configure_list(widget):
    """Compact, non-scrolling-sideways list: long text elides with a tooltip instead."""
    widget.setObjectName("Plain")
    widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    widget.setTextElideMode(Qt.ElideRight)
    widget.setWordWrap(False)
    widget.setUniformItemSizes(True)
    return widget


def chip(text: str, color: str = None) -> QLabel:
    label = QLabel(text)
    label.setObjectName("StatusPill")
    if color:
        label.setStyleSheet(f"color:{color}; border:1px solid {color}; border-radius:10px;"
                            "padding:4px 10px; font-size:11px;")
    return label


def elide(label: QLabel, text: str, width: int = None) -> None:
    """Sets text, eliding with '...' instead of letting the layout clip it."""
    metrics = label.fontMetrics()
    available = width if width else max(20, label.width() - 4)
    label.setText(metrics.elidedText(text, Qt.ElideRight, available))
    label.setToolTip(text)


def fade_window(window: QWidget, duration: int = 380):
    """Fades the whole window via its opacity property.

    A QGraphicsOpacityEffect is deliberately avoided: it conflicts with the custom
    paintEvent widgets (Qt logs "painted by one painter at a time").
    """
    import os
    if os.environ.get("QT_QPA_PLATFORM", "").lower() in ("offscreen", "minimal"):
        return None  # headless platforms have no window opacity
    animation = QPropertyAnimation(window, b"windowOpacity", window)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.start()
    window._window_fade = animation
    return animation
