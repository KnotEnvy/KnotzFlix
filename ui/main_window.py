from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from infra import library_service
from infra.config import AppConfig, load_config, save_config
from infra.db import Database


def _qt_imports():
    from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
    from PyQt6.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QListWidget,
        QPushButton,
        QFileDialog,
        QStatusBar,
        QProgressBar,
        QMessageBox,
    )
    return Qt, QObject, QThread, pyqtSignal, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QFileDialog, QStatusBar, QProgressBar, QMessageBox


class ScanWorkerSignals:
    def __init__(self, pyqtSignal):
        self.progress = pyqtSignal(int, int)  # processed, total
        self.finished = pyqtSignal(object)  # summary


def _make_scan_worker_class():
    Qt, QObject, QThread, pyqtSignal, *_ = _qt_imports()

    class _Signals(QObject):
        progress = pyqtSignal(int, int)
        finished = pyqtSignal(object)

    class ScanWorker(QThread):
        def __init__(self, db: Database, roots: list[Path], ignore_rules: list[str], concurrency: int, do_fingerprint: bool) -> None:
            super().__init__()
            self.db = db
            self.roots = roots
            self.ignore_rules = ignore_rules
            self.concurrency = concurrency
            self.do_fingerprint = do_fingerprint
            self.signals = _Signals()

        def run(self) -> None:
            # Use a thread-local DB connection to avoid cross-thread sqlite usage.
            local_db = Database()
            try:
                summary = library_service.scan_and_index(
                    db=local_db,
                    roots=self.roots,
                    ignore_rules=self.ignore_rules,
                    concurrency=self.concurrency,
                    do_fingerprint=self.do_fingerprint,
                    progress=lambda d, t: self.signals.progress.emit(d, t),
                )
                self.signals.finished.emit(summary)
            finally:
                try:
                    local_db.close()
                except Exception:
                    pass

    return ScanWorker


def create_main_window() -> "QMainWindow":
    (
        Qt,
        QObject,
        QThread,
        pyqtSignal,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QListWidget,
        QPushButton,
        QFileDialog,
        QStatusBar,
        QProgressBar,
        QMessageBox,
    ) = _qt_imports()

    ScanWorker = _make_scan_worker_class()

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("KnotzFLix")
            self.resize(900, 600)

            self.cfg: AppConfig = load_config()
            self.db = Database(); self.db.initialize()

            # Tabs: Library + Recently Added + By Folder + Settings
            from PyQt6.QtWidgets import QTabWidget
            from ui.views.poster_grid import PosterGrid
            from ui.views.by_folder import ByFolderView

            self.tabs = QTabWidget()
            # Library tab
            self.grid = PosterGrid(self.db)
            self.tabs.addTab(self.grid, "Library")
            # Recently Added tab
            self.recent = PosterGrid(self.db, order_mode="recent")
            self.tabs.addTab(self.recent, "Recently Added")
            # By Folder tab
            self.by_folder = ByFolderView(self.db, self.cfg.library_roots[:])
            self.tabs.addTab(self.by_folder, "By Folder")
            # Continue Watching tab
            from PyQt6.QtWidgets import QWidget
            self.continue_grid = PosterGrid(self.db, order_mode="default", id_allowlist=self.db.get_continue_watching_ids())
            self.tabs.addTab(self.continue_grid, "Continue Watching")

            # Settings tab
            self.roots_list = QListWidget()
            self._refresh_roots()
            add_btn = QPushButton("Add Folder…"); add_btn.clicked.connect(self.add_folder)
            remove_btn = QPushButton("Remove Selected"); remove_btn.clicked.connect(self.remove_selected_root)
            rescan_btn = QPushButton("Rescan All"); rescan_btn.clicked.connect(self.rescan)
            rescan_sel_btn = QPushButton("Rescan Selected"); rescan_sel_btn.clicked.connect(self.rescan_selected)
            btn_row = QHBoxLayout(); btn_row.addWidget(add_btn); btn_row.addWidget(remove_btn); btn_row.addWidget(rescan_btn); btn_row.addWidget(rescan_sel_btn); btn_row.addStretch(1)
            settings_layout = QVBoxLayout(); settings_layout.addWidget(self.roots_list); settings_layout.addLayout(btn_row)
            settings_page = QWidget(); settings_page.setLayout(settings_layout)
            self.tabs.addTab(settings_page, "Settings")

            self.setCentralWidget(self.tabs)

            sb = QStatusBar(); self.setStatusBar(sb)
            self.progress = QProgressBar(); self.progress.setRange(0, 100)
            self.progress.setValue(0); self.progress.setVisible(False)
            sb.addPermanentWidget(self.progress)

            self._scan_thread: Optional[QThread] = None
            # Simple polling watcher: rescan roots periodically (lightweight approach)
            from PyQt6.QtCore import QTimer
            self._watch_timer = QTimer(self)
            self._watch_timer.setInterval(120_000)  # 2 minutes
            self._watch_timer.timeout.connect(self._on_watch_tick)
            self._watch_timer.start()

        def _refresh_roots(self) -> None:
            self.roots_list.clear()
            for r in self.cfg.library_roots:
                self.roots_list.addItem(r)
            # keep By Folder list in sync
            try:
                self.by_folder.folders.clear()
                self.by_folder.folders.addItem("All")
                for r in self.cfg.library_roots:
                    self.by_folder.folders.addItem(r)
                self.by_folder.folders.setCurrentRow(0)
            except Exception:
                pass

        def add_folder(self) -> None:
            folder = QFileDialog.getExistingDirectory(self, "Select Movie Folder")
            if not folder:
                return
            if folder not in self.cfg.library_roots:
                self.cfg.library_roots.append(folder)
                save_config(self.cfg)
                self._refresh_roots()
            else:
                QMessageBox.information(self, "KnotzFLix", "Folder already added.")

        def remove_selected_root(self) -> None:
            row = self.roots_list.currentRow()
            if row < 0:
                QMessageBox.information(self, "KnotzFLix", "Select a folder to remove.")
                return
            try:
                self.cfg.library_roots.pop(row)
            except Exception:
                return
            save_config(self.cfg)
            self._refresh_roots()

        def rescan(self) -> None:
            if not self.cfg.library_roots:
                QMessageBox.warning(self, "KnotzFLix", "No library folders added.")
                return
            self.progress.setVisible(True); self.progress.setValue(0)
            roots = [Path(p) for p in self.cfg.library_roots]
            worker = ScanWorker(self.db, roots, self.cfg.ignore_rules, self.cfg.concurrency, True)
            worker.signals.progress.connect(self._on_progress)
            worker.signals.finished.connect(self._on_scan_finished)
            self._scan_thread = worker
            worker.start()

        def rescan_selected(self) -> None:
            row = self.roots_list.currentRow()
            if row < 0:
                QMessageBox.information(self, "KnotzFLix", "Select a folder to rescan.")
                return
            root = self.cfg.library_roots[row]
            self.progress.setVisible(True); self.progress.setValue(0)
            worker = ScanWorker(self.db, [Path(root)], self.cfg.ignore_rules, self.cfg.concurrency, True)
            worker.signals.progress.connect(self._on_progress)
            worker.signals.finished.connect(self._on_scan_finished)
            self._scan_thread = worker
            worker.start()

        def _on_progress(self, done: int, total: int) -> None:
            val = int((done / total) * 100) if total else 0
            self.progress.setValue(val)

        def _on_scan_finished(self, summary) -> None:
            self.statusBar().showMessage(
                f"Scanned {summary.total_files} files | New movies: {summary.new_movies} | New files: {summary.new_files} | Duplicates: {summary.duplicates}",
                5000,
            )
            self.progress.setVisible(False)
            # Refresh library grid
            try:
                self.grid.refresh()
                self.recent.refresh()
                # by_folder grid refreshes via same model
                self.by_folder.grid.refresh()
                # refresh continue watching allowlist
                try:
                    ids = self.db.get_continue_watching_ids()
                    self.continue_grid.model.set_id_allowlist(ids)
                    self.continue_grid.refresh()
                except Exception:
                    pass
            except Exception:
                pass

        def closeEvent(self, event) -> None:  # type: ignore[override]
            try:
                self.db.close()
            finally:
                super().closeEvent(event)

        def _on_watch_tick(self) -> None:
            # Skip if a scan is running or no roots
            if self._scan_thread is not None and self._scan_thread.isRunning():  # type: ignore[union-attr]
                return
            if not self.cfg.library_roots:
                return
            # Trigger a quick background rescan of all roots
            roots = [Path(p) for p in self.cfg.library_roots]
            worker = ScanWorker(self.db, roots, self.cfg.ignore_rules, self.cfg.concurrency, True)
            worker.signals.progress.connect(lambda d, t: None)
            worker.signals.finished.connect(lambda _s: self._on_scan_finished(_s))
            self._scan_thread = worker
            worker.start()

    return MainWindow()
