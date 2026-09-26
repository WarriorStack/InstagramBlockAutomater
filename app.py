import sys
import csv
import threading

from PySide6.QtCore import QObject, QThread, Signal

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


# ======================================================
# Process Worker
# ======================================================

class ProcessWorker(QObject):

    progress = Signal(int, int, int, str, str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, users):
        super().__init__()

        self.users = users

        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

    def pause(self):
        self.pause_event.set()

    def resume(self):
        self.pause_event.clear()

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()

    def run(self):

        total = len(self.users)
        completed = 0

        try:

            for user in self.users:

                # Stop before starting another user
                if self.stop_event.is_set():
                    break

                # Wait while paused
                while self.pause_event.is_set():

                    if self.stop_event.is_set():
                        self.finished.emit()
                        return

                    threading.Event().wait(0.1)

                user_id = user["id"]
                username = user["username"]

                print(
                    f"Processing "
                    f"{completed + 1}/{total}: "
                    f"@{username}"
                )

                try:

                    result = open_profile(username)

                    if result not in (
                        "success",
                        "failed"
                    ):
                        result = "failed"

                except Exception as e:

                    print(
                        f"Error processing "
                        f"@{username}: {e}"
                    )

                    result = "failed"

                completed += 1

                self.progress.emit(
                    completed,
                    total,
                    user_id,
                    username,
                    result
                )

            self.finished.emit()

        except Exception as e:

            self.error.emit(str(e))
            self.finished.emit()


# ======================================================
# Main Window
# ======================================================

class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Instagram Account Manager"
        )

        self.resize(
            1100,
            750
        )

        database.init_db()

        # Processing state
        self.process_thread = None
        self.process_worker = None
        self.processing = False
        self.is_paused = False

        # Active Instagram account used for account-specific status.
        self.active_account_id = None
        self.active_account_username = None

        # =============================
        # Main layout
        # =============================

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # =============================
        # Title
        # =============================

        title = QLabel(
            "Instagram Account Manager"
        )

        title.setObjectName(
            "title"
        )

        layout.addWidget(title)

        # =============================
        # Active Instagram account
        # =============================

        account_controls = QHBoxLayout()

        account_label = QLabel(
            "Instagram Account:"
        )

        self.account_combo = QComboBox()
        self.account_combo.setEditable(True)
        self.account_combo.setPlaceholderText(
            "Enter the account currently logged into Instagram"
        )

        existing_accounts = database.get_accounts()
        for account in existing_accounts:
            self.account_combo.addItem(
                "@" + account["username"],
                account["username"]
            )

        self.use_account_btn = QPushButton(
            "Use Account"
        )

        self.active_account_label = QLabel(
            "Active: Not set"
        )

        self.use_account_btn.clicked.connect(
            self.set_active_account
        )

        account_controls.addWidget(
            account_label
        )
        account_controls.addWidget(
            self.account_combo
        )
        account_controls.addWidget(
            self.use_account_btn
        )
        account_controls.addWidget(
            self.active_account_label
        )

        layout.addLayout(
            account_controls
        )

        # =============================
        # Dashboard cards
        # =============================

        cards = QHBoxLayout()

        self.total = QLabel(
            "Total\n0"
        )

        self.pending = QLabel(
            "Pending\n0"
        )

        self.blocked = QLabel(
            "Blocked\n0"
        )

        self.skipped = QLabel(
            "Skipped\n0"
        )

        for widget in (
            self.total,
            self.pending,
            self.blocked,
            self.skipped,
        ):

            widget.setObjectName(
                "card"
            )

            cards.addWidget(
                widget
            )

        layout.addLayout(cards)

        # =============================
        # Progress
        # =============================

        self.progress_label = QLabel(
            "Completed: 0/0 (0%)"
        )

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100
        )

        self.progress_bar.setValue(
            0
        )

        self.progress_bar.setTextVisible(
            True
        )

        layout.addWidget(
            self.progress_label
        )

        layout.addWidget(
            self.progress_bar
        )

        # =============================
        # Process Controls
        # =============================

        process_controls = QHBoxLayout()

        self.process_all_btn = QPushButton(
            "Process All"
        )

        self.pause_btn = QPushButton(
            "Pause"
        )

        self.stop_btn = QPushButton(
            "Stop"
        )

        process_controls.addWidget(
            self.process_all_btn
        )

        process_controls.addWidget(
            self.pause_btn
        )

        process_controls.addWidget(
            self.stop_btn
        )

        layout.addLayout(
            process_controls
        )

        # Button connections
        self.process_all_btn.clicked.connect(
            self.start_process_all
        )

        self.pause_btn.clicked.connect(
            self.toggle_pause
        )

        self.stop_btn.clicked.connect(
            self.stop_process_all
        )

        # Initial state
        self.pause_btn.setEnabled(
            False
        )

        self.stop_btn.setEnabled(
            False
        )

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

        controls.addWidget(
            self.search
        )

        # =============================
        # Import button
        # =============================

        import_btn = QPushButton(
            "Import TXT / CSV / JSON"
        )

        import_btn.clicked.connect(
            self.import_file
        )

        controls.addWidget(
            import_btn
        )

        # =============================
        # Export button
        # =============================

        export_btn = QPushButton(
            "Export CSV"
        )

        export_btn.clicked.connect(
            self.export_csv
        )

        controls.addWidget(
            export_btn
        )

        layout.addLayout(
            controls
        )

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

        layout.addWidget(
            self.table
        )

        # =============================
        # Information
        # =============================

        note = QLabel(
            "Import accepts TXT, CSV, or JSON. "
            "JSON can contain nested objects/lists. "
            "Usernames are cleaned and duplicates are removed. "
            "Processing status is stored separately for each Instagram account."
        )

        note.setWordWrap(
            True
        )

        layout.addWidget(
            note
        )

        # =============================
        # Styling
        # =============================

        self.apply_style()

        # =============================
        # Load data
        # =============================

        if len(existing_accounts) == 1:
            only_account = existing_accounts[0]["username"]
            self.account_combo.setCurrentText(
                "@" + only_account
            )
            self.set_active_account()
        else:
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
    # Active Instagram account
    # ==================================================

    def set_active_account(self):

        value = self.account_combo.currentText().strip()
        username = value.lstrip("@").strip().lower()

        if not username:
            QMessageBox.warning(
                self,
                "Account required",
                "Enter the Instagram account username currently logged in."
            )
            return

        if self.processing:
            return

        try:
            account_id = database.get_or_create_account(
                username
            )

            self.active_account_id = account_id
            self.active_account_username = username

            index = self.account_combo.findData(
                username
            )

            if index == -1:
                self.account_combo.addItem(
                    "@" + username,
                    username
                )
                index = self.account_combo.count() - 1

            self.account_combo.setCurrentIndex(
                index
            )

            self.active_account_label.setText(
                f"Active: @{username}"
            )

            self.refresh()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Account error",
                str(e)
            )

    # ==================================================
    # Refresh table
    # ==================================================

    def refresh(self):

        rows = database.get_users(
            self.search.text(),
            self.active_account_id
        )

        self.table.setRowCount(
            0
        )

        for r in rows:

            row = self.table.rowCount()

            self.table.insertRow(
                row
            )

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
                self.process_user(
                    uid,
                    u
                )
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
                self.change_status(
                    uid,
                    status
                )
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

            # Color username/status
            for column in range(2):

                item = self.table.item(
                    row,
                    column
                )

                if item:

                    item.setBackground(
                        QColor(
                            background
                        )
                    )

                    item.setForeground(
                        QColor(
                            text
                        )
                    )

        # =============================
        # Dashboard
        # =============================

        s = database.stats(
            self.active_account_id
        )

        self.total.setText(
            f"Total\n{s.get('Total', 0)}"
        )

        self.pending.setText(
            f"Pending\n{s.get('Pending', 0)}"
        )

        self.blocked.setText(
            f"Blocked\n{s.get('Blocked', 0)}"
        )

        self.skipped.setText(
            f"Skipped\n{s.get('Skipped', 0)}"
        )

        # =============================
        # Progress
        # =============================

        total = s.get("Total", 0)

        finished = (
            s.get("Blocked", 0)
            + s.get("Skipped", 0)
            + s.get("Failed", 0)
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
    # Process single user
    # ==================================================

    def process_user(
        self,
        user_id,
        username
    ):

        if self.processing:
            return

        try:

            result = open_profile(
                username
            )

            if result == "success":

                database.set_status(
                    user_id,
                    "Blocked",
                    self.active_account_id
                )

                print(
                    f"SUCCESS: "
                    f"@{username} → Blocked"
                )

            else:

                database.set_status(
                    user_id,
                    "Failed",
                    self.active_account_id
                )

                print(
                    f"FAILED: "
                    f"@{username} → Failed"
                )

        except Exception as e:

            database.set_status(
                user_id,
                "Failed"
            )

            print(
                f"ERROR: "
                f"@{username} → {e}"
            )

        self.refresh()

    # ==================================================
    # Start Process All
    # ==================================================

    def start_process_all(self):

        if self.processing:
            return

        if self.active_account_id is None:
            QMessageBox.warning(
                self,
                "Account not selected",
                "Select the Instagram account currently logged in, then click Use Account."
            )
            return

        rows = database.get_users(
            account_id=self.active_account_id
        )

        pending_users = [
            row
            for row in rows
            if row["status"] == "Pending"
        ]

        if not pending_users:

            QMessageBox.information(
                self,
                "Process All",
                "No pending users found."
            )

            return

        reply = QMessageBox.question(
            self,
            "Process All",
            (
                f"Process "
                f"{len(pending_users)} "
                f"pending users?"
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Processing state
        self.processing = True
        self.is_paused = False

        # Buttons
        self.process_all_btn.setEnabled(
            False
        )
        self.use_account_btn.setEnabled(
            False
        )
        self.account_combo.setEnabled(
            False
        )

        self.pause_btn.setEnabled(
            True
        )

        self.stop_btn.setEnabled(
            True
        )

        self.pause_btn.setText(
            "Pause"
        )

        # Reset progress for this batch
        self.progress_bar.setValue(
            0
        )

        self.progress_label.setText(
            f"Completed: "
            f"0/{len(pending_users)} "
            f"(0%)"
        )

        # =============================
        # Create worker thread
        # =============================

        self.process_thread = QThread()

        self.process_worker = ProcessWorker(
            pending_users
        )

        self.process_worker.moveToThread(
            self.process_thread
        )

        # Thread start
        self.process_thread.started.connect(
            self.process_worker.run
        )

        # Worker progress
        self.process_worker.progress.connect(
            self.on_process_progress
        )

        # Worker finished
        self.process_worker.finished.connect(
            self.on_process_finished
        )

        self.process_worker.finished.connect(
            self.process_thread.quit
        )

        # Worker error
        self.process_worker.error.connect(
            self.on_process_error
        )

        # Cleanup
        self.process_worker.finished.connect(
            self.process_worker.deleteLater
        )

        self.process_thread.finished.connect(
            self.on_process_thread_finished
        )

        self.process_thread.finished.connect(
            self.process_thread.deleteLater
        )

        self.process_thread.start()

    # ==================================================
    # Process progress
    # ==================================================

    def on_process_progress(
        self,
        completed,
        total,
        user_id,
        username,
        result
    ):

        if result == "success":

            database.set_status(
                user_id,
                "Blocked"
            )

            print(
                f"SUCCESS: "
                f"@{username} → Blocked"
            )

        else:

            database.set_status(
                user_id,
                "Failed"
            )

            print(
                f"FAILED: "
                f"@{username} → Failed"
            )

        # Progress
        progress = int(
            (completed / total) * 100
        )

        self.progress_bar.setValue(
            progress
        )

        self.progress_label.setText(
            f"Completed: "
            f"{completed}/{total} "
            f"({progress}%)"
        )

        # Refresh UI
        self.refresh()

    # ==================================================
    # Pause / Resume
    # ==================================================

    def toggle_pause(self):

        if not self.processing:
            return

        if self.is_paused:

            self.process_worker.resume()

            self.is_paused = False

            self.pause_btn.setText(
                "Pause"
            )

            print(
                "Processing resumed."
            )

        else:

            self.process_worker.pause()

            self.is_paused = True

            self.pause_btn.setText(
                "Resume"
            )

            print(
                "Processing paused."
            )

    # ==================================================
    # Stop
    # ==================================================

    def stop_process_all(self):

        if not self.processing:
            return

        self.process_worker.stop()

        self.stop_btn.setEnabled(
            False
        )

        self.pause_btn.setEnabled(
            False
        )

        self.pause_btn.setText(
            "Pause"
        )

        print(
            "Stop requested."
        )

    # ==================================================
    # Process finished
    # ==================================================

    def on_process_finished(self):

        self.processing = False
        self.is_paused = False

        self.process_all_btn.setEnabled(
            True
        )
        self.use_account_btn.setEnabled(
            True
        )
        self.account_combo.setEnabled(
            True
        )

        self.pause_btn.setEnabled(
            False
        )

        self.stop_btn.setEnabled(
            False
        )

        self.pause_btn.setText(
            "Pause"
        )

        self.refresh()

        print(
            "Process All finished."
        )

    # ==================================================
    # Worker error
    # ==================================================

    def on_process_error(
        self,
        message
    ):

        print(
            f"Process worker error: "
            f"{message}"
        )

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
            status,
            self.active_account_id
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

            from importer import extract_usernames

            usernames = extract_usernames(
                path
            )

            if not usernames:

                QMessageBox.warning(
                    self,
                    "No usernames found",
                    (
                        "No valid "
                        "Instagram-style "
                        "usernames were found "
                        "in this file."
                    )
                )

                return

            added = database.add_users(
                usernames
            )

            QMessageBox.information(
                self,
                "Import complete",
                (
                    f"Found "
                    f"{len(usernames)} "
                    f"unique usernames.\n\n"
                    f"Added {added} "
                    f"new usernames.\n"
                    f"Existing duplicates "
                    f"were ignored."
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

            if self.active_account_id is None:
                QMessageBox.warning(
                    self,
                    "Account not selected",
                    "Select an active Instagram account before exporting."
                )
                return

            rows = database.get_users(
                account_id=self.active_account_id
            )

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
                        "instagram_account",
                    ]
                )

                for r in rows:

                    writer.writerow(
                        [
                            r["username"],
                            r["status"],
                            r["created_at"],
                            r["updated_at"],
                            self.active_account_username,
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

    # ==================================================
    # Thread cleanup
    # ==================================================

    def on_process_thread_finished(self):

        self.process_thread = None
        self.process_worker = None

    # ==================================================
    # Close application
    # ==================================================

    def closeEvent(self, event):

        if self.process_worker is not None:
            try:
                self.process_worker.stop()
            except RuntimeError:
                pass

        if self.process_thread is not None:
            try:
                if self.process_thread.isRunning():
                    self.process_thread.quit()
                    self.process_thread.wait(3000)
            except RuntimeError:
                # QThread was already deleted by Qt.
                pass

        event.accept()


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