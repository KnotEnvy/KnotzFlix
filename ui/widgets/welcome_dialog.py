from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QCheckBox, QWidget, QFileDialog, QMessageBox
)


class WelcomeDialog(QDialog):
    """First-run welcome dialog to guide new users through setup."""
    
    folder_added = pyqtSignal(str)  # Signal when user adds a folder
    start_scan = pyqtSignal()  # Signal to start initial scan
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Welcome to KnotzFLix!")
        self.setModal(True)
        self.setFixedSize(600, 700)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2b2b35, stop:1 #1a1a1f);
                color: white;
            }
            QLabel {
                color: white;
            }
            QTextEdit {
                background-color: #1e1e23;
                border: 1px solid #555;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton {
                background-color: #4682b4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a9bd4;
            }
            QPushButton:pressed {
                background-color: #3a6b94;
            }
            QPushButton#secondary {
                background-color: #5a5a5f;
            }
            QPushButton#secondary:hover {
                background-color: #6a6a6f;
            }
            QCheckBox {
                color: white;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #555;
                border-radius: 3px;
                background-color: #2b2b30;
            }
            QCheckBox::indicator:checked {
                background-color: #4682b4;
                border-color: #4682b4;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header with logo area
        header_widget = QWidget()
        header_widget.setFixedHeight(120)
        header_layout = QVBoxLayout(header_widget)
        
        # Create a simple logo/header
        title_label = QLabel("🎬 Welcome to KnotzFLix!")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #4682b4; margin: 10px;")
        
        subtitle_label = QLabel("Your Personal Movie Library Manager")
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #87ceeb; margin-bottom: 10px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_widget)
        
        # Welcome message
        welcome_text = QTextEdit()
        welcome_text.setReadOnly(True)
        welcome_text.setMaximumHeight(200)
        welcome_content = """
<h3 style="color: #4682b4;">Welcome to KnotzFLix!</h3>

<p>Thanks for choosing KnotzFLix to manage your personal movie library. This quick setup will get you started in just a few minutes.</p>

<p><b style="color: #87ceeb;">What KnotzFLix does:</b></p>
<ul>
<li>🔍 <b>Scans your folders</b> to find all your movies automatically</li>
<li>🖼️ <b>Generates beautiful posters</b> using intelligent frame selection</li>
<li>⚡ <b>Lightning-fast search</b> to find any movie instantly</li>
<li>🔒 <b>Private library protection</b> with secure password encryption</li>
<li>🎯 <b>Smart organization</b> with Recently Added and Continue Watching</li>
</ul>

<p><b style="color: #ffcc00;">Important:</b> For best results, install <a href="https://ffmpeg.org/download.html" style="color: #87ceeb;">FFmpeg</a> to enable automatic poster generation. Without it, placeholder images will be used.</p>
        """
        welcome_text.setHtml(welcome_content)
        layout.addWidget(welcome_text)
        
        # Setup section
        setup_label = QLabel("Let's set up your first movie folder:")
        setup_font = QFont()
        setup_font.setPointSize(14)
        setup_font.setBold(True)
        setup_label.setFont(setup_font)
        setup_label.setStyleSheet("color: #4682b4; margin: 10px 0 5px 0;")
        layout.addWidget(setup_label)
        
        # Folder selection
        folder_layout = QHBoxLayout()
        
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("""
            color: #cccccc; 
            padding: 8px; 
            background-color: #1e1e23; 
            border: 1px solid #555; 
            border-radius: 4px;
            min-height: 20px;
        """)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_folder)
        
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)
        
        # Quick tips
        tips_label = QLabel("💡 Quick Tips:")
        tips_font = QFont()
        tips_font.setPointSize(12)
        tips_font.setBold(True)
        tips_label.setFont(tips_font)
        tips_label.setStyleSheet("color: #87ceeb; margin: 15px 0 5px 0;")
        layout.addWidget(tips_label)
        
        tips_text = QTextEdit()
        tips_text.setReadOnly(True)
        tips_text.setMaximumHeight(120)
        tips_content = """
<ul style="color: white; margin: 0; padding-left: 20px;">
<li><b>Multiple Folders:</b> You can add more folders later in Settings</li>
<li><b>File Types:</b> Supports MP4, AVI, MKV, MOV, and many other video formats</li>
<li><b>Subfolders:</b> KnotzFLix will scan all subfolders automatically</li>
<li><b>Safe Scanning:</b> Your files are never moved or modified, only read</li>
<li><b>Performance:</b> Initial scan may take time for large libraries</li>
</ul>
        """
        tips_text.setHtml(tips_content)
        layout.addWidget(tips_text)
        
        # Options
        options_layout = QVBoxLayout()
        
        self.dont_show_again = QCheckBox("Don't show this welcome dialog again")
        self.dont_show_again.setChecked(False)
        options_layout.addWidget(self.dont_show_again)
        
        layout.addLayout(options_layout)
        
        # Stretch to push buttons to bottom
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        skip_btn = QPushButton("Skip Setup")
        skip_btn.setObjectName("secondary")
        skip_btn.clicked.connect(self.skip_setup)
        
        button_layout.addWidget(skip_btn)
        button_layout.addStretch()
        
        self.start_btn = QPushButton("Add Folder & Start Scan")
        self.start_btn.clicked.connect(self.start_setup)
        self.start_btn.setEnabled(False)  # Disabled until folder selected
        self.start_btn.setDefault(True)
        
        button_layout.addWidget(self.start_btn)
        
        layout.addLayout(button_layout)
        
        # Store selected folder
        self.selected_folder = None
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Your Movie Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.selected_folder = folder
            # Truncate long paths for display
            display_path = folder
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            
            self.folder_label.setText(display_path)
            self.folder_label.setToolTip(folder)  # Full path in tooltip
            self.folder_label.setStyleSheet("""
                color: #87ceeb; 
                padding: 8px; 
                background-color: #1e1e23; 
                border: 1px solid #4682b4; 
                border-radius: 4px;
                min-height: 20px;
            """)
            self.start_btn.setEnabled(True)
            self.start_btn.setText(f"Add Folder & Start Scan")
    
    def start_setup(self):
        if self.selected_folder:
            self.folder_added.emit(self.selected_folder)
            self.start_scan.emit()
            
            # Show success message
            QMessageBox.information(
                self,
                "Setup Started!",
                f"Added folder: {self.selected_folder}\n\n"
                "KnotzFLix will now scan your movies and generate posters. "
                "This may take a few minutes depending on your library size.\n\n"
                "You can continue using the app while scanning in the background."
            )
            
            self.accept()
    
    def skip_setup(self):
        reply = QMessageBox.question(
            self,
            "Skip Setup?",
            "Are you sure you want to skip the initial setup?\n\n"
            "You can always add folders later in the Settings tab.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
    
    def should_show_again(self) -> bool:
        """Return False if user checked 'don't show again'."""
        return not self.dont_show_again.isChecked()