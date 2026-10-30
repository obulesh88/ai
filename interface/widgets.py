"""Custom widgets: glass panels, holographic avatar, gauges, chat view, quick tiles."""
import html
import math

from PySide6.QtCore import QPointF, QPropertyAnimation, QRectF, Qt, QTimer, Property
from PySide6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath,
                           QPen, QRadialGradient)
from PySide6.QtWidgets import (QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget)

from interface import theme


class GlassPanel(QFrame):
    """Translucent rounded panel with a neon border and a cyan title bar."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self._glow = 0.0
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 12)
        outer.setSpacing(8)
        header = QHBoxLayout()
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("PanelTitle")
        header.addWidget(self.title_label)
        header.addStretch(1)
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
        self.setMinimumSize(220, 220)
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
        side = min(self.width(), self.height())
        cx, cy = self.width() / 2, self.height() / 2
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
        painter.drawText(QRectF(0, cy + radius * 1.15 + 10, self.width(), 30),
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
        self.setHtml(self._wrap(""))

    @staticmethod
    def _bubble(kind: str, text: str) -> str:
        if kind == "user":
            bg, align, who, color = "rgba(0,229,255,0.13)", "right", "YOU", theme.CYAN
        elif kind == "error":
            bg, align, who, color = "rgba(255,77,109,0.14)", "left", "SYSTEM", theme.DANGER
        else:
            bg, align, who, color = "rgba(47,107,255,0.16)", "left", "HEMA", theme.VIOLET
        safe = html.escape(text).replace("\n", "<br>")
        return (f'<div style="margin:6px 2px; text-align:{align};">'
                f'<span style="color:{color}; font-size:10px; letter-spacing:2px;">{who}</span><br>'
                f'<span style="background-color:{bg}; padding:6px 9px; border-radius:8px; '
                f'font-family:Consolas, monospace; font-size:12px;">{safe}</span></div>')

    def _wrap(self, body: str) -> str:
        return ('<html><body style="background:transparent; color:#d8f6ff;">'
                + "".join(self._html) + body + "</body></html>")

    def add(self, kind: str, text: str):
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

    def transcript(self) -> str:
        import re
        return re.sub(r"<[^>]+>", " ", "".join(self._html))

    def _scroll_end(self):
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())


class QuickTile(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(f"{icon}   {label}")
        self.setObjectName("QuickTile")
        self.setMinimumHeight(46)
        self.setCursor(Qt.PointingHandCursor)


def fade_in(widget: QWidget, duration: int = 420) -> QPropertyAnimation:
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.start()
    widget._fade_anim = anim
    return anim
