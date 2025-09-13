from __future__ import annotations

from typing import Optional
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QPixmap
from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar


class KnotzFlixSplash:
    """Professional splash screen for KnotzFLix application."""
    
    def __init__(self, parent=None):
        
        # Create splash screen pixmap
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor(20, 20, 25))  # Dark background
        
        # Paint the splash screen
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw gradient background
        gradient_brush = QBrush(QColor(25, 25, 35))
        painter.fillRect(pixmap.rect(), gradient_brush)
        
        # Draw border
        border_pen = QPen(QColor(70, 130, 180), 3)  # Steel blue border
        painter.setPen(border_pen)
        painter.drawRect(5, 5, 590, 390)
        
        # App title
        title_font = QFont("Arial", 36, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(70, 130, 180))  # Steel blue
        painter.drawText(50, 120, "KnotzFLix")
        
        # Subtitle
        subtitle_font = QFont("Arial", 14)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(50, 150, "Your Personal Movie Library Manager")
        
        # Version info
        version_font = QFont("Arial", 10)
        painter.setFont(version_font)
        painter.setPen(QColor(150, 150, 150))
        painter.drawText(50, 180, "Version 1.0.0 - Production Ready")
        
        # Features list
        feature_font = QFont("Arial", 11)
        painter.setFont(feature_font)
        painter.setPen(QColor(180, 180, 180))
        features = [
            "• Lightning-fast search with FTS5",
            "• Automatic poster generation",
            "• Private library protection", 
            "• External player integration",
            "• File system watching",
            "• Offline-first design"
        ]
        
        y_pos = 220
        for feature in features:
            painter.drawText(50, y_pos, feature)
            y_pos += 20
        
        # Copyright
        painter.setPen(QColor(120, 120, 120))
        painter.drawText(400, 370, "© 2025 KnotzFLix Team")
        
        painter.end()
        
        # Create splash screen
        self.splash = QSplashScreen(pixmap)
        self.splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        
        # Add progress bar
        self.progress = QProgressBar(self.splash)
        self.progress.setGeometry(50, 350, 500, 20)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #4682b4;
                border-radius: 10px;
                text-align: center;
                background-color: #1a1a1f;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4682b4, stop:1 #87ceeb);
                border-radius: 8px;
            }
        """)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        
        # Status message
        self.status_msg = ""
        
    def show(self):
        """Show the splash screen."""
        self.splash.show()
        
    def close(self):
        """Close the splash screen."""
        self.splash.close()
        
    def showMessage(self, message: str, progress: Optional[int] = None):
        """Show a status message and optionally update progress."""
        
        self.status_msg = message
        self.splash.showMessage(message, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, QColor(200, 200, 200))
        
        if progress is not None:
            self.progress.setValue(min(100, max(0, progress)))
            
        # Process events to update display
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
    def setProgress(self, value: int):
        """Set progress bar value (0-100)."""
        self.progress.setValue(min(100, max(0, value)))
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()