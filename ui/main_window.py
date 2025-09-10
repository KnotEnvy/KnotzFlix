from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from infra import library_service
from infra.config import AppConfig, load_config, save_config
from infra.db import Database
from infra import watcher as fs_watcher
from infra import thumbnails


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

            # Tabs: Library + Recently Added + By Folder + Private + Settings
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

            # Private tab (locked by default)
            self._private_unlocked: bool = False
            self._private_ids: list[int] = []
            self.private_grid = PosterGrid(self.db, order_mode="default", id_allowlist=[])
            self._private_tab_index = self.tabs.addTab(self.private_grid, "Private")

            # Keep Continue Watching shelf fresh when a movie is played
            def _update_continue_shelf(_mid: int) -> None:
                try:
                    ids = self.db.get_continue_watching_ids()
                    self.continue_grid.model.set_id_allowlist(ids)
                    self.continue_grid.refresh()
                except Exception:
                    pass

            self.grid.played.connect(_update_continue_shelf)
            self.recent.played.connect(_update_continue_shelf)
            try:
                self.by_folder.grid.played.connect(_update_continue_shelf)
            except Exception:
                pass

            # Settings tab
            self.roots_list = QListWidget()
            self._refresh_roots()
            add_btn = QPushButton("Add Folder…"); add_btn.clicked.connect(self.add_folder)
            add_priv_btn = QPushButton("Add Private Folder…"); add_priv_btn.clicked.connect(self.add_private_folder)
            remove_btn = QPushButton("Remove Selected"); remove_btn.clicked.connect(self.remove_selected_root)
            mark_priv_btn = QPushButton("Mark Selected Private"); mark_priv_btn.clicked.connect(self.mark_selected_private)
            mark_pub_btn = QPushButton("Mark Selected Public"); mark_pub_btn.clicked.connect(self.mark_selected_public)
            rescan_btn = QPushButton("Rescan All"); rescan_btn.clicked.connect(self.rescan)
            rescan_sel_btn = QPushButton("Rescan Selected"); rescan_sel_btn.clicked.connect(self.rescan_selected)
            validate_btn = QPushButton("Validate Posters"); validate_btn.clicked.connect(self.validate_posters)

            # Status row (ffmpeg)
            from PyQt6.QtWidgets import QLabel
            self.ffmpeg_lbl = QLabel()
            self._refresh_ffmpeg_status()

            # Private access controls
            set_code_btn = QPushButton("Set Private Code…"); set_code_btn.clicked.connect(self.set_private_code)
            unlock_btn = QPushButton("Unlock Private…"); unlock_btn.clicked.connect(self.unlock_private)
            lock_btn = QPushButton("Lock Private"); lock_btn.clicked.connect(self.lock_private)

            btn_row = QHBoxLayout();
            btn_row.addWidget(add_btn); btn_row.addWidget(add_priv_btn); btn_row.addWidget(remove_btn)
            btn_row.addWidget(mark_priv_btn); btn_row.addWidget(mark_pub_btn)
            btn_row.addWidget(rescan_btn); btn_row.addWidget(rescan_sel_btn); btn_row.addWidget(validate_btn); btn_row.addStretch(1)
            priv_row = QHBoxLayout(); priv_row.addWidget(set_code_btn); priv_row.addWidget(unlock_btn); priv_row.addWidget(lock_btn); priv_row.addStretch(1)
            status_row = QHBoxLayout(); status_row.addWidget(QLabel("ffmpeg:")); status_row.addWidget(self.ffmpeg_lbl); status_row.addStretch(1)

            settings_layout = QVBoxLayout(); settings_layout.addWidget(self.roots_list); settings_layout.addLayout(btn_row); settings_layout.addLayout(priv_row); settings_layout.addLayout(status_row)
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

            # Optional native FS watchers (watchdog) with debounce per-root
            self._watch_handles = None
            self._debounce: dict[str, QTimer] = {}

            def _on_native_change(root_path: Path) -> None:
                key = str(root_path)
                t = self._debounce.get(key)
                if t is None:
                    t = QTimer(self)
                    t.setSingleShot(True)
                    t.setInterval(1500)
                    t.timeout.connect(lambda rp=root_path: self._rescan_root_debounced(rp))
                    self._debounce[key] = t
                t.start()

            try:
                self._watch_handles = fs_watcher.start_watchers([Path(p) for p in self.cfg.library_roots], _on_native_change)
            except Exception:
                self._watch_handles = None

            # Initialize private filters and tab state
            self._refresh_private_filters()

        def _refresh_roots(self) -> None:
            self.roots_list.clear()
            for r in self.cfg.library_roots:
                self.roots_list.addItem(r)
            # keep By Folder list in sync
            try:
                self.by_folder.folders.clear()
                self.by_folder.folders.addItem("All")
                for r in self.cfg.library_roots:
                    # Hide private roots when locked
                    if (not self._private_unlocked) and (r in set(self.cfg.private_roots)):
                        continue
                    self.by_folder.folders.addItem(r)
                self.by_folder.folders.setCurrentRow(0)
            except Exception:
                pass
            # Update private ids when roots change
            self._refresh_private_filters()

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

        def add_private_folder(self) -> None:
            folder = QFileDialog.getExistingDirectory(self, "Select Private Folder")
            if not folder:
                return
            if folder not in self.cfg.library_roots:
                self.cfg.library_roots.append(folder)
            if folder not in self.cfg.private_roots:
                self.cfg.private_roots.append(folder)
            save_config(self.cfg)
            self._refresh_roots()

        def remove_selected_root(self) -> None:
            row = self.roots_list.currentRow()
            if row < 0:
                QMessageBox.information(self, "KnotzFLix", "Select a folder to remove.")
                return
            try:
                path = self.cfg.library_roots.pop(row)
                try:
                    self.cfg.private_roots.remove(path)
                except ValueError:
                    pass
            except Exception:
                return
            save_config(self.cfg)
            self._refresh_roots()

        def mark_selected_private(self) -> None:
            row = self.roots_list.currentRow()
            if row < 0:
                QMessageBox.information(self, "KnotzFLix", "Select a folder to mark private.")
                return
            path = self.roots_list.item(row).text()
            if path not in self.cfg.private_roots:
                self.cfg.private_roots.append(path)
                save_config(self.cfg)
                self._refresh_roots()

        def mark_selected_public(self) -> None:
            row = self.roots_list.currentRow()
            if row < 0:
                QMessageBox.information(self, "KnotzFLix", "Select a folder to mark public.")
                return
            path = self.roots_list.item(row).text()
            try:
                self.cfg.private_roots.remove(path)
            except ValueError:
                pass
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
                # Update private filters post-scan
                self._refresh_private_filters()
                # refresh continue watching allowlist
                try:
                    ids = self.db.get_continue_watching_ids()
                    self.continue_grid.model.set_id_allowlist(ids)
                    self.continue_grid.refresh()
                except Exception:
                    pass
                # refresh ffmpeg status (could have been installed during runtime)
                self._refresh_ffmpeg_status()
            except Exception:
                pass

        # Private helpers
        def _hash_private_code(self, code: str) -> str:
            import hashlib
            # Use a short person string (<=16 bytes) for domain separation
            h = hashlib.blake2b(code.encode("utf-8"), digest_size=32, person=b"knotzflix-priv")
            return h.hexdigest()

        def set_private_code(self) -> None:
            from PyQt6.QtWidgets import QInputDialog
            code, ok = QInputDialog.getText(self, "Set Private Code", "Enter new code:")
            if not ok or not code:
                return
            code2, ok2 = QInputDialog.getText(self, "Confirm Private Code", "Re-enter code:")
            if not ok2 or code2 != code:
                QMessageBox.warning(self, "KnotzFLix", "Codes do not match.")
                return
            self.cfg.private_code_hash = self._hash_private_code(code)
            save_config(self.cfg)
            QMessageBox.information(self, "KnotzFLix", "Private code updated.")

        def unlock_private(self) -> None:
            if not self.cfg.private_code_hash:
                QMessageBox.information(self, "KnotzFLix", "Set a private code first.")
                return
            from PyQt6.QtWidgets import QInputDialog
            code, ok = QInputDialog.getText(self, "Unlock Private", "Enter private code:")
            if not ok:
                return
            if self._hash_private_code(code) == self.cfg.private_code_hash:
                self._private_unlocked = True
                self._refresh_private_filters()
                QMessageBox.information(self, "KnotzFLix", "Private unlocked.")
            else:
                QMessageBox.warning(self, "KnotzFLix", "Incorrect code.")

        def lock_private(self) -> None:
            self._private_unlocked = False
            self._refresh_private_filters()
            QMessageBox.information(self, "KnotzFLix", "Private locked.")

        def _compute_private_ids(self) -> list[int]:
            ids: set[int] = set()
            for r in self.cfg.private_roots:
                try:
                    for mid in self.db.get_movie_ids_by_path_prefix(r):
                        ids.add(int(mid))
                except Exception:
                    pass
            return sorted(ids)

        def _refresh_private_filters(self) -> None:
            # Recompute private ids
            self._private_ids = self._compute_private_ids()
            # Update Private tab allowlist if unlocked
            if self._private_unlocked:
                self.private_grid.model.set_id_allowlist(self._private_ids)
            else:
                self.private_grid.model.set_id_allowlist([])
            self.private_grid.refresh()
            # Exclude private ids from main grids when locked
            exclude = [] if self._private_unlocked else self._private_ids
            try:
                self.grid.model.set_id_blocklist(exclude)
                self.grid.refresh()
            except Exception:
                pass
            try:
                self.recent.model.set_id_blocklist(exclude)
                self.recent.refresh()
            except Exception:
                pass
            # Update Private tab UI cues
            try:
                if self._private_unlocked:
                    self.tabs.setTabText(self._private_tab_index, "Private")
                    self.private_grid.set_empty_message("No private movies yet.")
                else:
                    self.tabs.setTabText(self._private_tab_index, "Private 🔒")
                    self.private_grid.set_empty_message("🔒 Private library is locked. Unlock in Settings.")
            except Exception:
                pass

        def closeEvent(self, event) -> None:  # type: ignore[override]
            try:
                if getattr(self, "_watch_handles", None):
                    try:
                        self._watch_handles.stop()
                    except Exception:
                        pass
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

        def _rescan_root_debounced(self, root: Path) -> None:
            if self._scan_thread is not None and self._scan_thread.isRunning():  # type: ignore[union-attr]
                return
            worker = ScanWorker(self.db, [root], self.cfg.ignore_rules, self.cfg.concurrency, True)
            worker.signals.progress.connect(lambda d, t: None)
            worker.signals.finished.connect(lambda _s: self._on_scan_finished(_s))
            self._scan_thread = worker
            worker.start()

        # Posters validation
        def _refresh_ffmpeg_status(self) -> None:
            ok, ver = thumbnails.ffmpeg_status()
            self.ffmpeg_lbl.setText(ver if ok else "Not Found")

        def validate_posters(self) -> None:
            # Kick off background validator
            PosterFixWorker = _make_poster_fix_worker_class()
            worker = PosterFixWorker()
            worker.signals.progress.connect(self._on_progress)
            def _after(_summary: object) -> None:
                self._on_scan_finished(_summary)
            worker.signals.finished.connect(_after)
            self.progress.setVisible(True); self.progress.setValue(0)
            worker.start()

    # Poster fixer worker
    def _make_poster_fix_worker_class():
        from PyQt6.QtCore import QThread, QObject, pyqtSignal

        class _Signals(QObject):
            progress = pyqtSignal(int, int)
            finished = pyqtSignal(object)

        class PosterFixWorker(QThread):
            def __init__(self) -> None:
                super().__init__()
                self.signals = _Signals()

            def run(self) -> None:
                from infra.db import Database
                from infra import thumbnails, fingerprinter
                from pathlib import Path as _P

                db = Database()
                try:
                    # Load all movie ids
                    cur = db.conn.execute("SELECT id, runtime_sec FROM movie ORDER BY id")
                    rows = cur.fetchall()
                    total = len(rows)
                    fixed = 0
                    for i, row in enumerate(rows, start=1):
                        mid = int(row[0])
                        runtime = row[1]
                        # get current poster
                        imgs = db.get_images_for_movie(mid, kind="poster")
                        img = imgs[0] if imgs else None
                        # get primary media file
                        mfiles = db.get_media_files_for_movie(mid)
                        if not mfiles:
                            self.signals.progress.emit(i, total)
                            continue
                        mf = mfiles[0]
                        # compute fingerprint if missing
                        fp = mf.fingerprint
                        if not fp:
                            try:
                                fp = fingerprinter.fingerprint_partial(_P(mf.path))
                            except Exception:
                                fp = None
                        if not fp:
                            self.signals.progress.emit(i, total)
                            continue

                        # Decide if needs regen
                        needs_regen = False
                        if img is None:
                            needs_regen = True
                        else:
                            try:
                                p = _P(img.path)
                                if (not p.exists()) or (p.stat().st_size < 2048) or ((img.src or "") == "placeholder"):
                                    needs_regen = True
                            except Exception:
                                needs_regen = True

                        if needs_regen:
                            out, _ = thumbnails.generate_poster(_P(mf.path), file_fingerprint=fp, duration_sec=float(runtime) if runtime else None, dry_run=False, force=True)
                            try:
                                from infra.thumbnails import detect_poster_source
                                src = detect_poster_source(out)
                            except Exception:
                                src = "ffmpeg" if out.exists() else "placeholder"
                            if img is None:
                                from domain.models import Image
                                db.add_image(Image(id=None, movie_id=mid, kind='poster', path=str(out), src=src))
                            else:
                                img.path = str(out)
                                img.src = src
                                db.add_image(img)
                            fixed += 1
                        self.signals.progress.emit(i, total)
                    self.signals.finished.emit({"total": total, "fixed": fixed})
                finally:
                    db.close()

        return PosterFixWorker

    return MainWindow()
