from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from infra.db import Database
from infra import playback


class DetailsDialog(QDialog):
    def __init__(self, db: Database, movie_id: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.movie_id = movie_id
        self.setWindowTitle("Details")

        m = db.get_movie(movie_id)
        imgs = db.get_images_for_movie(movie_id, kind="poster")
        files = db.get_media_files_for_movie(movie_id)
        poster_path = imgs[0].path if imgs else None

        # Poster and title row
        poster = QLabel()
        poster.setFixedSize(QSize(240, 360))
        if poster_path:
            pix = QPixmap(poster_path)
            if not pix.isNull():
                poster.setPixmap(pix.scaled(poster.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))

        title_lbl = QLabel()
        if m:
            y = f" ({m.year})" if m.year else ""
            title_lbl.setText(f"<b>{m.canonical_title}</b>{y}")
        else:
            title_lbl.setText("<b>Unknown</b>")

        # Badges row
        badges = []
        if files:
            f = files[0]
            if f.width and f.height:
                badges.append(f"{f.width}x{f.height}")
            if f.video_codec:
                badges.append(f.video_codec)
            if f.audio_channels:
                badges.append(f"{f.audio_channels}ch")
        if m and m.runtime_sec:
            badges.append(f"{m.runtime_sec//60} min")

        badges_lbl = QLabel(" ".join(f"<span style='background:#eee;padding:2px 6px;border-radius:4px'>{b}</span>" for b in badges))

        # Buttons
        play_btn = QPushButton("Play")
        open_btn = QPushButton("Open Folder")

        play_btn.clicked.connect(self._play)
        open_btn.clicked.connect(self._open)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject)

        left = QVBoxLayout(); left.addWidget(title_lbl); left.addWidget(badges_lbl); left.addStretch(1); left.addWidget(play_btn); left.addWidget(open_btn)
        top = QHBoxLayout(); top.addWidget(poster); top.addLayout(left)

        lay = QVBoxLayout(); lay.addLayout(top); lay.addStretch(1); lay.addWidget(bb)
        self.setLayout(lay)

    def _primary_file(self) -> Optional[Path]:
        files = self.db.get_media_files_for_movie(self.movie_id)
        if not files:
            return None
        return Path(files[0].path)

    def _play(self) -> None:
        p = self._primary_file()
        if p and p.exists():
            playback.launch_external(p)

    def _open(self) -> None:
        p = self._primary_file()
        if p:
            playback.open_containing_folder(p)

