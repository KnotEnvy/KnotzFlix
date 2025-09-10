from __future__ import annotations

from PyQt6.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFontMetrics, QPixmap
from PyQt6.QtWidgets import QListView, QWidget, QVBoxLayout, QStyledItemDelegate, QStyleOptionViewItem, QStyle, QLineEdit, QMenu, QMessageBox, QFileDialog

from infra.db import Database
from domain.models import PlayState
from ui.models.movie_list_model import MovieListModel, Roles
from ui.views.details_dialog import DetailsDialog
from infra import playback
from ui.widgets.toast import show_toast


class PosterTileDelegate(QStyledItemDelegate):
    def __init__(self, parent: QListView, tile_width: int = 180, ratio_w: int = 2, ratio_h: int = 3):
        super().__init__(parent)
        self.parent_view = parent
        self.tile_width = tile_width
        self.ratio_w = ratio_w
        self.ratio_h = ratio_h
        self._scaled_cache: dict[tuple[str, int, int], QPixmap] = {}

    def tile_size(self) -> QSize:
        h = int(self.tile_width * self.ratio_h / self.ratio_w)
        # Extra space for text overlay (we draw over image, so height is just poster)
        return QSize(self.tile_width, h)

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:  # type: ignore[override]
        return self.tile_size()

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # type: ignore[override]
        rect: QRect = option.rect
        painter.save()
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform, True)

        # Tile geometry
        poster_rect = QRect(rect.left(), rect.top(), rect.width(), rect.height())
        radius = 8

        # Background (for empty/placeholder)
        bg = QColor(28, 28, 28) if option.palette.color(option.palette.ColorRole.Base).lightness() < 128 else QColor(240, 240, 240)
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(poster_rect, radius, radius)

        # Poster image (with fallback to placeholder when loading fails)
        path = index.data(Roles.PosterPathRole)
        is_placeholder = bool(index.data(Roles.PosterIsPlaceholderRole))
        drew_image = False
        if isinstance(path, str) and path and not is_placeholder:
            key = (path, poster_rect.width(), poster_rect.height())
            pix = self._scaled_cache.get(key)
            if pix is None:
                src = QPixmap(path)
                if not src.isNull() and (src.width() > 2 and src.height() > 2):
                    # Scale preserving aspect ratio and center crop to fill tile
                    scaled = src.scaled(poster_rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    pix = scaled
                    self._scaled_cache[key] = pix
            if pix and not pix.isNull():
                # Center crop draw
                sx = max(0, (pix.width() - poster_rect.width()) // 2)
                sy = max(0, (pix.height() - poster_rect.height()) // 2)
                painter.setClipRect(poster_rect)
                painter.drawPixmap(poster_rect.topLeft(), pix, QRect(sx, sy, poster_rect.width(), poster_rect.height()))
                painter.setClipping(False)
                drew_image = True
        if not drew_image:
            # Placeholder tile when no poster or failed decode
            ph = QColor(70, 70, 70)
            painter.setBrush(QBrush(ph))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(poster_rect, radius, radius)
            # Simple centered label
            painter.setPen(QColor(200, 200, 200))
            from PyQt6.QtGui import QFont
            f = painter.font()
            f.setPointSizeF(max(9.0, f.pointSizeF()))
            painter.setFont(f)
            label = "No Poster"
            fm = QFontMetrics(f)
            tw = fm.horizontalAdvance(label)
            th = fm.height()
            tx = poster_rect.left() + (poster_rect.width() - tw) // 2
            ty = poster_rect.top() + (poster_rect.height() + th) // 2 - fm.descent()
            painter.drawText(QPoint(tx, ty), label)

        # Bottom gradient overlay for text
        grad_h = min(56, poster_rect.height() // 3)
        overlay = QRect(poster_rect.left(), poster_rect.bottom() - grad_h + 1, poster_rect.width(), grad_h)
        g1 = QColor(0, 0, 0, 180)
        g2 = QColor(0, 0, 0, 0)
        # Use QLinearGradient for the overlay fade
        from PyQt6.QtGui import QLinearGradient

        # QLinearGradient requires QPointF or float coords; use floats.
        lg = QLinearGradient(float(overlay.left()), float(overlay.top()), float(overlay.left()), float(overlay.bottom()))
        lg.setColorAt(0.0, g2)
        lg.setColorAt(1.0, g1)
        painter.fillRect(overlay, QBrush(lg))

        # Title + year text
        title = index.data(Roles.TitleRole) or ""
        year = index.data(Roles.YearRole)
        label = f"{title} ({year})" if year else str(title)
        # Padding
        pad = 8
        text_rect = overlay.adjusted(pad, 0, -pad, -4)
        painter.setPen(QColor(255, 255, 255))
        fm = QFontMetrics(painter.font())
        elided = fm.elidedText(label, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, elided)

        # Progress badge (continue watching)
        try:
            progress = int(index.data(Roles.ProgressRole) or 0)
        except Exception:
            progress = 0
        if 0 < progress < 100:
            bar_w = max(40, poster_rect.width() // 3)
            bar_h = 8
            bx = poster_rect.right() - bar_w - 8
            by = poster_rect.top() + 8
            bgc = QColor(0, 0, 0, 140)
            fgc = QColor(66, 133, 244)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(bgc))
            painter.drawRoundedRect(QRect(bx, by, bar_w, bar_h), 4, 4)
            fill_w = int(bar_w * (progress / 100.0))
            if fill_w > 0:
                painter.setBrush(QBrush(fgc))
                painter.drawRoundedRect(QRect(bx, by, fill_w, bar_h), 4, 4)
            # percent text
            painter.setPen(QColor(255, 255, 255))
            from PyQt6.QtGui import QFont
            f = painter.font()
            f.setPointSizeF(max(7.0, f.pointSizeF() - 1))
            painter.setFont(f)
            t = f"{progress}%"
            fm2 = QFontMetrics(f)
            tw2 = fm2.horizontalAdvance(t)
            tx2 = bx + (bar_w - tw2) // 2
            ty2 = by + bar_h - 1
            painter.drawText(QRect(bx, by - 6, bar_w, bar_h + 12), Qt.AlignmentFlag.AlignCenter, t)

        # Selection or focus ring
        has_focus = bool(option.state & QStyle.StateFlag.State_HasFocus) or self.parent_view.currentIndex() == index
        is_sel = bool(option.state & QStyle.StateFlag.State_Selected)
        if is_sel or has_focus:
            pen_color = QColor(66, 133, 244) if has_focus else QColor(255, 255, 255, 180)
            pen = QPen(pen_color, 2)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawRoundedRect(poster_rect.adjusted(1, 1, -1, -1), radius, radius)

        # Hover glow
        if option.state & QStyle.StateFlag.State_MouseOver:
            painter.setBrush(QColor(255, 255, 255, 20))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(poster_rect, radius, radius)

        painter.restore()


class PosterListView(QListView):
    def keyPressEvent(self, event):  # type: ignore[override]
        key = event.key()
        if key in (Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            m = self.model()
            if not m:
                return super().keyPressEvent(event)
            count = m.rowCount()
            if count == 0:
                return super().keyPressEvent(event)
            gs = self.gridSize()
            spacing = self.spacing()
            cols = max(1, (self.viewport().width() + spacing) // (max(1, gs.width()) + spacing))
            rows = max(1, (self.viewport().height() + spacing) // (max(1, gs.height()) + spacing))
            cur = self.currentIndex().row()
            if key == Qt.Key.Key_Home:
                self.setCurrentIndex(m.index(0, 0))
                return
            if key == Qt.Key.Key_End:
                self.setCurrentIndex(m.index(count - 1, 0))
                return
            if key == Qt.Key.Key_PageDown:
                nxt = min(count - 1, cur + cols * rows)
                self.setCurrentIndex(m.index(nxt, 0))
                return
            if key == Qt.Key.Key_PageUp:
                prv = max(0, cur - cols * rows)
                self.setCurrentIndex(m.index(prv, 0))
                return
        return super().keyPressEvent(event)


class PosterGrid(QWidget):
    played = pyqtSignal(int)  # movie_id
    def __init__(self, db: Database, *, order_mode: str = "default", path_prefix: str | None = None, id_allowlist: list[int] | None = None):
        super().__init__()
        self.db = db
        self.model = MovieListModel(db, order_mode=order_mode, path_prefix=path_prefix, id_allowlist=id_allowlist)
        self.view = PosterListView()
        self.view.setModel(self.model)
        self.view.setViewMode(QListView.ViewMode.IconMode)
        self.view.setResizeMode(QListView.ResizeMode.Adjust)
        self.view.setUniformItemSizes(True)
        self.view.setWrapping(True)
        self.view.setMovement(QListView.Movement.Static)
        self.view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.view.setSelectionBehavior(QListView.SelectionBehavior.SelectItems)
        self.view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.view.setMouseTracking(True)
        self.view.setSpacing(16)
        # Performance tweaks for large lists
        self.view.setLayoutMode(QListView.LayoutMode.Batched)
        self.view.setBatchSize(256)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._on_context_menu)
        self.view.doubleClicked.connect(lambda _idx: self._show_details())
        self.view.activated.connect(lambda _idx: self._show_details())

        # Custom delegate with pretty rendering
        self._tile_width = 180
        self.delegate = PosterTileDelegate(self.view, tile_width=self._tile_width)
        self.view.setItemDelegate(self.delegate)
        self._apply_grid_size()

        # Search box for instant filtering
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search titles…")
        # Debounce search updates for snappy UI
        from PyQt6.QtCore import QTimer
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(120)
        self.search.textChanged.connect(lambda _t: self._search_timer.start())
        self._search_timer.timeout.connect(self._apply_search)

        from PyQt6.QtWidgets import QLabel
        self.empty = QLabel("No movies yet. Add folders in Settings and click Rescan.")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setVisible(False)

        lay = QVBoxLayout(); lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.search)
        lay.addWidget(self.view)
        lay.addWidget(self.empty)
        self.setLayout(lay)

        # Shortcuts: P to Play, R to Reveal
        from PyQt6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("P"), self.view, activated=self._play)
        QShortcut(QKeySequence("R"), self.view, activated=self._open_containing)
        # Mark watched/unwatched
        QShortcut(QKeySequence("W"), self.view, activated=lambda: self._set_watched(True))
        QShortcut(QKeySequence("U"), self.view, activated=lambda: self._set_watched(False))

    def refresh(self) -> None:
        self.model.refresh()
        self._update_empty_state()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        # Adjust tile width to fit an integer number of columns nicely
        self._apply_grid_size()

    def _apply_grid_size(self) -> None:
        viewport_w = max(1, self.view.viewport().width())
        spacing = self.view.spacing()
        # Aim for tile width around 200 but fit whole columns
        target = 200
        # Columns: try to maximize while keeping >= 140px tiles
        for cols in range(12, 0, -1):
            total_spacing = spacing * (cols + 1)
            avail = viewport_w - total_spacing
            if avail <= 0:
                continue
            w = avail // cols
            if w >= 140:
                self._tile_width = min(max(w, 140), 260)
                break
        else:
            self._tile_width = 160
        self.delegate.tile_width = self._tile_width
        size = self.delegate.tile_size()
        # Grid size defines item rect; add slight padding to avoid clipping focus ring
        self.view.setGridSize(QSize(size.width(), size.height()))

    def _apply_search(self) -> None:
        text = self.search.text()
        self.model.set_filter_query(text)
        self._update_empty_state()

    def _update_empty_state(self) -> None:
        has_items = self.model.rowCount() > 0
        self.view.setVisible(has_items)
        self.empty.setVisible(not has_items)

    # UI helpers
    def set_empty_message(self, text: str) -> None:
        try:
            self.empty.setText(text)
        except Exception:
            pass

    # Actions
    def _current_movie_id(self) -> int | None:
        idx = self.view.currentIndex()
        if not idx.isValid():
            return None
        return idx.data(Roles.IdRole)

    def _primary_file_path(self) -> str | None:
        mid = self._current_movie_id()
        if mid is None:
            return None
        files = self.db.get_media_files_for_movie(int(mid))
        return files[0].path if files else None

    def _on_context_menu(self, pos) -> None:
        idx = self.view.indexAt(pos)
        if not idx.isValid():
            return
        self.view.setCurrentIndex(idx)
        menu = QMenu(self)
        play_act = menu.addAction("Play")
        open_act = menu.addAction("Open Containing Folder")
        det_act = menu.addAction("Details…")
        loc_act = menu.addAction("Locate Missing…")
        menu.addSeparator()
        mark_w = menu.addAction("Mark as Watched")
        mark_uw = menu.addAction("Mark as Unwatched")
        reset_prog = menu.addAction("Reset Progress")
        act = menu.exec(self.view.viewport().mapToGlobal(pos))
        if act == play_act:
            self._play()
        elif act == open_act:
            self._open_containing()
        elif act == det_act:
            self._show_details()
        elif act == loc_act:
            self._locate_missing()
        elif act == mark_w:
            self._set_watched(True)
        elif act == mark_uw:
            self._set_watched(False)
        elif act == reset_prog:
            self._reset_progress()

    def _play(self) -> None:
        p = self._primary_file_path()
        if not p:
            show_toast(self, "No file linked to this movie.")
            return
        from pathlib import Path as _P
        playback.launch_external(_P(p))
        # Seed Continue Watching with a small non-zero position for immediate visibility
        mid = self._current_movie_id()
        if mid is not None:
            try:
                self.db.set_play_state(PlayState(movie_id=int(mid), position_sec=60, watched=False))
            except Exception:
                pass
            # Notify listeners (e.g., MainWindow) to refresh shelves
            self.played.emit(int(mid))

    def _open_containing(self) -> None:
        p = self._primary_file_path()
        if not p:
            show_toast(self, "No file linked to this movie.")
            return
        from pathlib import Path as _P
        playback.open_containing_folder(_P(p))

    def _show_details(self) -> None:
        mid = self._current_movie_id()
        if mid is None:
            return
        dlg = DetailsDialog(self.db, int(mid), self)
        dlg.exec()

    def _set_watched(self, watched: bool) -> None:
        mid = self._current_movie_id()
        if mid is None:
            return
        try:
            self.db.set_watched(int(mid), watched)
            show_toast(self, "Marked watched" if watched else "Marked unwatched")
        except Exception:
            pass

    def _reset_progress(self) -> None:
        mid = self._current_movie_id()
        if mid is None:
            return
        try:
            self.db.reset_progress(int(mid))
            show_toast(self, "Progress reset")
        except Exception:
            pass

    def _locate_missing(self) -> None:
        # If the primary file path is missing, allow the user to relink
        p = self._primary_file_path()
        if not p:
            show_toast(self, "No file to relink for this movie.")
            return
        from pathlib import Path as _P
        old = _P(p)
        if old.exists():
            show_toast(self, "File exists; no relink needed.")
            return
        new_path, _ = QFileDialog.getOpenFileName(self, "Locate File", old.parent.as_posix())
        if not new_path:
            return
        if self.db.relink_media_file_by_path(str(old), new_path):
            show_toast(self, "File relinked.")
            self.refresh()
        else:
            show_toast(self, "Could not relink this file.")
