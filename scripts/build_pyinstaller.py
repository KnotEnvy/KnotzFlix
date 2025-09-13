from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if shutil.which("pyinstaller") is None:
        print("PyInstaller not found. Install with: pip install pyinstaller", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    entry = root / "scripts" / "run_app.py"
    dist_dir = root / "dist"
    build_dir = root / "build"
    name = "knotzflix"

    args = [
        "pyinstaller",
        "--name",
        name,
        "--noconfirm",
        "--clean",
        "--windowed",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        str(entry),
    ]
    print("Running:", " ".join(args))
    res = subprocess.run(args)
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())

