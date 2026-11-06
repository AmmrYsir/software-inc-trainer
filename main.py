"""
Software Inc. - Executive Studio Command Center
Native Windows 11 Fluent Design Desktop Application (WinUI 3 / PySide6)

Architecture:
  - core/memory.py: High-speed Win32 external memory manipulation & 64-bit Unity Mono runtime traversal
  - core/worker.py: Non-blocking QThread background telemetry & global Windows hotkeys monitor
  - core/constants.py: 33 traits, role specializations, hotkeys, and financial presets
  - core/cli.py: Terminal automation interface for headless operations
  - ui/components/: Fluent Vitals Gauges, Star Rating Selectors, Trait Chips, Stat Cards, and Header Ribbon
  - ui/views/: Executive Dashboard, Talent HQ (Unified Personnel & Founder), Projects Pipeline, Innovation & Patents, Sandbox, and Shortcuts & Audit Log
  - ui/window.py: Main Windows 11 Fluent Window with hardware-accelerated Mica/Acrylic navigation

Usage:
  - GUI Mode: python main.py
  - CLI Mode: python main.py --help
"""

import os
import sys

# Windows High-DPI Scaling Configuration
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"


def main():
    # If command-line arguments are passed, route directly to CLI mode
    if len(sys.argv) > 1:
        from core.cli import run_cli
        sys.exit(run_cli(sys.argv[1:]))

    # Otherwise launch modern PySide6 Fluent Desktop GUI
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from qfluentwidgets import setTheme, Theme
    from ui.window import MainWindow

    # Set rounding policy
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Software Inc. Studio Suite")
    app.setOrganizationName("SoftwareIncTrainer")

    # Enforce dark theme
    setTheme(Theme.DARK)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
