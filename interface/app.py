"""Launcher for the HEMA desktop interface.

Run with:  python main.py --gui
Requires PySide6 (optional dependency, see requirements.txt).
"""
import sys


def run_gui(controller) -> int:
    from PySide6.QtWidgets import QApplication

    from interface import theme
    from interface.main_window import MainWindow
    from interface.widgets import fade_in

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("HEMA AI")
    app.setStyleSheet(theme.stylesheet())
    window = MainWindow(controller)
    window.show()
    fade_in(window.centralWidget(), 500)
    return app.exec()
