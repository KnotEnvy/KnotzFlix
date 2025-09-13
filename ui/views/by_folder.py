from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QListWidget, QSplitter, QWidget

from infra.db import Database
from ui.views.poster_grid import PosterGrid


class ByFolderView(QWidget):
    def __init__(self, db: Database, roots: list[str]):
        super().__init__()
        self.db = db
        self.roots = roots

        self.split = QSplitter()
        self.folders = QListWidget()
        self.folders.addItem("All")
        for r in roots:
            self.folders.addItem(r)
        self.folders.setCurrentRow(0)

        self.grid = PosterGrid(db)

        self.split.addWidget(self.folders)
        self.split.addWidget(self.grid)
        self.split.setStretchFactor(1, 1)

        lay = QHBoxLayout(); lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.split)
        self.setLayout(lay)

        self.folders.currentRowChanged.connect(self._on_folder_changed)

    def _on_folder_changed(self, row: int) -> None:
        if row <= 0:
            self.grid.model.set_path_prefix(None)
        else:
            prefix = self.folders.item(row).text()
            self.grid.model.set_path_prefix(prefix)
        self.grid.refresh()

