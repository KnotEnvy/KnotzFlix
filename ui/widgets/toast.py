from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QEasingCurve, QRect
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import QPropertyAnimation


class Toast(QLabel):
    """A small non-modal toast message that fades out automatically.

    Use show_toast(parent, message) for convenience.
    """

    def __init__(self, parent: Optional[QWidget], message: str, *, duration_ms: int = 2500) -> None:
        super().__init__(parent)
        self.setText(message)
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAutoFillBackground(True)

        pal = self.palette()
        # Semi-transparent dark background with white text
        pal.setColor(QPalette.ColorRole.Window, pal.color(QPalette.ColorRole.WindowText))
        self.setPalette(pal)
        self.setStyleSheet(
            """
            QLabel {
              background-color: rgba(32,32,32,210);
              color: white;
              border-radius: 8px;
              padding: 8px 12px;
            }
            """
        )

        self._duration = duration_ms
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(500)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        # Position bottom-center of parent or screen
        parent = self.parentWidget()
        geom: QRect
        if parent is not None:
            geom = parent.rect()
            pos = parent.mapToGlobal(geom.center())
            self.adjustSize()
            x = pos.x() - self.width() // 2
            y = parent.mapToGlobal(geom.bottomLeft()).y() - self.height() - 24
            self.move(x, y)
        else:
            # Fallback: center of primary screen
            screen = self.screen()
            self.adjustSize()
            if screen:
                g = screen.availableGeometry()
                x = g.left() + (g.width() - self.width()) // 2
                y = g.bottom() - self.height() - 24
                self.move(x, y)

        self.setWindowOpacity(1.0)
        # Auto-hide timer then fade out
        QTimer.singleShot(self._duration, self._fade_out)

    def _fade_out(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self.close)
        self._anim.start()


def show_toast(parent: Optional[QWidget], message: str, *, duration_ms: int = 2500) -> None:
    t = Toast(parent, message, duration_ms=duration_ms)
    t.show()

