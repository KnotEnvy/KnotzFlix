from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt
from PyQt6.QtGui import QIcon, QPixmap

from infra.db import Database


class Roles:
    IdRole = Qt.ItemDataRole.UserRole + 1
    TitleRole = Qt.ItemDataRole.UserRole + 2
    YearRole = Qt.ItemDataRole.UserRole + 3
    PosterPathRole = Qt.ItemDataRole.UserRole + 4


class MovieListModel(QAbstractListModel):
    def __init__(self, db: Database, *, order_mode: str = "default", path_prefix: Optional[str] = None):
        super().__init__()
        self.db = db
        self._items: list[dict[str, Any]] = []
        self._icon_cache: dict[str, QIcon] = {}
        self._query: str = ""
        self._order_mode = order_mode  # "default" (sort_title) or "recent" (created_at desc)
        self._path_prefix = path_prefix
        self.refresh()

    def refresh(self) -> None:
        # Apply optional search filter using FTS5 ids if query is set
        ids: list[int] | None = None
        q = (self._query or "").strip()
        if q:
            ids = self.db.search_titles(q)
            if not ids:
                self.beginResetModel()
                self._items = []
                self._icon_cache.clear()
                self.endResetModel()
                return

        # Optional path filter
        if self._path_prefix:
            pf_ids = self.db.get_movie_ids_by_path_prefix(self._path_prefix)
            if ids is None:
                ids = pf_ids
            else:
                # intersection
                s = set(ids).intersection(pf_ids)
                ids = list(s)

        order_clause = "ORDER BY COALESCE(m.sort_title, m.canonical_title)"
        if self._order_mode == "recent":
            order_clause = "ORDER BY datetime(m.created_at) DESC, COALESCE(m.sort_title, m.canonical_title)"

        if ids is None:
            sql = (
                """
                SELECT m.id, m.canonical_title, m.year,
                       (SELECT path FROM image WHERE movie_id=m.id AND kind='poster' LIMIT 1) AS poster
                FROM movie m
                """
                + "\n"
                + order_clause
            )
            cur = self.db.conn.execute(sql)
        else:
            if not ids:
                # No matches
                self.beginResetModel()
                self._items = []
                self._icon_cache.clear()
                self.endResetModel()
                return
            placeholders = ",".join(["?"] * len(ids))
            sql = (
                """
                SELECT m.id, m.canonical_title, m.year,
                       (SELECT path FROM image WHERE movie_id=m.id AND kind='poster' LIMIT 1) AS poster
                FROM movie m
                WHERE m.id IN ("""
                + placeholders
                + ")\n"
                + order_clause
            )
            cur = self.db.conn.execute(sql, ids)
        self.beginResetModel()
        self._items = [
            {
                "id": row[0],
                "title": row[1],
                "year": row[2],
                "poster": row[3],
            }
            for row in cur.fetchall()
        ]
        self._icon_cache.clear()
        self.endResetModel()

    def set_filter_query(self, query: str) -> None:
        q = query or ""
        if q == self._query:
            return
        self._query = q
        self.refresh()

    def set_path_prefix(self, prefix: Optional[str]) -> None:
        self._path_prefix = prefix
        self.refresh()

    def set_order_mode(self, mode: str) -> None:
        if mode not in ("default", "recent"):
            return
        self._order_mode = mode
        self.refresh()

    # Qt model interface
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        it = self._items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            y = f" ({it['year']})" if it["year"] else ""
            return f"{it['title']}{y}"
        if role == Qt.ItemDataRole.DecorationRole:
            p = it.get("poster")
            if not p:
                return None
            icon = self._icon_cache.get(p)
            if icon is None:
                pix = QPixmap(p)
                if not pix.isNull():
                    icon = QIcon(pix)
                    self._icon_cache[p] = icon
            return icon
        if role == Roles.IdRole:
            return it["id"]
        if role == Roles.TitleRole:
            return it["title"]
        if role == Roles.YearRole:
            return it["year"]
        if role == Roles.PosterPathRole:
            return it.get("poster")
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        names = super().roleNames()
        names[Roles.IdRole] = b"id"
        names[Roles.TitleRole] = b"title"
        names[Roles.YearRole] = b"year"
        names[Roles.PosterPathRole] = b"poster"
        return names
