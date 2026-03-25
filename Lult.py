import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PyQt6.QtCore import QObject, QRunnable, QSize, QThreadPool, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

APP_ROOT = Path(__file__).resolve().parent
REPAK_SRC = APP_ROOT / "repak"
REPAK_BIN = REPAK_SRC / "target" / "release" / "repak"
UNREAL_LOCRES_EXE = APP_ROOT / "unreallocres" / "UnrealLocres.exe"
MANIFEST_FILE = APP_ROOT / ".locres_workflow_manifest.json"
STATE_FILE = APP_ROOT / ".locres_gui_state.json"
CZ_ICON = APP_ROOT / "icons" / "cz.svg"
EN_ICON = APP_ROOT / "icons" / "en.svg"
APP_ICON = APP_ROOT / "icons" / "lult_app.svg"
USER_DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "LULT"
TOOLS_DIR = USER_DATA_DIR / "tools"
RUNTIME_REPAK_BIN = TOOLS_DIR / "repak" / "repak"
RUNTIME_UNREAL_LOCRES_EXE = TOOLS_DIR / "unreallocres" / "UnrealLocres.exe"
REPAK_RELEASE_API = "https://api.github.com/repos/trumank/repak/releases/latest"
UNREAL_LOCRES_RELEASE_API = "https://api.github.com/repos/akintos/UnrealLocres/releases/latest"
GITHUB_API_TIMEOUT = 20
TOOLS_REFRESH_INTERVAL_SECONDS = 12 * 60 * 60


class TaskSignals(QObject):
    progress = pyqtSignal(int)
    set_field = pyqtSignal(str, str)
    done = pyqtSignal(bool, str)


class TaskRunner(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = TaskSignals()

    def run(self):
        try:
            message = self.fn(self.signals.progress.emit, self.signals.set_field.emit)
            self.signals.done.emit(True, message)
        except Exception as exc:
            self.signals.done.emit(False, str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LULT - Linux Unreal Localization Tool")
        if APP_ICON.is_file():
            self.setWindowIcon(QIcon(str(APP_ICON)))
        self.resize(580, 560)

        self.thread_pool = QThreadPool.globalInstance()
        self.busy = False
        self.pending_task_name = ""
        self.pending_auto_check = False
        self.startup_pak_cleanup_scheduled = False
        self.pak_field_user_touched = False

        self.state = self._load_state()
        self.step_buttons = []
        self.language = "en"

        self._build_ui()
        self._apply_styles()
        self._load_defaults()
        self._apply_language()
        self._sanitize_initial_pak_field()

        QTimer.singleShot(0, self.auto_check_tools)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(22, 22, 22, 22)
        outer.setSpacing(14)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(0)
        top_bar.addStretch(1)

        flags = QHBoxLayout()
        flags.setSpacing(4)
        self.en_button = QToolButton()
        self.en_button.setIcon(QIcon(str(EN_ICON)))
        self.en_button.setIconSize(QSize(20, 13))
        self.en_button.setFixedSize(QSize(28, 20))
        self.en_button.setToolTip("English")
        self.en_button.setAutoRaise(True)
        self.en_button.clicked.connect(lambda: self.set_language("en"))
        self.cz_button = QToolButton()
        self.cz_button.setIcon(QIcon(str(CZ_ICON)))
        self.cz_button.setIconSize(QSize(20, 13))
        self.cz_button.setFixedSize(QSize(28, 20))
        self.cz_button.setToolTip("Čeština")
        self.cz_button.setAutoRaise(True)
        self.cz_button.clicked.connect(lambda: self.set_language("cs"))
        flags.addWidget(self.en_button)
        flags.addWidget(self.cz_button)
        top_bar.addLayout(flags)
        outer.addLayout(top_bar)

        title_column = QVBoxLayout()
        title_column.setSpacing(4)
        title = QLabel("Linux Unreal Localization Tool")
        title.setObjectName("title")
        title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.title_label = title
        subtitle = QLabel("Vyber pak, extrahuj locres do CSV a po úpravě vrať změny zpět do nového *_P.pak")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(False)
        subtitle.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.subtitle_label = subtitle
        title_column.addWidget(title)
        title_column.addWidget(subtitle)
        outer.addLayout(title_column)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)
        outer.addWidget(card)

        self.input_label = self._label("")
        card_layout.addWidget(self.input_label)
        pak_row = QHBoxLayout()
        pak_row.setSpacing(8)
        self.input_pak_edit = QLineEdit()
        self.input_pak_edit.textEdited.connect(self._on_input_pak_edited)
        pak_button = QPushButton("")
        self.pick_pak_button = pak_button
        pak_button.clicked.connect(self._pick_input_pak)
        pak_row.addWidget(self.input_pak_edit, 1)
        pak_row.addWidget(pak_button)
        card_layout.addLayout(pak_row)

        self.selected_locres_info = QLabel("")
        self.selected_locres_info.setObjectName("infoText")
        self.selected_locres_info.setWordWrap(False)
        self.selected_locres_info.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        card_layout.addWidget(self.selected_locres_info)

        self.csv_info = QLabel("")
        self.csv_info.setObjectName("infoText")
        self.csv_info.setWordWrap(False)
        self.csv_info.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        csv_info_row = QHBoxLayout()
        csv_info_row.setSpacing(8)
        csv_info_row.addWidget(self.csv_info, 1)
        self.open_csv_button = QPushButton("")
        self.open_csv_button.setObjectName("smallButton")
        self.open_csv_button.clicked.connect(self.open_current_csv)
        self.open_csv_button.setEnabled(False)
        self.open_csv_button.setVisible(False)
        csv_info_row.addWidget(self.open_csv_button, 0)

        self.open_csv_folder_button = QPushButton("")
        self.open_csv_folder_button.setObjectName("smallButton")
        self.open_csv_folder_button.clicked.connect(self.open_current_csv_folder)
        self.open_csv_folder_button.setEnabled(False)
        self.open_csv_folder_button.setVisible(False)
        csv_info_row.addWidget(self.open_csv_folder_button, 0)
        card_layout.addLayout(csv_info_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Připraveno")
        card_layout.addWidget(self.progress)

        extract_row = QHBoxLayout()
        extract_row.setSpacing(8)
        self.btn_extract = QPushButton("")
        self.btn_extract.clicked.connect(self.extract_locres)
        extract_row.addWidget(self.btn_extract, 1)
        self.extract_all_checkbox = QCheckBox("")
        self.extract_all_checkbox.setObjectName("cleanupCheckbox")
        extract_row.addWidget(self.extract_all_checkbox, 0, Qt.AlignmentFlag.AlignRight)
        card_layout.addLayout(extract_row)

        import_row = QHBoxLayout()
        import_row.setSpacing(8)
        self.btn_import_pack = QPushButton("")
        self.btn_import_pack.clicked.connect(self.import_and_pack)
        import_row.addWidget(self.btn_import_pack, 1)

        self.cleanup_checkbox = QCheckBox("")
        self.cleanup_checkbox.setObjectName("cleanupCheckbox")
        self.cleanup_checkbox.setToolTip("")
        self.cleanup_checkbox.setSizePolicy(self.cleanup_checkbox.sizePolicy().horizontalPolicy(), self.cleanup_checkbox.sizePolicy().verticalPolicy())
        import_row.addWidget(self.cleanup_checkbox, 0, Qt.AlignmentFlag.AlignRight)
        card_layout.addLayout(import_row)

        self.step_buttons = [
            self.btn_extract,
            self.btn_import_pack,
            pak_button,
            self.open_csv_button,
            self.open_csv_folder_button,
            self.extract_all_checkbox,
            self.cleanup_checkbox,
        ]

        card_layout.addStretch(1)

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.footer_status = QLabel("Kontrola nástrojů: čekám...")
        self.footer_status.setTextFormat(Qt.TextFormat.RichText)
        self.statusBar().addPermanentWidget(self.footer_status)

    def _label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #f4f7fb;
                color: #1f2937;
                font-family: "Noto Sans", "DejaVu Sans", sans-serif;
                font-size: 13px;
            }
            #title {
                font-size: 30px;
                font-weight: 800;
                color: #0f172a;
            }
            #subtitle {
                color: #475569;
                margin-bottom: 4px;
            }
            QToolButton {
                background: transparent;
                border: none;
                padding: 0px;
                min-width: 30px;
                min-height: 20px;
            }
            QToolButton:hover {
                background: transparent;
            }
            #fieldLabel {
                font-size: 13px;
                font-weight: 700;
                color: #1e293b;
                margin-top: 4px;
            }
            #infoText {
                font-size: 11px;
                color: #64748b;
                margin-top: 2px;
                margin-bottom: 2px;
            }
            #card {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #ffffff, stop:1 #edf3fb);
                border: 1px solid #d5e0ed;
                border-radius: 18px;
            }
            QLineEdit {
                border: 1px solid #c8d3e0;
                border-radius: 10px;
                padding: 9px;
                background: #fbfdff;
                min-height: 22px;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
                background: #ffffff;
            }
            QPushButton {
                background: #1d4ed8;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 700;
                min-height: 24px;
            }
            QPushButton:hover {
                background: #1e40af;
            }
            QPushButton:disabled {
                background: #94a3b8;
                color: #e2e8f0;
            }
            #smallButton {
                border-radius: 8px;
                padding: 4px 8px;
                min-height: 20px;
                min-width: 58px;
                font-size: 11px;
            }
            #cleanupCheckbox {
                spacing: 8px;
                font-weight: 700;
                color: #1e293b;
                padding-left: 4px;
            }
            QProgressBar {
                border: 1px solid #93c5fd;
                border-radius: 10px;
                background: #eff6ff;
                text-align: center;
                color: #0f172a;
                min-height: 26px;
                font-weight: 700;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #16a34a, stop:1 #22c55e);
            }
            QStatusBar {
                background: #dbeafe;
                color: #0f172a;
            }
            """
        )

    def _update_min_window_width(self):
        minimum_width = 580
        self.setMinimumWidth(minimum_width)
        if self.width() < minimum_width:
            self.resize(minimum_width, self.height())

    def showEvent(self, event):
        super().showEvent(event)
        if self.startup_pak_cleanup_scheduled:
            return
        self.startup_pak_cleanup_scheduled = True
        for delay in (0, 150, 500):
            QTimer.singleShot(delay, self._clear_startup_pak_text_if_untouched)

    def _on_input_pak_edited(self, _text):
        self.pak_field_user_touched = True

    def _clear_startup_pak_text_if_untouched(self):
        if self.pak_field_user_touched:
            return
        if not self.input_pak_edit.text():
            return
        self.input_pak_edit.clear()
        self.input_pak_edit.setPlaceholderText(self.tr_text("pak_placeholder"))

    def _pick_input_pak(self):
        selected, _ = QFileDialog.getOpenFileName(self, self.tr_text("pick_pak_title"), self.input_pak_edit.text(), self.tr_text("pak_filter"))
        if selected:
            self.pak_field_user_touched = True
            self.input_pak_edit.setText(selected)

    def tr_text(self, key):
        texts = {
            "en": {
                "window_title": "LULT - Linux Unreal Localization Tool",
                "title": "Linux Unreal Localization Tool",
                "subtitle": "Select pak, extract locres to CSV, then import changes back into a new *_P.pak",
                "input_label": "Input pak",
                "pick": "Browse",
                "pak_placeholder": "select path to .pak",
                "selected_none": "Selected locres: none",
                "csv_none": "CSV file: not created yet",
                "selected_prefix": "Selected locres: {value}",
                "csv_prefix": "CSV file: {value}",
                "open": "Open",
                "folder": "Folder",
                "extract_button": "Extract locres",
                "extract_all": "Extract all",
                "import_button": "Back import",
                "cleanup": "Cleanup",
                "cleanup_tooltip": "After import finishes, the app deletes all generated helper files except the final pak and the CSV file.",
                "busy_title": "Action running",
                "busy_text": "Wait until the current action finishes.",
                "tools_wait": "Tool check: waiting...",
                "tools_ok": "Tool check: OK ({message})",
                "tools_error": "Tool check: ERROR ({message})",
                "tool_mono": "mono",
                "tool_repak": "repak",
                "tool_unreallocres": "UnrealLocres",
                "tool_update_available": "update available",
                "done_prefix": "Done: {name}",
                "error_prefix": "Error: {name}",
                "error_title": "Error",
                "pick_pak_title": "Select pak",
                "pak_filter": "Pak (*.pak);;All files (*)",
                "missing_manifest": "Manifest not found. Run locres extraction first.",
                "missing_locres": "No locres selected. Run locres extraction first.",
                "missing_locres_in_pak": "No .locres file was found in the pak.",
                "locres_pick_title": "Choose locres",
                "locres_pick_text": "Choose the locres file to extract:",
                "cancelled_choice": "Action was cancelled. No locres file was selected.",
                "extract_done": "Locres was extracted and CSV opened",
                "extract_all_done": "All locres files were extracted to CSV",
                "import_done": "Done. New pak: {path}",
                "auto_check": "mono + UnrealLocres {unreal_version} + repak {repak_version} ready",
                "need_mono": "mono is missing. Install mono-complete.",
                "need_unreal": "UnrealLocres.exe is missing: {path}",
                "need_repak_src": "Repak source is missing: {path}",
                "need_cargo": "cargo is missing and repak binary does not exist.",
                "build_failed": "Repak build finished, but the binary is missing: {path}",
                "bundled_version": "bundled",
                "unknown_version": "unknown",
                "repak_asset_missing": "No Linux repak release asset was found for architecture: {arch}",
                "unreal_asset_missing": "UnrealLocres.exe asset is missing in the latest GitHub release.",
                "tool_update_download_failed": "GitHub tool update failed: {message}",
                "input_pak_missing": "Input pak",
                "pak_must_be": "{label} must be a .pak: {path}",
                "csv_must_be": "{label} must be a .csv: {path}",
                "not_found": "{label} not found: {path}",
                "not_dir": "{label} folder not found: {path}",
                "extract_root_label": "Extraction folder",
                "working_locres_label": "Working locres",
                "csv_label": "CSV file",
                "working_locres_missing": "Working locres",
                "selected_after_extract_missing": "Selected locres does not exist after extraction: {path}",
                "selected_all_prefix": "Selected locres: all ({value})",
                "csv_missing_after_export": "Export finished, but CSV is missing: {path}",
                "csv_folder_prefix": "CSV folder: {value}",
                "pack_missing": "Packed file is missing: {path}",
                "open_failed": "Could not open: {path}",
            },
            "cs": {
                "window_title": "LULT - Linux Unreal Localization Tool",
                "title": "Linux Unreal Localization Tool",
                "subtitle": "Vyber pak, extrahuj locres do CSV a po úpravě vrať změny zpět do nového *_P.pak",
                "input_label": "Vstupní pak",
                "pick": "Vybrat",
                "pak_placeholder": "vyber cestu k .pak",
                "selected_none": "Vybraný locres: není vybrán",
                "csv_none": "CSV soubor: zatím nevytvořen",
                "selected_prefix": "Vybraný locres: {value}",
                "csv_prefix": "CSV soubor: {value}",
                "open": "Otevřít",
                "folder": "Složka",
                "extract_button": "Extrahovat locres",
                "extract_all": "Extrahovat všechny",
                "import_button": "Zpětný import",
                "cleanup": "Uklidit",
                "cleanup_tooltip": "Po dokončení importu program smaže všechny pomocné soubory, které vytvořil, kromě finálního paku a CSV souboru.",
                "busy_title": "Běží akce",
                "busy_text": "Počkej na dokončení aktuální akce.",
                "tools_wait": "Kontrola nástrojů: čekám...",
                "tools_ok": "Kontrola nástrojů: OK ({message})",
                "tools_error": "Kontrola nástrojů: CHYBA ({message})",
                "tool_mono": "mono",
                "tool_repak": "repak",
                "tool_unreallocres": "UnrealLocres",
                "tool_update_available": "dostupná aktualizace",
                "done_prefix": "Hotovo: {name}",
                "error_prefix": "Chyba: {name}",
                "error_title": "Chyba",
                "pick_pak_title": "Vyber pak",
                "pak_filter": "Pak (*.pak);;Všechny soubory (*)",
                "missing_manifest": "Manifest nenalezen. Nejdřív spusť extrakci locres.",
                "missing_locres": "Není vybraný locres. Spusť nejdřív extrakci locres.",
                "missing_locres_in_pak": "V paku nebyl nalezen žádný .locres soubor.",
                "locres_pick_title": "Vyber locres",
                "locres_pick_text": "Vyber locres soubor k extrakci:",
                "cancelled_choice": "Akce byla zrušena. Nebyl vybrán locres soubor.",
                "extract_done": "Locres byl extrahován a CSV otevřen",
                "extract_all_done": "Všechny locres soubory byly extrahovány do CSV",
                "import_done": "Hotovo. Nový pak: {path}",
                "auto_check": "mono + UnrealLocres {unreal_version} + repak {repak_version} připraveny",
                "need_mono": "Chybí mono. Nainstaluj mono-complete.",
                "need_unreal": "UnrealLocres.exe chybí: {path}",
                "need_repak_src": "Repak zdroj chybí: {path}",
                "need_cargo": "Chybí cargo a repak binárka neexistuje.",
                "build_failed": "Repak build skončil, ale binárka chybí: {path}",
                "bundled_version": "bundled",
                "unknown_version": "neznámá",
                "repak_asset_missing": "Pro architekturu {arch} nebyl v GitHub release nalezen linuxový asset repaku.",
                "unreal_asset_missing": "V posledním GitHub release chybí asset UnrealLocres.exe.",
                "tool_update_download_failed": "GitHub aktualizace nástrojů selhala: {message}",
                "input_pak_missing": "Vstupní pak",
                "pak_must_be": "{label} musí být .pak: {path}",
                "csv_must_be": "{label} musí být .csv: {path}",
                "not_found": "{label} nenalezen: {path}",
                "not_dir": "{label} nenalezena: {path}",
                "extract_root_label": "Extrakční složka",
                "working_locres_label": "Pracovní locres",
                "csv_label": "CSV soubor",
                "working_locres_missing": "Pracovní locres",
                "selected_after_extract_missing": "Vybraný locres po extrakci neexistuje: {path}",
                "selected_all_prefix": "Vybraný locres: všechny ({value})",
                "csv_missing_after_export": "Export proběhl, ale CSV chybí: {path}",
                "csv_folder_prefix": "CSV složka: {value}",
                "pack_missing": "Po pack chybí soubor: {path}",
                "open_failed": "Nepodařilo se otevřít: {path}",
            },
        }
        return texts[self.language][key]

    def set_language(self, language):
        self.language = language
        self._apply_language()

    def _apply_language(self):
        self.setWindowTitle(self.tr_text("window_title"))
        self.title_label.setText(self.tr_text("title"))
        self.subtitle_label.setText(self.tr_text("subtitle"))
        self.input_label.setText(self.tr_text("input_label"))
        self.pick_pak_button.setText(self.tr_text("pick"))
        self.input_pak_edit.setPlaceholderText(self.tr_text("pak_placeholder"))
        self.open_csv_button.setText(self.tr_text("open"))
        self.open_csv_folder_button.setText(self.tr_text("folder"))
        self.btn_extract.setText(self.tr_text("extract_button"))
        self.extract_all_checkbox.setText(self.tr_text("extract_all"))
        self.btn_import_pack.setText(self.tr_text("import_button"))
        self.cleanup_checkbox.setText(self.tr_text("cleanup"))
        self.cleanup_checkbox.setToolTip(self.tr_text("cleanup_tooltip"))
        if not self.selected_locres_info.text() or ":" not in self.selected_locres_info.text():
            self.selected_locres_info.setText(self.tr_text("selected_none"))
        elif self.selected_locres_info.text().endswith("none") or self.selected_locres_info.text().endswith("není vybrán"):
            self.selected_locres_info.setText(self.tr_text("selected_none"))
        else:
            value = self.selected_locres_info.text().split(":", 1)[1].strip()
            self.selected_locres_info.setText(self.tr_text("selected_prefix").format(value=value))
        if not self.csv_info.text() or ":" not in self.csv_info.text():
            self.csv_info.setText(self.tr_text("csv_none"))
        elif self.csv_info.text().endswith("not created yet") or self.csv_info.text().endswith("zatím nevytvořen"):
            self.csv_info.setText(self.tr_text("csv_none"))
        else:
            value = self.csv_info.text().split(":", 1)[1].strip()
            self.csv_info.setText(self.tr_text("csv_prefix").format(value=value))
        if self.pending_auto_check:
            self._set_footer(self.tr_text("tools_wait"))
        self._update_min_window_width()

    def _set_footer(self, text):
        self.footer_status.setText(text)

    def _set_busy(self, busy):
        self.busy = busy
        for button in self.step_buttons:
            button.setEnabled(not busy)

    def _set_progress(self, value):
        value = max(0, min(100, value))
        self.progress.setValue(value)
        self.progress.setFormat(f"{value}%")

    def _run_task(self, name, fn, auto_check=False):
        if self.busy:
            QMessageBox.warning(self, self.tr_text("busy_title"), self.tr_text("busy_text"))
            return

        self.pending_task_name = name
        self.pending_auto_check = auto_check
        self._set_busy(True)
        self._set_progress(5)

        runner = TaskRunner(fn)
        runner.signals.progress.connect(self._set_progress)
        runner.signals.set_field.connect(self._on_set_field)
        runner.signals.done.connect(self._on_task_done)
        self.thread_pool.start(runner)

    def _on_set_field(self, key, value):
        if key == "selected_locres":
            name = Path(value).name if value else "není vybrán"
            self.selected_locres_info.setText(self.tr_text("selected_prefix").format(value=name))
        elif key == "selected_locres_all":
            self.selected_locres_info.setText(self.tr_text("selected_all_prefix").format(value=value))
        elif key == "csv":
            name = Path(value).name if value else "zatím nevytvořen"
            self.csv_info.setText(self.tr_text("csv_prefix").format(value=name))
            is_ready = bool(value and Path(value).is_file())
            self._set_csv_actions(is_ready, show_open=is_ready, show_folder=is_ready)
        elif key == "csv_folder":
            folder_name = Path(value).name if value else ""
            self.csv_info.setText(self.tr_text("csv_folder_prefix").format(value=folder_name))
            is_ready = bool(value and Path(value).is_dir())
            self._set_csv_actions(is_ready, show_open=False, show_folder=is_ready)

    def _on_task_done(self, ok, message):
        self._set_busy(False)
        if ok:
            self._set_progress(100)
            if self.pending_auto_check:
                self._set_footer(self.tr_text("tools_ok").format(message=message))
            else:
                self._set_footer(self.tr_text("done_prefix").format(name=self.pending_task_name))
        else:
            self._set_progress(0)
            if self.pending_auto_check:
                detail = self._build_tool_check_detail(check_updates=False)
                self._set_footer(self.tr_text("tools_error").format(message=detail))
            else:
                self._set_footer(self.tr_text("error_prefix").format(name=self.pending_task_name))
            QMessageBox.critical(self, self.tr_text("error_title"), message)

        self.pending_task_name = ""
        self.pending_auto_check = False

    def _run_command(self, command, cwd=None):
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
            if len(output) > 3000:
                output = output[-3000:]
            raise RuntimeError(
                f"Příkaz selhal s kódem {result.returncode}: {' '.join(str(x) for x in command)}"
                + (f"\n\n{output}" if output else "")
            )
        return result.stdout

    def _load_defaults(self):
        self.input_pak_edit.setText("")
        self.input_pak_edit.setPlaceholderText(self.tr_text("pak_placeholder"))
        self.selected_locres_info.setText(self.tr_text("selected_none"))
        self.csv_info.setText(self.tr_text("csv_none"))
        self._set_csv_actions(False, show_open=False, show_folder=False)

    def _set_csv_actions(self, is_ready, show_open, show_folder):
        self.open_csv_button.setVisible(show_open)
        self.open_csv_button.setEnabled(bool(is_ready and show_open))
        self.open_csv_folder_button.setVisible(show_folder)
        self.open_csv_folder_button.setEnabled(bool(is_ready and show_folder))

    def _sanitize_initial_pak_field(self):
        # Defensive cleanup for stale defaults from older packaged builds.
        text = self.input_pak_edit.text().strip()
        if not text:
            return
        normalized = str(Path(text).expanduser())
        app_default = str(APP_ROOT / "input.pak")
        if normalized == app_default or ("/tmp/_MEI" in normalized and normalized.endswith("/input.pak")):
            self.input_pak_edit.clear()

    def open_current_csv(self):
        try:
            manifest = self._load_manifest()
            csv_path = self._require_csv(manifest.get("working_csv", ""), self.tr_text("csv_label"))
            self._open_path(csv_path, fail_if_unopened=True)
        except Exception as exc:
            QMessageBox.critical(self, self.tr_text("error_title"), str(exc))

    def open_current_csv_folder(self):
        try:
            manifest = self._load_manifest()
            if manifest.get("mode") == "all":
                work_root = self._require_dir(manifest.get("work_root", ""), self.tr_text("extract_root_label"))
                self._open_path(work_root, fail_if_unopened=True)
                return
            csv_path = self._require_csv(manifest.get("working_csv", ""), self.tr_text("csv_label"))
            self._open_path(csv_path.parent, fail_if_unopened=True)
        except Exception as exc:
            QMessageBox.critical(self, self.tr_text("error_title"), str(exc))

    def _load_state(self):
        if not STATE_FILE.is_file():
            return {"last_locres_by_pak": {}, "tool_versions": {}, "tools_last_checked_at": 0}
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"last_locres_by_pak": {}, "tool_versions": {}, "tools_last_checked_at": 0}
        if not isinstance(data, dict):
            return {"last_locres_by_pak": {}, "tool_versions": {}, "tools_last_checked_at": 0}
        if not isinstance(data.get("last_locres_by_pak"), dict):
            data["last_locres_by_pak"] = {}
        if not isinstance(data.get("tool_versions"), dict):
            data["tool_versions"] = {}
        if not isinstance(data.get("tools_last_checked_at"), (int, float)):
            data["tools_last_checked_at"] = 0
        return data

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _get_last_locres_for_pak(self, pak_file):
        return self.state.get("last_locres_by_pak", {}).get(str(Path(pak_file).resolve()), "")

    def _set_last_locres_for_pak(self, pak_file, locres_relative):
        self.state.setdefault("last_locres_by_pak", {})[str(Path(pak_file).resolve())] = locres_relative
        self._save_state()

    def _save_manifest(self, data):
        MANIFEST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_manifest(self):
        if not MANIFEST_FILE.is_file():
            raise RuntimeError(self.tr_text("missing_manifest"))
        return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))

    def _require_file(self, text_path, label):
        path = Path(text_path).expanduser()
        if not path.is_file():
            raise RuntimeError(self.tr_text("not_found").format(label=label, path=path))
        return path

    def _require_dir(self, text_path, label):
        path = Path(text_path).expanduser()
        if not path.is_dir():
            raise RuntimeError(self.tr_text("not_dir").format(label=label, path=path))
        return path

    def _require_pak(self, text_path, label):
        path = self._require_file(text_path, label)
        if path.suffix.lower() != ".pak":
            raise RuntimeError(self.tr_text("pak_must_be").format(label=label, path=path))
        return path

    def _require_csv(self, text_path, label):
        path = self._require_file(text_path, label)
        if path.suffix.lower() != ".csv":
            raise RuntimeError(self.tr_text("csv_must_be").format(label=label, path=path))
        return path

    def _is_tool_file_healthy(self, path, require_exec=False):
        try:
            if not path.is_file() or path.stat().st_size <= 0:
                return False
            if require_exec and not os.access(path, os.X_OK):
                return False
            return True
        except OSError:
            return False

    def _is_mono_healthy(self):
        mono_path = shutil.which("mono")
        if not mono_path:
            return False
        try:
            result = subprocess.run([mono_path, "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def _normalize_version(self, value):
        if value is None:
            return ""
        return str(value).strip().lstrip("v")

    def _version_sort_key(self, value):
        normalized = self._normalize_version(value)
        parts = []
        token = ""
        for char in normalized:
            if char.isdigit():
                token += char
            else:
                if token:
                    parts.append(int(token))
                    token = ""
        if token:
            parts.append(int(token))
        return tuple(parts)

    def _is_update_available(self, current_version, latest_version):
        current = self._normalize_version(current_version)
        latest = self._normalize_version(latest_version)
        if not current or not latest:
            return False
        current_key = self._version_sort_key(current)
        latest_key = self._version_sort_key(latest)
        if current_key and latest_key and current_key != latest_key:
            return latest_key > current_key
        return latest != current

    def _latest_release_versions(self):
        versions = {"repak": "", "unreallocres": ""}
        try:
            repak_release = self._download_json(REPAK_RELEASE_API)
            versions["repak"] = self._normalize_version(repak_release.get("tag_name", ""))
        except Exception:
            pass
        try:
            unreal_release = self._download_json(UNREAL_LOCRES_RELEASE_API)
            versions["unreallocres"] = self._normalize_version(unreal_release.get("tag_name", ""))
        except Exception:
            pass
        return versions

    def _tool_status_badge(self, state):
        if state == "ok":
            return '<span style="color:#16a34a; font-weight:700;">✔</span>'
        if state == "update":
            return '<span style="color:#f59e0b; font-weight:700;">▲</span>'
        return '<span style="color:#dc2626; font-weight:700;">!</span>'

    def _build_tool_check_detail(self, check_updates):
        latest_versions = self._latest_release_versions() if check_updates else {"repak": "", "unreallocres": ""}
        runtime_versions = self._runtime_tool_versions()
        tool_details = []

        mono_state = "ok" if self._is_mono_healthy() else "missing"
        tool_details.append(
            f"{self._tool_status_badge(mono_state)} {self.tr_text('tool_mono')}"
        )

        repak_bin = self._get_repak_bin()
        repak_ok = self._is_tool_file_healthy(repak_bin, require_exec=True)
        repak_state = "ok"
        if not repak_ok:
            repak_state = "missing"
        elif check_updates and self._is_update_available(runtime_versions.get("repak", ""), latest_versions.get("repak", "")):
            repak_state = "update"
        repak_suffix = ""
        if repak_state == "update":
            repak_suffix = f" ({self.tr_text('tool_update_available')})"
        tool_details.append(
            f"{self._tool_status_badge(repak_state)} {self.tr_text('tool_repak')}{repak_suffix}"
        )

        unreal_exe = self._get_unreal_locres_exe()
        unreal_ok = self._is_tool_file_healthy(unreal_exe, require_exec=False)
        unreal_state = "ok"
        if not unreal_ok:
            unreal_state = "missing"
        elif check_updates and self._is_update_available(runtime_versions.get("unreallocres", ""), latest_versions.get("unreallocres", "")):
            unreal_state = "update"
        unreal_suffix = ""
        if unreal_state == "update":
            unreal_suffix = f" ({self.tr_text('tool_update_available')})"
        tool_details.append(
            f"{self._tool_status_badge(unreal_state)} {self.tr_text('tool_unreallocres')}{unreal_suffix}"
        )

        return " | ".join(tool_details)

    def _runtime_tool_versions(self):
        return self.state.setdefault("tool_versions", {})

    def _get_repak_bin(self):
        if RUNTIME_REPAK_BIN.is_file():
            return RUNTIME_REPAK_BIN
        return REPAK_BIN

    def _get_unreal_locres_exe(self):
        if RUNTIME_UNREAL_LOCRES_EXE.is_file():
            return RUNTIME_UNREAL_LOCRES_EXE
        return UNREAL_LOCRES_EXE

    def _current_tool_version_text(self, key, runtime_path, bundled_path):
        version = self._runtime_tool_versions().get(key)
        if version:
            return version
        active_path = runtime_path if runtime_path.is_file() else bundled_path
        if active_path == bundled_path and bundled_path.is_file():
            return self.tr_text("bundled_version")
        return self.tr_text("unknown_version")

    def _download_json(self, url):
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "LULT",
            },
        )
        with urlopen(request, timeout=GITHUB_API_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))

    def _download_file(self, url, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        request = Request(url, headers={"User-Agent": "LULT"})
        with urlopen(request, timeout=GITHUB_API_TIMEOUT) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)

    def _repak_asset_name(self):
        machine = platform.machine().lower()
        if machine in {"x86_64", "amd64"}:
            return "repak_cli-x86_64-unknown-linux-gnu.tar.xz"
        raise RuntimeError(self.tr_text("repak_asset_missing").format(arch=platform.machine()))

    def _extract_repak_archive(self, archive_path, destination):
        with tarfile.open(archive_path, "r:*") as archive:
            members = [member for member in archive.getmembers() if member.isfile() and Path(member.name).name in {"repak", "repak_cli"}]
            if not members:
                raise RuntimeError(self.tr_text("repak_asset_missing").format(arch=platform.machine()))
            extracted = archive.extractfile(members[0])
            if extracted is None:
                raise RuntimeError(self.tr_text("repak_asset_missing").format(arch=platform.machine()))
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as handle:
                shutil.copyfileobj(extracted, handle)
        destination.chmod(0o755)

    def _update_repak_from_github(self):
        release = self._download_json(REPAK_RELEASE_API)
        asset_name = self._repak_asset_name()
        asset = next((item for item in release.get("assets", []) if item.get("name") == asset_name), None)
        if asset is None:
            raise RuntimeError(self.tr_text("repak_asset_missing").format(arch=platform.machine()))

        version = str(release.get("tag_name", "")).lstrip("v") or self.tr_text("unknown_version")
        if RUNTIME_REPAK_BIN.is_file() and self._runtime_tool_versions().get("repak") == version:
            return version

        with tempfile.TemporaryDirectory(prefix="lult-repak-") as temp_dir:
            archive_path = Path(temp_dir) / asset_name
            self._download_file(asset.get("browser_download_url", ""), archive_path)
            self._extract_repak_archive(archive_path, RUNTIME_REPAK_BIN)

        self._runtime_tool_versions()["repak"] = version
        self._save_state()
        return version

    def _update_unreal_locres_from_github(self):
        release = self._download_json(UNREAL_LOCRES_RELEASE_API)
        asset = next((item for item in release.get("assets", []) if item.get("name") == "UnrealLocres.exe"), None)
        if asset is None:
            raise RuntimeError(self.tr_text("unreal_asset_missing"))

        version = str(release.get("tag_name", "")) or self.tr_text("unknown_version")
        if RUNTIME_UNREAL_LOCRES_EXE.is_file() and self._runtime_tool_versions().get("unreallocres") == version:
            return version

        with tempfile.TemporaryDirectory(prefix="lult-unreallocres-") as temp_dir:
            temp_exe = Path(temp_dir) / "UnrealLocres.exe"
            self._download_file(asset.get("browser_download_url", ""), temp_exe)
            RUNTIME_UNREAL_LOCRES_EXE.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_exe, RUNTIME_UNREAL_LOCRES_EXE)

        self._runtime_tool_versions()["unreallocres"] = version
        self._save_state()
        return version

    def _should_refresh_runtime_tools(self):
        last_checked = float(self.state.get("tools_last_checked_at", 0) or 0)
        if not RUNTIME_REPAK_BIN.is_file() or not RUNTIME_UNREAL_LOCRES_EXE.is_file():
            return True
        return (time.time() - last_checked) >= TOOLS_REFRESH_INTERVAL_SECONDS

    def _refresh_runtime_tools(self):
        if not self._should_refresh_runtime_tools():
            return self.tr_text("auto_check").format(
                unreal_version=self._current_tool_version_text("unreallocres", RUNTIME_UNREAL_LOCRES_EXE, UNREAL_LOCRES_EXE),
                repak_version=self._current_tool_version_text("repak", RUNTIME_REPAK_BIN, REPAK_BIN),
            )

        errors = []
        for updater in (self._update_repak_from_github, self._update_unreal_locres_from_github):
            try:
                updater()
            except (HTTPError, URLError, TimeoutError, RuntimeError, OSError) as exc:
                errors.append(str(exc))

        self.state["tools_last_checked_at"] = time.time()
        self._save_state()

        if not self._get_repak_bin().is_file() or not self._get_unreal_locres_exe().is_file():
            detail = errors[0] if errors else self.tr_text("unknown_version")
            raise RuntimeError(self.tr_text("tool_update_download_failed").format(message=detail))

        return self.tr_text("auto_check").format(
            unreal_version=self._current_tool_version_text("unreallocres", RUNTIME_UNREAL_LOCRES_EXE, UNREAL_LOCRES_EXE),
            repak_version=self._current_tool_version_text("repak", RUNTIME_REPAK_BIN, REPAK_BIN),
        )

    def _ensure_tools(self, allow_updates=False):
        if not shutil.which("mono"):
            raise RuntimeError(self.tr_text("need_mono"))
        if allow_updates:
            self._refresh_runtime_tools()
        unreal_locres_exe = self._get_unreal_locres_exe()
        if not unreal_locres_exe.is_file():
            raise RuntimeError(self.tr_text("need_unreal").format(path=unreal_locres_exe))
        if self._get_repak_bin().is_file():
            return
        if not (REPAK_SRC / "Cargo.toml").is_file():
            raise RuntimeError(self.tr_text("need_repak_src").format(path=REPAK_SRC))
        if not shutil.which("cargo"):
            raise RuntimeError(self.tr_text("need_cargo"))
        self._run_command(["cargo", "build", "--release"], cwd=str(REPAK_SRC))
        if not self._get_repak_bin().is_file():
            raise RuntimeError(self.tr_text("build_failed").format(path=REPAK_BIN))

    def _list_locres_in_pak(self, pak_file):
        output = self._run_command([str(self._get_repak_bin()), "list", str(pak_file)])
        found = []
        for raw in output.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.lower().endswith(".locres"):
                found.append(line)
                continue
            for token in line.split():
                if token.lower().endswith(".locres"):
                    found.append(token)
                    break
        return list(dict.fromkeys(found))

    def _prompt_locres_choice(self, input_pak):
        self._ensure_tools()
        locres_entries = self._list_locres_in_pak(input_pak)
        if not locres_entries:
            raise RuntimeError(self.tr_text("missing_locres_in_pak"))

        selected_relative = locres_entries[0]
        if len(locres_entries) > 1:
            default_choice = self._get_last_locres_for_pak(input_pak)
            default_index = locres_entries.index(default_choice) if default_choice in locres_entries else 0
            choice, ok = QInputDialog.getItem(
                self,
                self.tr_text("locres_pick_title"),
                self.tr_text("locres_pick_text"),
                locres_entries,
                default_index,
                False,
            )
            if not ok or not choice:
                return None
            selected_relative = choice

        self._set_last_locres_for_pak(input_pak, selected_relative)
        return selected_relative

    def _open_path(self, path, fail_if_unopened=False):
        target = Path(path).expanduser()
        if not target.exists():
            if fail_if_unopened:
                raise RuntimeError(self.tr_text("open_failed").format(path=target))
            return False

        launchers = []
        if platform.system() == "Linux":
            launchers = [["xdg-open", str(target)], ["gio", "open", str(target)]]
        elif platform.system() == "Darwin":
            launchers = [["open", str(target)]]
        elif platform.system() == "Windows":
            try:
                os.startfile(str(target))
                return True
            except Exception:
                launchers = [["cmd", "/c", "start", "", str(target)]]

        for command in launchers:
            if shutil.which(command[0]) is None:
                continue
            try:
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode == 0:
                    return True
            except Exception:
                continue

        if fail_if_unopened:
            raise RuntimeError(self.tr_text("open_failed").format(path=target))
        return False

    def auto_check_tools(self):
        def task(progress, set_field):
            progress(20)
            self._refresh_runtime_tools()
            self._ensure_tools()
            progress(100)
            return self._build_tool_check_detail(check_updates=True)

        self._run_task("Kontrola nástrojů", task, auto_check=True)

    def extract_locres(self):
        try:
            input_pak = self._require_pak(self.input_pak_edit.text(), self.tr_text("input_label"))
            extract_all_mode = self.extract_all_checkbox.isChecked()
            if extract_all_mode:
                self._ensure_tools()
                locres_entries = self._list_locres_in_pak(input_pak)
                if not locres_entries:
                    raise RuntimeError(self.tr_text("missing_locres_in_pak"))
                selected_relative = ""
            else:
                locres_entries = []
                selected_relative = self._prompt_locres_choice(input_pak)
        except Exception as exc:
            QMessageBox.critical(self, self.tr_text("error_title"), str(exc))
            return

        if not extract_all_mode and not selected_relative:
            return

        def task(progress, set_field):
            self._ensure_tools()

            extract_root = input_pak.parent / f"{input_pak.stem}_unpacked"
            work_root = input_pak.parent / f"{input_pak.stem}_locres_work"

            if extract_root.exists():
                shutil.rmtree(extract_root)
            if work_root.exists():
                shutil.rmtree(work_root)

            extract_root.mkdir(parents=True, exist_ok=True)
            work_root.mkdir(parents=True, exist_ok=True)

            progress(20)
            progress(40)
            self._run_command([str(self._get_repak_bin()), "unpack", str(input_pak), "--output", str(extract_root)])

            if extract_all_mode:
                items = []
                total = max(1, len(locres_entries))
                for index, relative in enumerate(locres_entries, start=1):
                    locres_in_tree = extract_root / relative
                    if not locres_in_tree.is_file():
                        raise RuntimeError(self.tr_text("selected_after_extract_missing").format(path=locres_in_tree))

                    working_locres = work_root / relative
                    working_locres.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(locres_in_tree, working_locres)

                    csv_path = working_locres.with_suffix(".csv")
                    self._run_command(["mono", str(self._get_unreal_locres_exe()), "export", str(working_locres), "-o", str(csv_path)])
                    if not csv_path.is_file():
                        raise RuntimeError(self.tr_text("csv_missing_after_export").format(path=csv_path))

                    items.append(
                        {
                            "relative": relative,
                            "working_locres": str(working_locres),
                            "working_csv": str(csv_path),
                        }
                    )
                    progress(40 + int((index / total) * 55))

                manifest = {
                    "mode": "all",
                    "input_pak": str(input_pak),
                    "extract_root": str(extract_root),
                    "work_root": str(work_root),
                    "locres_items": items,
                }
                self._save_manifest(manifest)
                set_field("selected_locres_all", str(len(items)))
                set_field("csv_folder", str(work_root))
                self._open_path(work_root)
                progress(100)
                return self.tr_text("extract_all_done")

            selected_in_tree = extract_root / selected_relative
            if not selected_in_tree.is_file():
                raise RuntimeError(self.tr_text("selected_after_extract_missing").format(path=selected_in_tree))

            working_locres = work_root / selected_in_tree.name
            shutil.copy2(selected_in_tree, working_locres)

            progress(65)
            csv_path = working_locres.with_suffix(".csv")
            self._run_command(["mono", str(self._get_unreal_locres_exe()), "export", str(working_locres), "-o", str(csv_path)])

            if not csv_path.is_file():
                raise RuntimeError(self.tr_text("csv_missing_after_export").format(path=csv_path))

            manifest = {
                "mode": "single",
                "input_pak": str(input_pak),
                "extract_root": str(extract_root),
                "work_root": str(work_root),
                "selected_locres_relative": selected_relative,
                "working_locres": str(working_locres),
                "working_csv": str(csv_path),
            }
            self._save_manifest(manifest)

            set_field("selected_locres", str(working_locres))
            set_field("csv", str(csv_path))
            self._open_path(csv_path)
            progress(100)
            return self.tr_text("extract_done")

        self._run_task(self.tr_text("extract_button"), task)

    def import_and_pack(self):
        def task(progress, set_field):
            self._ensure_tools()
            manifest = self._load_manifest()

            input_pak = self._require_pak(manifest["input_pak"], self.tr_text("input_label"))
            extract_root = self._require_dir(manifest["extract_root"], self.tr_text("extract_root_label"))
            mode = manifest.get("mode", "single")
            csv_to_keep = set()

            if mode == "all":
                items = manifest.get("locres_items", [])
                if not isinstance(items, list) or not items:
                    raise RuntimeError(self.tr_text("missing_locres"))
                set_field("selected_locres_all", str(len(items)))
                set_field("csv_folder", str(manifest.get("work_root", "")))

                total = max(1, len(items))
                for index, item in enumerate(items, start=1):
                    selected_relative = item.get("relative", "")
                    if not selected_relative:
                        raise RuntimeError(self.tr_text("missing_locres"))
                    working_locres = self._require_file(item.get("working_locres", ""), self.tr_text("working_locres_label"))
                    csv_path = self._require_csv(item.get("working_csv", ""), self.tr_text("csv_label"))
                    csv_to_keep.add(csv_path)

                    self._run_command(
                        [
                            "mono",
                            str(self._get_unreal_locres_exe()),
                            "import",
                            str(working_locres),
                            str(csv_path),
                            "-o",
                            str(working_locres),
                        ]
                    )

                    target_locres = extract_root / selected_relative
                    target_locres.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(working_locres, target_locres)
                    progress(20 + int((index / total) * 45))
            else:
                selected_relative = manifest.get("selected_locres_relative", "")
                if not selected_relative:
                    raise RuntimeError(self.tr_text("missing_locres"))

                working_locres = self._require_file(manifest.get("working_locres", ""), self.tr_text("working_locres_label"))
                csv_path = self._require_csv(manifest.get("working_csv", ""), self.tr_text("csv_label"))
                csv_to_keep.add(csv_path)
                set_field("selected_locres", str(working_locres))
                set_field("csv", str(csv_path))

                progress(25)
                self._run_command(
                    [
                        "mono",
                        str(self._get_unreal_locres_exe()),
                        "import",
                        str(working_locres),
                        str(csv_path),
                        "-o",
                        str(working_locres),
                    ]
                )

                target_locres = extract_root / selected_relative
                target_locres.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(working_locres, target_locres)

            progress(65)
            self._run_command([str(self._get_repak_bin()), "pack", str(extract_root)])

            generated_pak = Path(f"{extract_root}.pak")
            if not generated_pak.is_file():
                raise RuntimeError(self.tr_text("pack_missing").format(path=generated_pak))

            output_pak = input_pak.with_name(f"{input_pak.stem}_P{input_pak.suffix}")
            shutil.copy2(generated_pak, output_pak)

            if self.cleanup_checkbox.isChecked():
                try:
                    generated_pak.unlink(missing_ok=True)
                except Exception:
                    pass

                work_root = Path(manifest.get("work_root", ""))
                if work_root.is_dir():
                    for path in sorted(work_root.rglob("*"), reverse=True):
                        if path in csv_to_keep:
                            continue
                        if path.is_file():
                            path.unlink(missing_ok=True)
                        elif path.is_dir():
                            shutil.rmtree(path, ignore_errors=True)

                if extract_root.is_dir():
                    shutil.rmtree(extract_root, ignore_errors=True)

            progress(100)
            return self.tr_text("import_done").format(path=output_pak)

        self._run_task(self.tr_text("import_button"), task)


def main():
    app = QApplication(sys.argv)
    if APP_ICON.is_file():
        app.setWindowIcon(QIcon(str(APP_ICON)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
