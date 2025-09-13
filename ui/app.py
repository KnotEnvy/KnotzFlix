from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when running as a script
_project_root = str(Path(__file__).resolve().parents[1])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from infra import ipc_focus
from infra.logging_config import setup_logging
from infra.single_instance import SingleInstance, SingleInstanceError


def run() -> int:
    setup_logging()
    try:
        with SingleInstance():
            return _run_qt()
    except SingleInstanceError:
        # Notify existing instance to focus, if possible
        if ipc_focus.ping_existing():
            logging.getLogger(__name__).info("Signaled existing instance to focus window.")
            return 0
        logging.getLogger(__name__).warning("Another instance is already running (no focus signal).")
        return 0


def _run_qt() -> int:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    import time

    from ui.main_window import create_main_window
    from ui.widgets.splash import KnotzFlixSplash

    app = QApplication([])
    app.setApplicationName("KnotzFLix")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("KnotzFLix Team")
    
    # Show splash screen
    splash = KnotzFlixSplash()
    splash.show()
    
    # Initialize application with progress updates
    splash.showMessage("Initializing application...", 10)
    time.sleep(0.1)  # Small delay to show splash
    
    splash.showMessage("Loading configuration...", 30)
    QApplication.processEvents()
    
    splash.showMessage("Setting up database...", 50)
    QApplication.processEvents()
    
    splash.showMessage("Creating main window...", 70)
    QApplication.processEvents()
    
    # Create main window
    win = create_main_window()
    
    splash.showMessage("Starting IPC server...", 90)
    QApplication.processEvents()
    
    # Start focus IPC server to bring window to front on subsequent launches
    try:
        server = ipc_focus.start_server(lambda: _focus_window(win))
        # Ensure server stops on app exit
        app.aboutToQuit.connect(lambda: server.stop())  # type: ignore[attr-defined]
    except Exception:
        pass
    
    splash.showMessage("Ready!", 100)
    QApplication.processEvents()
    
    # Show main window and close splash after a brief moment
    def show_main_window():
        splash.close()
        win.show()
        
        # Show welcome dialog for first-time users
        _show_welcome_if_needed(win)
    
    # Delay to ensure splash is visible for at least a moment
    QTimer.singleShot(500, show_main_window)
    
    return app.exec()


def _show_welcome_if_needed(win) -> None:
    """Show welcome dialog for first-time users."""
    try:
        from infra.config import load_config
        from ui.widgets.welcome_dialog import WelcomeDialog
        
        config = load_config()
        
        # Show welcome if no library roots are configured and user hasn't disabled it
        if not config.library_roots and not getattr(config, 'hide_welcome', False):
            welcome = WelcomeDialog(win)
            
            # Connect signals to main window methods
            if hasattr(win, 'add_folder_from_welcome'):
                welcome.folder_added.connect(win.add_folder_from_welcome)
            if hasattr(win, 'start_initial_scan'):
                welcome.start_scan.connect(win.start_initial_scan)
                
            result = welcome.exec()
            
            # Save preference if user chose not to show again
            if not welcome.should_show_again():
                config.hide_welcome = True
                from infra.config import save_config
                save_config(config)
                
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error showing welcome dialog: {e}")


def _focus_window(win) -> None:
    try:
        win.raise_()
        win.activateWindow()
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(run())
