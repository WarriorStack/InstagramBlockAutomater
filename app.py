import sys
import csv

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QHeaderView,
    QProgressBar,
)

from PySide6.QtGui import QColor

import database
from instagram import open_profile
from importer import extract_usernames


class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Instagram Account Manager")
        self.resize(1100, 750)

        database.init_db()

        # =============================
        # Main layout
        # =============================

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # =============================
        # Title
        # =============================

        title = QLabel("Instagram Account Manager")
        title.setObjectName("title")

        layout.addWidget(title)

        # =============================
        # Dashboard cards
        # =============================

        cards = QHBoxLayout()

        self.total = QLabel("Total\n0")
        self.pending = QLabel("Pending\n0")
        self.blocked = QLabel("Blocked\n0")
        self.skipped = QLabel("Skipped\n0")

        for widget in (
            self.total,
            self.pending,
            self.blocked,
            self.skipped,
        ):
            widget.setObjectName("card")
            cards.addWidget(widget)

        layout.addLayout(cards)

        # =============================
        # Progress
        # =============================

        self.progress_label = QLabel(
            "Completed: 0/0 (0%)"
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

        # =============================
        # Controls
        # =============================

        controls = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search username..."
        )

        self.search.textChanged.connect(
            self.refresh
        )

        controls.addWidget(self.search)

        # Import button
        import_btn = QPushButton(
            "Import TXT / CSV / JSON"
        )

        import_btn.clicked.connect(
            self.import_file
        )

        controls.addWidget(import_btn)

        # Export button
        export_btn = QPushButton(
            "Export CSV"
        )

        export_btn.clicked.connect(
            self.export_csv
        )

        controls.addWidget(export_btn)

        layout.addLayout(controls)

        # =============================
        # Table
        # =============================

        self.table = QTableWidget(
            0,
            4
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Username",
                "Status",
                "Process",
                "Status Action",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        self.table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        self.table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        self.table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        layout.addWidget(self.table)

        # =============================
        # Information
        # =============================

        note = QLabel(
            "Import accepts TXT, CSV, or JSON. "
            "JSON can contain nested objects/lists. "
            "Usernames are cleaned and duplicates are removed. "
            "Data is stored locally."
        )

        note.setWordWrap(True)

        layout.addWidget(note)

        # =============================
        # Styling
        # =============================

        self.apply_style()

        # =============================
        # Load data
        # =============================

        self.refresh()

    # ==================================================
    # Styling
    # ==================================================

    def apply_style(self):

        self.setStyleSheet(
            """
            QWidget {
                font-size: 14px;
            }

            #title {
                font-size: 25px;
                font-weight: 700;
                padding: 10px 0;
            }

            #card {
                border: 1px solid #cccccc;
                border-radius: 10px;
                padding: 15px;
                min-width: 150px;
                font-weight: 600;
            }

            QPushButton {
                padding: 8px 14px;
            }

            QLineEdit {
                padding: 8px;
            }

            QTableWidget {
                gridline-color: #dddddd;
            }

            QProgressBar {
                height: 25px;
                text-align: center;
            }
            """
        )

    # ==================================================
    # Refresh table
    # ==================================================

    def refresh(self):

        rows = database.get_users(
            self.search.text()
        )

        self.table.setRowCount(0)

        for r in rows:

            row = self.table.rowCount()

            self.table.insertRow(row)

            # -------------------------
            # Username
            # -------------------------

            username_item = QTableWidgetItem(
                "@" + r["username"]
            )

            self.table.setItem(
                row,
                0,
                username_item
            )

            # -------------------------
            # Status
            # -------------------------

            status_item = QTableWidgetItem(
                r["status"]
            )

            self.table.setItem(
                row,
                1,
                status_item
            )

            # -------------------------
            # Process button
            # -------------------------

            process_btn = QPushButton(
                "Process"
            )

            process_btn.clicked.connect(
                lambda _, uid=r["id"], u=r["username"]:
                self.process_user(uid, u)
            )

            self.table.setCellWidget(
                row,
                2,
                process_btn
            )

            # -------------------------
            # Status dropdown
            # -------------------------

            combo = QComboBox()

            combo.addItems(
                [
                    "Pending",
                    "Blocked",
                    "Skipped",
                    "Failed",
                ]
            )

            combo.setCurrentText(
                r["status"]
            )

            combo.currentTextChanged.connect(
                lambda status, uid=r["id"]:
                self.change_status(uid, status)
            )

            self.table.setCellWidget(
                row,
                3,
                combo
            )

            # -------------------------
            # Row colors
            # -------------------------

            status = r["status"]

            if status == "Blocked":

                background = "#d4edda"
                text = "#155724"

            elif status == "Skipped":

                background = "#fff3cd"
                text = "#856404"

            elif status == "Failed":

                background = "#f8d7da"
                text = "#721c24"

            else:

                background = "#dbeafe"
                text = "#1e40af"

            # Color text cells
            for column in range(2):

                item = self.table.item(
                    row,
                    column
                )

                if item:

                    item.setBackground(
                        QColor(background)
                    )

                    item.setForeground(
                        QColor(text)
                    )

        # =============================
        # Dashboard
        # =============================

        s = database.stats()

        self.total.setText(
            f"Total\n{s['Total']}"
        )

        self.pending.setText(
            f"Pending\n{s['Pending']}"
        )

        self.blocked.setText(
            f"Blocked\n{s['Blocked']}"
        )

        self.skipped.setText(
            f"Skipped\n{s['Skipped']}"
        )

        # =============================
        # Progress
        # =============================

        total = s["Total"]

        finished = (
            s["Blocked"]
            + s["Skipped"]
        )

        if total > 0:

            progress = int(
                (finished / total) * 100
            )

        else:

            progress = 0

        self.progress_bar.setValue(
            progress
        )

        self.progress_label.setText(
            f"Completed: "
            f"{finished}/{total} "
            f"({progress}%)"
        )

    # ==================================================
    # Process user
    # ==================================================

    def process_user(
        self,
        user_id,
        username
    ):

        result = open_profile(
            username
        )

        if result == "success":

            database.set_status(
                user_id,
                "Blocked"
            )

            print(
                f"SUCCESS: @{username} → Blocked"
            )

        elif result == "failed":

            database.set_status(
                user_id,
                "Failed"
            )

            print(
                f"FAILED: @{username} → Failed"
            )

        self.refresh()

    # ==================================================
    # Manual status change
    # ==================================================

    def change_status(
        self,
        uid,
        status
    ):

        database.set_status(
            uid,
            status
        )

        self.refresh()

    # ==================================================
    # Import
    # ==================================================

    def import_file(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select follower list",
            "",
            (
                "Supported files "
                "(*.txt *.csv *.json);;"
                "Text (*.txt);;"
                "CSV (*.csv);;"
                "JSON (*.json)"
            )
        )

        if not path:
            return

        try:

            usernames = extract_usernames(
                path
            )

            if not usernames:

                QMessageBox.warning(
                    self,
                    "No usernames found",
                    "No valid Instagram-style usernames "
                    "were found in this file."
                )

                return

            added = database.add_users(
                usernames
            )

            QMessageBox.information(
                self,
                "Import complete",
                (
                    f"Found {len(usernames)} "
                    f"unique usernames.\n\n"
                    f"Added {added} new usernames.\n"
                    f"Existing duplicates were ignored."
                )
            )

            self.refresh()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Import error",
                str(e)
            )

    # ==================================================
    # Export
    # ==================================================

    def export_csv(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "instagram_users.csv",
            "CSV (*.csv)"
        )

        if not path:
            return

        try:

            rows = database.get_users()

            with open(
                path,
                "w",
                newline="",
                encoding="utf-8"
            ) as f:

                writer = csv.writer(f)

                writer.writerow(
                    [
                        "username",
                        "status",
                        "created_at",
                        "updated_at",
                    ]
                )

                for r in rows:

                    writer.writerow(
                        [
                            r["username"],
                            r["status"],
                            r["created_at"],
                            r["updated_at"],
                        ]
                    )

            QMessageBox.information(
                self,
                "Export complete",
                f"Saved to:\n{path}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Export error",
                str(e)
            )


# ======================================================
# Start application
# ======================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    win = Window()

    win.show()

    sys.exit(
        app.exec()
    )