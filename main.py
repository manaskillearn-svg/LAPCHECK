
import sys
import json
import platform
import subprocess
from datetime import datetime

import psutil
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QGridLayout, QTextEdit, QMessageBox
)


def get_windows_info(command):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "Not available"


def scan_system():
    cpu = platform.processor() or get_windows_info(
        "(Get-CimInstance Win32_Processor).Name"
    )

    memory = psutil.virtual_memory()

    gpu = get_windows_info(
        "(Get-CimInstance Win32_VideoController).Name -join ', '"
    )

    disks = get_windows_info(
        "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus,Size | ConvertTo-Json"
    )

    battery = get_windows_info(
        "powercfg /batteryreport /output $env:TEMP\\lapcheck-battery.html; Get-Item $env:TEMP\\lapcheck-battery.html | Select-Object -ExpandProperty FullName"
    )

    return {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Computer": platform.node(),
        "Windows": platform.platform(),
        "CPU": cpu,
        "CPU Usage": f"{psutil.cpu_percent(interval=1)}%",
        "RAM": f"{memory.total / (1024**3):.1f} GB",
        "RAM Usage": f"{memory.percent}%",
        "GPU": gpu,
        "Storage": disks,
        "Battery Report": battery,
    }


class LapCheck(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LAPCHECK - Laptop Diagnostics")
        self.resize(950, 700)

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #101827;
                color: white;
                font-family: Segoe UI;
            }
            QLabel#title {
                font-size: 30px;
                font-weight: bold;
                color: #60a5fa;
            }
            QLabel#card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 18px;
                font-size: 15px;
            }
            QPushButton {
                background: #2563eb;
                color: white;
                padding: 13px;
                border-radius: 8px;
                font-weight: bold;
            }
            QTextEdit {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: white;
                padding: 10px;
            }
        """)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        title = QLabel("LAPCHECK")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("Professional Laptop Hardware Inspection")
        layout.addWidget(subtitle)

        grid = QGridLayout()
        self.cards = {}

        names = [
            "CPU", "RAM", "GPU",
            "STORAGE", "BATTERY", "SYSTEM"
        ]

        for index, name in enumerate(names):
            card = QLabel(name + "\nNot scanned")
            card.setObjectName("card")
            card.setMinimumHeight(90)
            self.cards[name] = card
            grid.addWidget(card, index // 2, index % 2)

        layout.addLayout(grid)

        self.scan_button = QPushButton("START FULL SYSTEM SCAN")
        self.scan_button.clicked.connect(self.run_scan)
        layout.addWidget(self.scan_button)

        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.report.setPlaceholderText(
            "Your diagnostic report will appear here."
        )
        layout.addWidget(self.report)

        self.save_button = QPushButton("SAVE REPORT")
        self.save_button.clicked.connect(self.save_report)
        self.save_button.setEnabled(False)
        layout.addWidget(self.save_button)

        self.data = None

    def run_scan(self):
        self.scan_button.setEnabled(False)
        self.scan_button.setText("SCANNING...")

        try:
            self.data = scan_system()

            self.cards["CPU"].setText(
                "CPU\n" + self.data["CPU"]
            )
            self.cards["RAM"].setText(
                "RAM\n" + self.data["RAM"]
            )
            self.cards["GPU"].setText(
                "GPU\n" + self.data["GPU"]
            )
            self.cards["STORAGE"].setText(
                "STORAGE\n" + self.data["Storage"][:150]
            )
            self.cards["BATTERY"].setText(
                "BATTERY\nReport generated"
            )
            self.cards["SYSTEM"].setText(
                "SYSTEM\n" + self.data["Computer"]
            )

            self.report.setPlainText(
                json.dumps(self.data, indent=4)
            )

            self.save_button.setEnabled(True)

        except Exception as error:
            QMessageBox.critical(
                self, "Scan Error", str(error)
            )

        finally:
            self.scan_button.setEnabled(True)
            self.scan_button.setText("START FULL SYSTEM SCAN")

    def save_report(self):
        if not self.data:
            return

        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            "LAPCHECK-report.json",
            "JSON Files (*.json)"
        )

        if path:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4)

            QMessageBox.information(
                self, "LAPCHECK", "Report saved successfully!"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LapCheck()
    window.show()
    sys.exit(app.exec())
