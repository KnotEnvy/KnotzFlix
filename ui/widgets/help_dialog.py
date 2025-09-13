from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTabWidget, QWidget
)


class HelpDialog(QDialog):
    """Help dialog with keyboard shortcuts and user guide."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("KnotzFLix Help & Shortcuts")
        self.setModal(True)
        self.setFixedSize(700, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b30;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b30;
            }
            QTabBar::tab {
                background-color: #3c3c41;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4682b4;
            }
            QTextEdit {
                background-color: #1e1e23;
                border: 1px solid #555;
                color: white;
                font-size: 12px;
                line-height: 1.4;
            }
            QPushButton {
                background-color: #4682b4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a9bd4;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("KnotzFLix Help & User Guide")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #4682b4; margin: 10px;")
        layout.addWidget(header_label)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Keyboard Shortcuts Tab
        shortcuts_tab = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_tab)
        
        shortcuts_text = QTextEdit()
        shortcuts_text.setReadOnly(True)
        shortcuts_content = """
<h3 style="color: #4682b4;">Keyboard Shortcuts</h3>

<h4 style="color: #87ceeb;">Navigation & Selection:</h4>
<table style="color: white; width: 100%;">
<tr><td style="padding: 4px;"><b>Arrow Keys</b></td><td style="padding: 4px;">Navigate through movie grid</td></tr>
<tr><td style="padding: 4px;"><b>Home</b></td><td style="padding: 4px;">Go to first movie</td></tr>
<tr><td style="padding: 4px;"><b>End</b></td><td style="padding: 4px;">Go to last movie</td></tr>
<tr><td style="padding: 4px;"><b>Page Up</b></td><td style="padding: 4px;">Scroll up one page</td></tr>
<tr><td style="padding: 4px;"><b>Page Down</b></td><td style="padding: 4px;">Scroll down one page</td></tr>
<tr><td style="padding: 4px;"><b>Enter / Double-Click</b></td><td style="padding: 4px;">Open movie details dialog</td></tr>
<tr><td style="padding: 4px;"><b>Escape</b></td><td style="padding: 4px;">Close current dialog or clear search</td></tr>
</table>

<h4 style="color: #87ceeb;">Movie Actions:</h4>
<table style="color: white; width: 100%;">
<tr><td style="padding: 4px;"><b>P</b></td><td style="padding: 4px;">Play selected movie in external player</td></tr>
<tr><td style="padding: 4px;"><b>R</b></td><td style="padding: 4px;">Reveal movie file in file explorer</td></tr>
<tr><td style="padding: 4px;"><b>W</b></td><td style="padding: 4px;">Mark movie as watched</td></tr>
<tr><td style="padding: 4px;"><b>U</b></td><td style="padding: 4px;">Mark movie as unwatched</td></tr>
<tr><td style="padding: 4px;"><b>Right-Click</b></td><td style="padding: 4px;">Open context menu with all actions</td></tr>
</table>

<h4 style="color: #87ceeb;">Search & Filtering:</h4>
<table style="color: white; width: 100%;">
<tr><td style="padding: 4px;"><b>Ctrl+F</b></td><td style="padding: 4px;">Focus search box</td></tr>
<tr><td style="padding: 4px;"><b>Type anywhere</b></td><td style="padding: 4px;">Start typing to search (auto-focus)</td></tr>
<tr><td style="padding: 4px;"><b>Ctrl+Tab</b></td><td style="padding: 4px;">Switch between tabs (Library, Recent, etc.)</td></tr>
</table>

<h4 style="color: #87ceeb;">Application:</h4>
<table style="color: white; width: 100%;">
<tr><td style="padding: 4px;"><b>F1</b></td><td style="padding: 4px;">Show this help dialog</td></tr>
<tr><td style="padding: 4px;"><b>Ctrl+,</b></td><td style="padding: 4px;">Open Settings tab</td></tr>
<tr><td style="padding: 4px;"><b>Alt+F4 / Ctrl+Q</b></td><td style="padding: 4px;">Quit application</td></tr>
<tr><td style="padding: 4px;"><b>F5</b></td><td style="padding: 4px;">Refresh current view</td></tr>
</table>
        """
        shortcuts_text.setHtml(shortcuts_content)
        shortcuts_layout.addWidget(shortcuts_text)
        
        # Getting Started Tab
        guide_tab = QWidget()
        guide_layout = QVBoxLayout(guide_tab)
        
        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_content = """
<h3 style="color: #4682b4;">Getting Started Guide</h3>

<h4 style="color: #87ceeb;">First Time Setup:</h4>
<ol style="color: white;">
<li><b>Add Your Movie Folders:</b>
   <ul>
   <li>Go to the "Settings" tab</li>
   <li>Click "Add Folder..." to add your movie directories</li>
   <li>You can add multiple folders from different drives</li>
   </ul>
</li>

<li><b>Scan Your Library:</b>
   <ul>
   <li>Click "Rescan All" to index your movies</li>
   <li>The app will scan files, extract metadata, and generate posters</li>
   <li>This may take a few minutes for large libraries</li>
   </ul>
</li>

<li><b>Install FFmpeg (Recommended):</b>
   <ul>
   <li>Download FFmpeg from <a href="https://ffmpeg.org/download.html">ffmpeg.org</a></li>
   <li>Add it to your system PATH</li>
   <li>Restart KnotzFLix to enable real poster generation</li>
   <li>Without FFmpeg, placeholder images will be used</li>
   </ul>
</li>
</ol>

<h4 style="color: #87ceeb;">Using the Library:</h4>

<p><b>Library Tab:</b> Browse all your movies in a grid view</p>
<p><b>Recently Added:</b> See your newest additions</p>
<p><b>By Folder:</b> Browse movies organized by their source folders</p>
<p><b>Continue Watching:</b> Resume movies you've started watching</p>
<p><b>Private:</b> Password-protected movies (set up in Settings)</p>

<h4 style="color: #87ceeb;">Search Features:</h4>
<ul style="color: white;">
<li><b>Instant Search:</b> Type anywhere to search instantly</li>
<li><b>Full-Text Search:</b> Searches titles, alternative titles, and metadata</li>
<li><b>Smart Results:</b> Automatically handles typos and partial matches</li>
</ul>

<h4 style="color: #87ceeb;">Privacy Features:</h4>
<ol style="color: white;">
<li><b>Set Private Code:</b> Go to Settings and click "Set Private Code"</li>
<li><b>Add Private Folders:</b> Use "Add Private Folder" or "Mark Selected Private"</li>
<li><b>Lock/Unlock:</b> Use "Lock Private" and "Unlock Private" buttons</li>
<li>When locked, private movies are hidden from all views</li>
</ol>

<h4 style="color: #87ceeb;">Tips & Tricks:</h4>
<ul style="color: white;">
<li><b>Context Menus:</b> Right-click movies for quick actions</li>
<li><b>Batch Operations:</b> Use "Mark Selected Private/Public" for multiple movies</li>
<li><b>Missing Files:</b> Use "Locate Missing" if files are moved</li>
<li><b>Poster Issues:</b> Click "Validate Posters" to regenerate them</li>
<li><b>Performance:</b> The app watches for file changes automatically</li>
</ul>
        """
        guide_text.setHtml(guide_content)
        guide_layout.addWidget(guide_text)
        
        # Troubleshooting Tab
        troubleshoot_tab = QWidget()
        troubleshoot_layout = QVBoxLayout(troubleshoot_tab)
        
        troubleshoot_text = QTextEdit()
        troubleshoot_text.setReadOnly(True)
        troubleshoot_content = """
<h3 style="color: #4682b4;">Troubleshooting Guide</h3>

<h4 style="color: #87ceeb;">Common Issues:</h4>

<p><b style="color: #ffcc00;">Posters are blank or white boxes:</b></p>
<ul style="color: white;">
<li>Install FFmpeg and make sure it's in your system PATH</li>
<li>Restart KnotzFLix after installing FFmpeg</li>
<li>Click "Validate Posters" in Settings to regenerate them</li>
<li>Check the ffmpeg status indicator in Settings</li>
</ul>

<p><b style="color: #ffcc00;">Movies not appearing after adding folder:</b></p>
<ul style="color: white;">
<li>Make sure the folder contains video files (.mp4, .avi, .mkv, etc.)</li>
<li>Click "Rescan All" or "Rescan Selected" to refresh</li>
<li>Check if files are being ignored by ignore rules</li>
<li>Verify folder permissions are correct</li>
</ul>

<p><b style="color: #ffcc00;">Search not finding movies:</b></p>
<ul style="color: white;">
<li>Try different search terms or partial titles</li>
<li>The search indexes titles and metadata, not file names</li>
<li>Rescan the library to rebuild the search index</li>
<li>Check if movies are in private folders while locked</li>
</ul>

<p><b style="color: #ffcc00;">Can't play movies:</b></p>
<ul style="color: white;">
<li>Make sure you have a video player installed (VLC recommended)</li>
<li>Check if the file still exists at the original location</li>
<li>Use "Locate Missing" if files were moved</li>
<li>Try "Open Containing Folder" to verify file location</li>
</ul>

<p><b style="color: #ffcc00;">Private folder issues:</b></p>
<ul style="color: white;">
<li>Make sure you've set a private code first</li>
<li>Private movies are hidden when locked - this is normal</li>
<li>Use "Unlock Private" to see private movies</li>
<li>Minimum password length is 8 characters</li>
</ul>

<h4 style="color: #87ceeb;">Performance Tips:</h4>
<ul style="color: white;">
<li>Store database on SSD for best performance</li>
<li>Large libraries (10k+ movies) may take time to scan initially</li>
<li>Disable file system watching if experiencing high CPU usage</li>
<li>Use "Rescan Selected" for single folders instead of "Rescan All"</li>
</ul>

<h4 style="color: #87ceeb;">Data Locations:</h4>
<ul style="color: white;">
<li><b>Database:</b> Stored in OS user data directory</li>
<li><b>Posters:</b> Content-addressed cache in user data directory</li>
<li><b>Settings:</b> settings.json in user data directory</li>
<li><b>Logs:</b> knotzflix.log in logs subdirectory</li>
</ul>

<h4 style="color: #87ceeb;">Getting Help:</h4>
<p style="color: white;">
If you continue to experience issues:
<ol>
<li>Check the application logs in the data directory</li>
<li>Try restarting the application</li>
<li>Verify system requirements are met</li>
<li>Visit our website or documentation for additional support</li>
</ol>
</p>
        """
        troubleshoot_text.setHtml(troubleshoot_content)
        troubleshoot_layout.addWidget(troubleshoot_text)
        
        # Add tabs
        tabs.addTab(shortcuts_tab, "Keyboard Shortcuts")
        tabs.addTab(guide_tab, "Getting Started")
        tabs.addTab(troubleshoot_tab, "Troubleshooting")
        
        layout.addWidget(tabs)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        # Set default tab
        tabs.setCurrentIndex(0)