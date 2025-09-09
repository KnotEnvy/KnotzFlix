from __future__ import annotations

import hashlib
from pathlib import Path


def fingerprint_partial(path: Path, bytes_per_chunk: int = 65536, chunks: int = 3) -> str:
    """Compute a partial fingerprint of a file using BLAKE2b as a fallback.

    Reads up to `chunks` equally spaced chunks from the file and hashes them.
    Using BLAKE2b here keeps us dependency-free; swap to BLAKE3 when available.
    """
    h = hashlib.blake2b(digest_size=32)
    size = path.stat().st_size
    if size == 0:
        h.update(b"")
        return h.hexdigest()
    with path.open("rb") as f:
        positions = [0]
        if chunks > 1:
            step = max((size - bytes_per_chunk) // (chunks - 1), 0)
            positions = [min(i * step, max(size - bytes_per_chunk, 0)) for i in range(chunks)]
        for pos in positions:
            f.seek(pos)
            h.update(f.read(bytes_per_chunk))
    return h.hexdigest()

