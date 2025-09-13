# KnotzFLix Packaging Plan

This document outlines how to package KnotzFLix for Windows, macOS, and Linux using PyInstaller. ffmpeg is not bundled; users should install it separately or you may ship OS-native guidance.

Targets
- Windows 10/11: .exe + installer (optional)
- macOS 12+: .app bundle (unsigned by default)
- Linux: AppDir/AppImage (optional) or plain binary folder

Approach: PyInstaller
- Pros: No code changes required, cross-platform, simple setup.
- Cons: Larger bundles; codesigning/notarization handled outside.

Requirements
- Python 3.11
- PyInstaller installed in a clean virtualenv
- Platform’s toolchain (e.g., Xcode CLT on macOS)

Build Steps
1) Install: `pip install pyinstaller`
2) From repo root, run the build helper:
   - Windows/macOS/Linux: `python scripts/build_pyinstaller.py`
3) Artifacts:
   - `dist/knotzflix/` directory with the executable.

Entrypoint
- The app entry is `scripts/run_app.py`, which imports `ui.app:run()`.

ffmpeg
- We do not bundle ffmpeg. Users should install it via OS package managers.
- The app shows an ffmpeg status indicator in Settings and a one-click “Validate Posters” button.

Installers (optional)
- Windows: Use Inno Setup or WiX to wrap `dist/knotzflix/` and create Start menu shortcuts.
- macOS: Zip the `.app` or use `hdiutil` to create a DMG; codesign if needed.
- Linux: Consider AppImage tooling or ship a tarball.

Notes
- Single-instance focuses via localhost IPC; ensure firewall prompts are benign.
- User data is stored in OS-appropriate dirs; no admin privileges required.

