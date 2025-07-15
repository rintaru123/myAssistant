import sys
import json
import os
import re
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,QScrollArea,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QHBoxLayout, QCheckBox, QTextEdit, QSplitter,
                             QStyle, QMenu, QDialog, QFileDialog, QDialogButtonBox,
                             QRadioButton, QMessageBox, QSpinBox, QInputDialog, QComboBox,
                             QFontComboBox, QButtonGroup, QColorDialog, QStackedLayout, QTabWidget)
from PyQt6.QtCore import Qt, QPoint, QUrl, QPropertyAnimation, QEasingCurve, pyqtSignal, QByteArray, QSize, QTimer, QEvent, QParallelAnimationGroup, QObject
from PyQt6.QtGui import QAction, QMouseEvent, QPalette, QKeyEvent, QPainter, QPixmap, QColor, QFont, QIcon, QTextCursor, QScreen
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# --- Константы ---
SETTINGS_FILE = "settings.json"
DATA_FILE = "data.json"
BACKUP_FILE = "data.json.bak"
DEFAULT_SETTINGS = {
    "language": "ru_RU",
    "theme": "light", "trigger_pos": "right", "accent_color": "#00aa00",
    "light_theme_bg": "#f8f9fa", "light_theme_text": "#212529", "light_theme_list_text": "#212529",
    "dark_theme_bg": "#2b2b2b", "dark_theme_text": "#bbbbbb", "dark_theme_list_text": "#bbbbbb",
    "zen_bg_path": "wallpapers/прогулка.jpg", "zen_editor_transparent": True,
    "zen_padding_horiz": 30, "zen_padding_vert": 5,
    "zen_font_family": "Candara", "zen_font_size": 14,
    "zen_font_color": "", "zen_alignment": "left",
    "zen_first_line_indent": 20,
    "splitter_ratio": [40, 60]
}
POMODORO_WORK_TIME = 25*60
POMODORO_BREAK_TIME = 5 * 60

# --- Локализация ---
class LocalizationManager(QObject):
    language_changed = pyqtSignal()
    
    def __init__(self, default_lang='ru_RU'):
        super().__init__()
        try: base_path = sys._MEIPASS
        except AttributeError: base_path = os.path.dirname(os.path.abspath(__file__))
        self.locales_dir = os.path.join(base_path, "locales")
        self.translations = {}
        self._ensure_locales_exist()
        self.available_languages = self._scan_languages()
        self.current_lang = default_lang
        
    def _ensure_locales_exist(self):

        if not os.path.isdir(self.locales_dir):
            os.makedirs(self.locales_dir)
        
        ru_path = os.path.join(self.locales_dir, 'ru_RU.json')
        if not os.path.exists(ru_path):
            ru_data = {
                "lang_name": "Русский",
                "add_task_button": "Добавить", "new_task_placeholder": "Новая задача...",
                "hide_completed_checkbox": "Скрыть выполненные",
                "delete_note_tooltip": "Удалить заметку", "delete_task_tooltip": "Удалить задачу",
                "notes_editor_label": "Редактор заметок:", "save_button": "Сохранить",
                "new_note_button": "Новая", "zen_button": "Zen", "search_placeholder": "Поиск по тексту...",
                "all_tags_combo": "Все теги", "new_note_placeholder": "Начните писать...",
                "unsaved_changes_status": "Несохраненные изменения...", "data_saved_status": "Данные сохранены",
                "word_count_label": "Слов",
                "pomodoro_label": "Pomodoro:", "pomodoro_start_btn": "Старт", "pomodoro_pause_btn": "Пауза", "pomodoro_reset_btn": "Сброс",
                "about_menu": "О программе...", "export_menu": "Экспорт заметок в Markdown...",
                "restore_menu": "Восстановить из резервной копии...", "exit_menu": "Выход",
                "add_list_menu": "Добавить список...", "rename_list_menu": "Переименовать список...", "delete_list_menu": "Удалить список...",
                "new_list_prompt": "Введите имя нового списка:", "rename_list_prompt": "Введите новое имя для списка:", "delete_list_confirm": "Вы уверены, что хотите удалить список '{list_name}'?",
                "settings_title": "Настройки", "settings_tab_general": "Общие", "settings_tab_appearance": "Оформление", "settings_tab_zen": "Редактор Zen",
                "settings_lang_label": "Язык:", "settings_theme_label": "Основная тема:",
                "settings_light_theme": "Светлая", "settings_dark_theme": "Тёмная",
                "settings_trigger_pos_label": "Позиция кнопки:", "settings_trigger_left": "Слева", "settings_trigger_right": "Справа",
                "settings_accent_color_label": "Акцентный цвет:", "settings_choose_color_btn": "Выбрать цвет...",
                "settings_light_theme_bg_label": "Фон светлой темы:", "settings_light_theme_text_label": "Текст светлой темы:",
                "settings_dark_theme_bg_label": "Фон тёмной темы:", "settings_dark_theme_text_label": "Текст тёмной темы:",
                "settings_light_theme_list_text_label": "Текст списков (светлая):", "settings_dark_theme_list_text_label": "Текст списков (тёмная):",
                "settings_zen_bg_label": "Фон Zen:", "settings_browse_btn": "Обзор...", "settings_clear_btn": "Очистить",
                "settings_transparent_editor": "Прозрачный редактор", "settings_font_label": "Шрифт:", "settings_size_label": "Размер:",
                "settings_font_color_label": "Цвет шрифта:", "settings_alignment_label": "Выравнивание:",
                "settings_align_left": "По левому краю", "settings_align_justify": "По ширине",
                "settings_padding_horiz": "Гор. отступ (%):", "settings_padding_vert": "Верт. отступ (%):",
                "settings_first_line_indent": "Отступ 1-й строки (px):",
                "task_menu_edit": "Редактировать...",
                "task_menu_toggle_completed": "Отметить/Снять отметку"
            }
            with open(ru_path, 'w', encoding='utf-8') as f: json.dump(ru_data, f, ensure_ascii=False, indent=2)

        en_path = os.path.join(self.locales_dir, 'en_US.json')
        if not os.path.exists(en_path):
            en_data = {
                "lang_name": "English", "add_task_button": "Add", "new_task_placeholder": "New task...", "hide_completed_checkbox": "Hide completed",
                "delete_note_tooltip": "Delete note", "delete_task_tooltip": "Delete task", "notes_editor_label": "Notes Editor:", "save_button": "Save",
                "new_note_button": "New", "zen_button": "Zen", "search_placeholder": "Search in text...", "all_tags_combo": "All tags",
                "new_note_placeholder": "Start writing...", "unsaved_changes_status": "Unsaved changes...", "data_saved_status": "Data saved",
                "word_count_label": "Words", "pomodoro_label": "Pomodoro:", "pomodoro_start_btn": "Start", "pomodoro_pause_btn": "Pause", "pomodoro_reset_btn": "Reset",
                "about_menu": "About...", "export_menu": "Export Notes to Markdown...", "restore_menu": "Restore from Backup...", "exit_menu": "Exit",
                "add_list_menu": "Add List...", "rename_list_menu": "Rename List...", "delete_list_menu": "Delete List...",
                "new_list_prompt": "Enter new list name:", "rename_list_prompt": "Enter new name for the list:", "delete_list_confirm": "Are you sure you want to delete list '{list_name}'?",
                "settings_title": "Settings", "settings_tab_general": "General", "settings_tab_appearance": "Appearance", "settings_tab_zen": "Zen Editor",
                "settings_lang_label": "Language:", "settings_theme_label": "Main theme:", "settings_light_theme": "Light", "settings_dark_theme": "Dark",
                "settings_trigger_pos_label": "Button position:", "settings_trigger_left": "Left", "settings_trigger_right": "Right",
                "settings_accent_color_label": "Accent color:", "settings_choose_color_btn": "Choose color...",
                "settings_light_theme_bg_label": "Light theme BG:", "settings_light_theme_text_label": "Light theme Text:", "settings_dark_theme_bg_label": "Dark theme BG:",
                "settings_dark_theme_text_label": "Dark theme Text:", "settings_light_theme_list_text_label": "List text (light):", "settings_dark_theme_list_text_label": "List text (dark):",
                "settings_zen_bg_label": "Zen Background:", "settings_browse_btn": "Browse...", "settings_clear_btn": "Clear",
                "settings_transparent_editor": "Transparent editor", "settings_font_label": "Font:", "settings_size_label": " :", "settings_font_color_label": "Font Color:",
                "settings_alignment_label": "Alignment:", "settings_align_left": "Left", "settings_align_justify": "Justify",
                "settings_padding_horiz": "Horiz. Padding (%):", "settings_padding_vert": "Vert. Padding (%):", "settings_first_line_indent": "1st line indent (px):",
                "task_menu_edit": "Edit...", "task_menu_toggle_completed": "Toggle completed"
            }
            with open(en_path, 'w', encoding='utf-8') as f: json.dump(en_data, f, ensure_ascii=False, indent=2)

    def _scan_languages(self):
        langs = {}
        if not os.path.isdir(self.locales_dir): return {}
        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]
                try:
                    with open(os.path.join(self.locales_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        langs[lang_code] = data.get("lang_name", lang_code)
                except Exception as e: print(f"Could not load language file {filename}: {e}")
        return langs
        
    def set_language(self, lang_code):
        path = os.path.join(self.locales_dir, f"{lang_code}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                self.current_lang = lang_code
                self.language_changed.emit()
            except Exception as e: print(f"Error loading language {lang_code}: {e}")
        else: print(f"Language file for {lang_code} not found.")

    def get(self, key, default_text=""):
        return self.translations.get(key, default_text or key)


class NoteEditor(QTextEdit):
    save_and_new_requested = pyqtSignal()
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.save_and_new_requested.emit()
        else: super().keyPressEvent(event)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setFixedSize(450, 400)
        layout = QVBoxLayout(self)
        info_label = QLabel("<h3>Мой Ассистент v1.1</h3>"
                            "<p>Эта программа была создана в рамках совместной работы пользователя и AI-ассистента от Google.</p>"
                            "<p><b>Разработчик:</b> Rintaru123</p>"
                            "<p><b>AI-ассистент:</b> Google</p>"
                            "<hr>"
                            "<h4>Лицензии используемых компонентов:</h4>"
                            "<p>Программа написана с использованием фреймворка <b>PyQt6</b>, который распространяется под лицензией <b>GPL v3</b></p>"
                            "<p>Лицензия кода <b>MIT</b>.</p>"
                            "<p>Иконки предоставлены Qt Framework.</p>"
                            "<hr>"
                            "<p>Лицензии на аудиоматериалы:</p>"
                            
                            "<p>Purple Dream by Ghostrifter <a target='_blank' href='https://bit.ly/ghostrifter-yt'>bit.ly/ghostrifter-yt</a><br>"
                            "Creative Commons — Attribution-NoDerivs 3.0 Unported — CC BY-ND 3.0<br>"
                            "Music promoted by <a target='_blank' href='https://www.chosic.com/free-music/all/'>https://www.chosic.com/free-music/all/ </a></p>"
                            
                            "<p>Transcendence by Alexander Nakarada | <a target='_blank' href='https://creatorchords.com'>https://creatorchords.com</a><br>"
                            "Music promoted by <a target='_blank' href='https://www.chosic.com/free-music/all/'>https://www.chosic.com/free-music/all/</a><br>"
                            "Creative Commons CC BY 4.0<br>"
                            "<a target='_blank' href='https://creativecommons.org/licenses/by/4.0/'>https://creativecommons.org/licenses/by/4.0/</a></p>"

                            "<p>Meanwhile by Scott Buckley | <a target='_blank' href='www.scottbuckley.com.au'>www.scottbuckley.com.au</a><br>"
                            "Music promoted by <a target='_blank' href='https://www.chosic.com/free-music/all/'>https://www.chosic.com/free-music/all/</a><br>"
                            "Creative Commons CC BY 4.0<br>"
                            "<a target='_blank' href='https://creativecommons.org/licenses/by/4.0/'>https://creativecommons.org/licenses/by/4.0/</a></p>"
                            
                            "<p>Shadows And Dust by Scott Buckley | <a target='_blank' href='www.scottbuckley.com.au'>www.scottbuckley.com.au</a><br>"
                            "Music promoted by <a target='_blank' href='https://www.chosic.com/free-music/all/'>https://www.chosic.com/free-music/all/</a><br>"
                            "Creative Commons CC BY 4.0<br>"
                            "<a target='_blank' href='https://creativecommons.org/licenses/by/4.0/'>https://creativecommons.org/licenses/by/4.0/</a></p>"
                            
                            "<p>Silent Wood by Purrple Cat | <a target='_blank' href='https://purrplecat.com/'>https://purrplecat.com/</a><br>"
                            "Music promoted by <a target='_blank' href='https://www.chosic.com/free-music/all/'>https://www.chosic.com/free-music/all/</a><br>"
                            "Creative Commons CC BY-SA 3.0<br>"
                            "<a target='_blank' href='https://creativecommons.org/licenses/by-sa/3.0/'>https://creativecommons.org/licenses/by-sa/3.0/</a></p>"
                            "<p><a target='_blank' href='https://icons8.com/icon/gkW5yexEuzan/left-handed'>Левша</a> иконка от <a target='_blank' href='https://icons8.com'>Icons8</a></p>")

        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(info_label)
        layout.addWidget(scroll_area)

        info_label.setOpenExternalLinks(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class TasksPanel(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.loc = data_manager.loc_manager
        self.task_lists = {}
        self.current_list_name = ""
        self.list_names = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        add_task_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.add_button = QPushButton()
        self.add_button.clicked.connect(self.add_task_from_input)
        self.task_input.returnPressed.connect(self.add_task_from_input)
        add_task_layout.addWidget(self.task_input)
        add_task_layout.addWidget(self.add_button)
        
        list_mgmt_layout = QHBoxLayout()
        list_mgmt_layout.setSpacing(5)
        self.prev_list_btn = QPushButton("<"); self.prev_list_btn.setFixedSize(30, 24)
        self.prev_list_btn.clicked.connect(lambda: self.switch_list(-1))
        self.list_name_label = QLabel(); self.list_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_name_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_name_label.customContextMenuRequested.connect(self.show_list_context_menu)
        self.next_list_btn = QPushButton(">"); self.next_list_btn.setFixedSize(30, 24)
        self.next_list_btn.clicked.connect(lambda: self.switch_list(1))
        self.hide_completed_checkbox = QCheckBox()
        self.hide_completed_checkbox.stateChanged.connect(self.filter_tasks)
        list_mgmt_layout.addWidget(self.prev_list_btn); list_mgmt_layout.addWidget(self.list_name_label, 1); list_mgmt_layout.addWidget(self.next_list_btn); list_mgmt_layout.addStretch(); list_mgmt_layout.addWidget(self.hide_completed_checkbox)

        self.task_list_widget = QListWidget()
        self.task_list_widget.setObjectName("TaskList") # Уникальное имя для стилизации
        self.task_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list_widget.customContextMenuRequested.connect(self.show_task_context_menu)
        self.task_list_widget.itemDoubleClicked.connect(self.edit_task)
        self.task_list_widget.itemClicked.connect(self.toggle_task_completion) # Клик по элементу для отметки

        layout.addLayout(add_task_layout)
        layout.addLayout(list_mgmt_layout)
        layout.addWidget(self.task_list_widget)

    def retranslate_ui(self):
        self.add_button.setText(self.loc.get("add_task_button"))
        self.task_input.setPlaceholderText(self.loc.get("new_task_placeholder"))
        self.hide_completed_checkbox.setText(self.loc.get("hide_completed_checkbox"))
        self.list_name_label.setToolTip(self.loc.get("list_management_tooltip", "Клик правой кнопкой для управления списками"))
    
    def add_task(self, text, is_completed=False):
        if not text: return
        item = QListWidgetItem()
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setData(Qt.ItemDataRole.UserRole, {"text": text, "completed": is_completed})
        item.setSizeHint(QSize(0, 32))
        self.update_task_item_style(item)
        self.task_list_widget.addItem(item)
        self.filter_tasks()

    def update_task_item_style(self, item):
        task_data = item.data(Qt.ItemDataRole.UserRole)
        is_completed = task_data.get("completed", False)
        font = item.font()
        font.setStrikeOut(is_completed)
        #font.setUnderline(is_completed) # Подчеркивание
        item.setFont(font)

        settings = self.data_manager.get_settings()
        is_dark = settings.get("theme") == "dark"
        base_color_hex = settings.get("dark_theme_list_text") if is_dark else settings.get("light_theme_list_text")
        final_color = QColor(base_color_hex)

        if is_completed:
            final_color.setAlpha(120)

        item.setForeground(final_color)
        item.setText(task_data.get("text", ""))
        item.setCheckState(Qt.CheckState.Checked if is_completed else Qt.CheckState.Unchecked)

    def filter_tasks(self, state=None):
        hide = self.hide_completed_checkbox.isChecked()
        for i in range(self.task_list_widget.count()):
            item = self.task_list_widget.item(i)
            task_data = item.data(Qt.ItemDataRole.UserRole)
            if task_data: item.setHidden(hide and task_data.get("completed", False))
            
    def add_task_from_input(self):
        task_text = self.task_input.text().strip()
        if task_text:
            self.add_task(task_text)
            self.task_input.clear()
            self.data_manager.save_app_data()

    def show_task_context_menu(self, pos):
        item = self.task_list_widget.itemAt(pos)
        if not item: return

        menu = QMenu(self)
        menu.addAction(self.loc.get("task_menu_edit"), lambda: self.edit_task(item))
        menu.addAction(self.loc.get("task_menu_toggle_completed"), lambda: self.toggle_task_completion(item))
        menu.addSeparator()
        menu.addAction(self.loc.get("delete_task_tooltip"), lambda: self.delete_task(item))
        menu.exec(self.task_list_widget.mapToGlobal(pos))
    
    def edit_task(self, item):
        if not item: return
        task_data = item.data(Qt.ItemDataRole.UserRole)
        old_text = task_data.get("text", "")
        new_text, ok = QInputDialog.getText(self, self.loc.get("task_menu_edit"), self.loc.get("rename_list_prompt"), QLineEdit.EchoMode.Normal, old_text)
        if ok and new_text and new_text.strip() != old_text:
            task_data["text"] = new_text.strip()
            item.setData(Qt.ItemDataRole.UserRole, task_data)
            self.update_task_item_style(item)
            self.data_manager.save_app_data()
    
    def toggle_task_completion(self, item):
        if not item: return
        task_data = item.data(Qt.ItemDataRole.UserRole)
        task_data["completed"] = not task_data.get("completed", False)
        item.setData(Qt.ItemDataRole.UserRole, task_data)
        self.update_task_item_style(item)
        self.filter_tasks()
        self.data_manager.save_app_data()

    def delete_task(self, item):
        row = self.task_list_widget.row(item)
        if row >= 0:
            self.task_list_widget.takeItem(row)
            self.data_manager.save_app_data()

    def get_task_lists_data(self):
        if self.current_list_name and self.current_list_name in self.task_lists:
            self.task_lists[self.current_list_name] = [self.task_list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.task_list_widget.count())]
        return self.task_lists

    def load_task_lists(self, task_lists_data, active_list_name):
        self.task_lists = task_lists_data if task_lists_data else {"Default": []}
        self.list_names = sorted(self.task_lists.keys())
        self.current_list_name = active_list_name if active_list_name in self.list_names else (self.list_names[0] if self.list_names else "")
        self._load_current_list_display()

    def _load_current_list_display(self):
        self.task_list_widget.clear()
        if not self.current_list_name: return
        self.list_name_label.setText(f"<b>{self.current_list_name}</b>")
        tasks = self.task_lists.get(self.current_list_name, [])
        for t in tasks: self.add_task(t['text'], t['completed'])
        self.filter_tasks()

    def switch_list(self, direction):
        if not self.list_names or len(self.list_names) < 2: return
        if self.current_list_name: self.task_lists[self.current_list_name] = [self.task_list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.task_list_widget.count())]
        current_index = self.list_names.index(self.current_list_name)
        new_index = (current_index + direction) % len(self.list_names)
        self.current_list_name = self.list_names[new_index]
        self._load_current_list_display()
        self.data_manager.save_app_data()

    def show_list_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction(self.loc.get("add_list_menu"), self.add_new_list)
        if self.current_list_name: menu.addAction(self.loc.get("rename_list_menu"), self.rename_current_list)
        if len(self.list_names) > 1: menu.addAction(self.loc.get("delete_list_menu"), self.delete_current_list)
        menu.exec(self.list_name_label.mapToGlobal(pos))
    
    def add_new_list(self):
        text, ok = QInputDialog.getText(self, self.loc.get("add_list_menu"), self.loc.get("new_list_prompt"))
        if ok and text and text not in self.task_lists:
            if self.current_list_name: self.task_lists[self.current_list_name] = [self.task_list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.task_list_widget.count())]
            self.task_lists[text] = []
            self.list_names = sorted(self.task_lists.keys())
            self.current_list_name = text
            self._load_current_list_display()
            self.data_manager.save_app_data()

    def rename_current_list(self):
        text, ok = QInputDialog.getText(self, self.loc.get("rename_list_menu"), self.loc.get("rename_list_prompt"), QLineEdit.EchoMode.Normal, self.current_list_name)
        if ok and text and text != self.current_list_name and text not in self.task_lists:
            self.task_lists[text] = [self.task_list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.task_list_widget.count())]
            del self.task_lists[self.current_list_name]
            self.list_names = sorted(self.task_lists.keys())
            self.current_list_name = text
            self.list_name_label.setText(f"<b>{self.current_list_name}</b>")
            self.data_manager.save_app_data()

    def delete_current_list(self):
        if len(self.list_names) <= 1: return
        reply = QMessageBox.question(self, self.loc.get("delete_list_menu"), self.loc.get("delete_list_confirm").format(list_name=self.current_list_name))
        if reply == QMessageBox.StandardButton.Yes:
            current_index = self.list_names.index(self.current_list_name)
            del self.task_lists[self.current_list_name]
            self.list_names = sorted(self.task_lists.keys())
            new_index = max(0, current_index - 1) if current_index > 0 else 0
            self.current_list_name = self.list_names[new_index] if self.list_names else ""
            self._load_current_list_display()
            self.data_manager.save_app_data()


class NotesPanel(QWidget):
    # ... (код остается почти без изменений) ...
    zen_mode_requested = pyqtSignal(str, str)
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.loc = data_manager.loc_manager
        self.current_note_item = None
        self.saved_text = ""
        self.is_dirty = False
        self.all_tags = set()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(5)

        self.notes_editor_label = QLabel()
        self.notes_editor = NoteEditor()
        self.notes_editor.textChanged.connect(self.on_editor_text_changed)
        self.notes_editor.save_and_new_requested.connect(self.handle_save_and_new)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton()
        self.save_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.save_button.setObjectName("save_button")
        self.new_button = QPushButton()
        self.new_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.zen_button = QPushButton()
        #self.zen_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton))
        self.save_button.clicked.connect(self.save_current_note)
        self.new_button.clicked.connect(lambda: self.clear_for_new_note(force=False))
        self.zen_button.clicked.connect(self.open_zen_mode)
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.zen_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_notes)
        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.currentIndexChanged.connect(self.filter_notes)
        filter_layout.addWidget(self.search_input, 1)
        filter_layout.addWidget(self.tag_filter_combo)

        self.note_list_widget = QListWidget()
        self.note_list_widget.currentItemChanged.connect(self.display_selected_note)
        self.note_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_list_widget.customContextMenuRequested.connect(self.show_note_context_menu)

        layout.addWidget(self.notes_editor_label)
        layout.addWidget(self.notes_editor, 1)
        layout.addLayout(button_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(self.note_list_widget, 1)

    def retranslate_ui(self):
        self.notes_editor_label.setText(self.loc.get("notes_editor_label"))
        self.save_button.setText(self.loc.get("save_button"))
        self.new_button.setText(self.loc.get("new_note_button"))
        self.zen_button.setText(self.loc.get("zen_button"))
        self.search_input.setPlaceholderText(self.loc.get("search_placeholder"))
        self.notes_editor.setPlaceholderText(self.loc.get("new_note_placeholder"))
        
        current_text = self.tag_filter_combo.currentText()
        all_tags_text = self.loc.get("all_tags_combo")

        self.tag_filter_combo.blockSignals(True)
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem(all_tags_text)
        self.tag_filter_combo.addItems(sorted(list(self.all_tags)))
        
        idx = self.tag_filter_combo.findText(current_text)
        if idx != -1: self.tag_filter_combo.setCurrentIndex(idx)
        else: self.tag_filter_combo.setCurrentIndex(0)
             
        self.tag_filter_combo.blockSignals(False)
        self.filter_notes()

    def show_note_context_menu(self, pos):
        item = self.note_list_widget.itemAt(pos)
        if not item: return

        menu = QMenu(self)
        delete_action = QAction(self.loc.get("delete_note_tooltip"), self)
        delete_action.triggered.connect(lambda: self.perform_delete_note(item))
        menu.addAction(delete_action)
        menu.exec(self.note_list_widget.mapToGlobal(pos))
    
    def find_tags(self, text): return set(re.findall(r'#(\w+)', text))
    
    def update_tag_filter(self): self.retranslate_ui()

    def filter_notes(self):
        search_text = self.search_input.text().lower(); selected_tag_item_text = self.tag_filter_combo.currentText()
        is_all_tags_selected = selected_tag_item_text == self.loc.get("all_tags_combo")
        for i in range(self.note_list_widget.count()):
            item = self.note_list_widget.item(i); note_data = item.data(Qt.ItemDataRole.UserRole); note_text = note_data.get('text', ''); note_timestamp = note_data.get('timestamp', ''); text_match = search_text in (note_timestamp + ' ' + note_text).lower(); tag_match = is_all_tags_selected or (f"#{selected_tag_item_text}" in note_text); item.setHidden(not (text_match and tag_match))
    
    def display_selected_note(self, current_item, previous_item):
        if previous_item and self.is_dirty: self.save_current_note()
        if not current_item:
            if self.current_note_item is not None: self.clear_for_new_note(force=True)
            return
        self.current_note_item = current_item
        note_data = self.current_note_item.data(Qt.ItemDataRole.UserRole)
        source_text = note_data.get("text", ""); self.notes_editor.setPlainText(source_text); self.saved_text = source_text; self.on_editor_text_changed()
    
    def save_current_note(self):
        text = self.notes_editor.toPlainText().strip()
        if not self.current_note_item and not text: return
        new_tags = self.find_tags(text)
        if new_tags != self.all_tags:
            self.all_tags.update(new_tags)
            self.update_tag_filter()
        if self.current_note_item:
            note_data = self.current_note_item.data(Qt.ItemDataRole.UserRole); note_data["text"] = text; self.current_note_item.setData(Qt.ItemDataRole.UserRole, note_data)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); note_data = {"timestamp": timestamp, "text": text}; new_item = self.add_note_item(note_data); self.current_note_item = new_item; self.note_list_widget.blockSignals(True); self.note_list_widget.setCurrentItem(new_item); self.note_list_widget.blockSignals(False)
        self.saved_text = text; self.on_editor_text_changed(); self.data_manager.save_app_data()
    
    def load_notes(self, notes_data):
        self.note_list_widget.clear(); self.all_tags.clear()
        sorted_notes = sorted(notes_data, key=lambda x: x.get('timestamp', ''), reverse=True)
        for note in sorted_notes:
            self.add_note_item(note); self.all_tags.update(self.find_tags(note.get("text", "")))
        self.update_tag_filter(); self.clear_for_new_note(force=True)
    
    def open_zen_mode(self):
        self.save_if_dirty(); text = self.notes_editor.toPlainText(); timestamp = ""
        if self.current_note_item: timestamp = self.current_note_item.data(Qt.ItemDataRole.UserRole)['timestamp']
        self.zen_mode_requested.emit(text, timestamp)
    
    def find_and_select_note_by_timestamp(self, timestamp):
        if not timestamp: return
        for i in range(self.note_list_widget.count()):
            item = self.note_list_widget.item(i); note_data = item.data(Qt.ItemDataRole.UserRole)
            if note_data and note_data.get('timestamp') == timestamp:
                self.note_list_widget.setCurrentItem(item); self.note_list_widget.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter); break
    
    def clear_for_new_note(self, force=False):
        if not force and self.is_dirty: self.save_current_note()
        self.current_note_item = None
        if self.note_list_widget.currentItem() is not None: self.note_list_widget.blockSignals(True); self.note_list_widget.setCurrentItem(None); self.note_list_widget.blockSignals(False)
        self.notes_editor.clear(); self.saved_text = ""; self.on_editor_text_changed(); self.notes_editor.setPlaceholderText(self.loc.get("new_note_placeholder"))
    
    def handle_save_and_new(self): self.save_current_note(); self.clear_for_new_note(force=True)
    
    def on_editor_text_changed(self):
        self.is_dirty = (self.notes_editor.toPlainText().strip() != self.saved_text.strip()); self.data_manager.main_popup_on_data_changed()
    
    def save_if_dirty(self):
        if self.is_dirty: self.save_current_note()
    
    def add_note_item(self, note_data):
        list_item = QListWidgetItem()
        list_item.setText(note_data["timestamp"])
        list_item.setData(Qt.ItemDataRole.UserRole, note_data)
        list_item.setSizeHint(QSize(0, 32))
        self.note_list_widget.insertItem(0, list_item)
        return list_item
    
    def perform_delete_note(self, item_to_delete):
        if self.note_list_widget.currentItem() == item_to_delete:
            self.clear_for_new_note(force=True)
        row = self.note_list_widget.row(item_to_delete)
        if row >= 0:
            self.note_list_widget.takeItem(row)
            self.data_manager.save_app_data()
    
    def get_notes_data(self): return [self.note_list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.note_list_widget.count())]


class ZenModeWindow(QWidget):
    # ... (код без изменений)
    zen_exited = pyqtSignal(str); zen_saved_and_closed = pyqtSignal(str); settings_updated_for_saving = pyqtSignal(dict)
    def __init__(self, initial_text, settings, loc_manager):
        super().__init__(); self.settings = settings; self.loc = loc_manager; self.background_pixmap = None; self.player = QMediaPlayer(); self.audio_output = QAudioOutput(); self.player.setAudioOutput(self.audio_output); self.current_playing_button = None; self.playlist_mode = False; self.playlist_files = []; self.playlist_index = 0; self.player.mediaStatusChanged.connect(self.handle_media_status_change); self.pomodoro_timer = QTimer(self); self.pomodoro_timer.timeout.connect(self.update_pomodoro); self.pomodoro_time_left = POMODORO_WORK_TIME; self.is_work_time = True; self.pomodoro_running = False; self.pomodoro_player = QMediaPlayer(); self.pomodoro_audio_output = QAudioOutput(); self.pomodoro_player.setAudioOutput(self.pomodoro_audio_output)
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__)); sound_path = os.path.join(script_dir, "pomodoro_end.wav")
            if os.path.exists(sound_path): self.pomodoro_player.setSource(QUrl.fromLocalFile(sound_path))
        except NameError: pass
        self.main_layout = QVBoxLayout(self); self.main_layout.setSpacing(0); self.main_layout.setContentsMargins(0, 0, 0, 0); 
        self.pomodoro_panel = self.create_pomodoro_panel(); 
        self.editor = QTextEdit()
        self.word_count_label = QLabel("Слов: 0")
        self.audio_panel = self.create_audio_panel()
        self.settings_panel = SettingsPanel(self.settings, self.loc, self)
        
        self.main_layout.addWidget(self.pomodoro_panel)
        self.main_layout.addWidget(self.editor)
        self.main_layout.addWidget(self.word_count_label)
        self.editor.setPlainText(initial_text)

        self.settings_panel.hide()
        self.settings_panel.settings_changed.connect(self.update_zen_settings)
        self.loc.language_changed.connect(self.retranslate_ui)
        self.editor.textChanged.connect(self.update_word_count)
        self.retranslate_ui()

        self.settings_button = self.create_settings_button(); self.exit_button = self.create_exit_button(); self.editor.setFocus(); self.update_background(); self._update_styles()
    
    def retranslate_ui(self):
        self.pomodoro_title_label.setText(f"<b>{self.loc.get('pomodoro_label')}</b>")
        self.pomodoro_start_button.setText(self.loc.get('pomodoro_start_btn') if not self.pomodoro_running else self.loc.get('pomodoro_pause_btn'))
        self.pomodoro_reset_button.setText(self.loc.get('pomodoro_reset_btn'))
        self.update_word_count()
        self.settings_panel.retranslate_ui()

    def create_pomodoro_panel(self):
        panel = QWidget(); layout = QHBoxLayout(panel); layout.setContentsMargins(10, 5, 10, 5)
        self.pomodoro_title_label = QLabel()
        self.pomodoro_label = QLabel("25:00")
        self.pomodoro_start_button = QPushButton()
        self.pomodoro_reset_button = QPushButton()
        self.pomodoro_start_button.clicked.connect(self.start_pause_pomodoro)
        self.pomodoro_reset_button.clicked.connect(self.reset_pomodoro)
        layout.addWidget(self.pomodoro_title_label); layout.addWidget(self.pomodoro_label); layout.addWidget(self.pomodoro_start_button); layout.addWidget(self.pomodoro_reset_button); layout.addStretch();
        return panel
    
    def start_pause_pomodoro(self):
        self.pomodoro_running = not self.pomodoro_running
        self.retranslate_ui()
        if self.pomodoro_running: self.pomodoro_timer.start(1000)
        else: self.pomodoro_timer.stop()
        
    def reset_pomodoro(self):
        self.pomodoro_timer.stop(); self.pomodoro_running = False; self.is_work_time = True; self.pomodoro_time_left = POMODORO_WORK_TIME
        self.retranslate_ui()
        self.update_pomodoro_label()
        
    def update_pomodoro(self):
        if not self.pomodoro_running: return
        self.pomodoro_time_left -= 1; self.update_pomodoro_label()
        if self.pomodoro_time_left <= 0:
            if self.pomodoro_player.source().isValid(): self.pomodoro_player.play()
            self.is_work_time = not self.is_work_time; self.pomodoro_time_left = POMODORO_WORK_TIME if self.is_work_time else POMODORO_BREAK_TIME
    def update_pomodoro_label(self):
        mins, secs = divmod(self.pomodoro_time_left, 60); self.pomodoro_label.setText(f"{mins:02d}:{secs:02d}")
    def update_word_count(self):
        text = self.editor.toPlainText(); word_count = len(text.split()) if text else 0; self.word_count_label.setText(f"{self.loc.get('word_count_label', 'Слов')}: {word_count}")
    def create_audio_panel(self):
        panel = QWidget(self); panel.setObjectName("audioPanel"); layout = QHBoxLayout(panel); layout.setContentsMargins(10, 5, 10, 5)
        try: script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError: script_dir = os.getcwd()
        audio_dir = os.path.join(script_dir, "zen_audio"); self.playlist_files = []
        if os.path.isdir(audio_dir):
            self.playlist_files = sorted([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))])
            if self.playlist_files:
                self.playlist_button = QPushButton("▶") # Используем текстовый символ; 
                self.playlist_button.setToolTip("Запустить/Пауза плейлист"); self.playlist_button.setFixedSize(30, 30); self.playlist_button.clicked.connect(self.toggle_playlist); layout.addWidget(self.playlist_button)
                self.stop_button = QPushButton("■") ; self.stop_button.setToolTip("Остановить музыку"); self.stop_button.setFixedSize(30, 30); self.stop_button.clicked.connect(self.stop_all_music); layout.addWidget(self.stop_button)
            for i, file_path in enumerate(self.playlist_files):
                btn = QPushButton(f"{i + 1}"); btn.setFixedSize(30, 30); btn.setObjectName("audio_button"); btn.setProperty("audio_path", file_path); btn.setProperty("original_text", f"{i+1}"); btn.clicked.connect(lambda ch, b=btn: self.toggle_single_track(b)); layout.addWidget(btn)
        panel.adjustSize(); return panel
    def handle_media_status_change(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.playlist_mode: self.play_next_in_playlist()
    def toggle_playlist(self):
        if not self.playlist_mode: self.start_playlist()
        else:
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
                self.playlist_button.setText("▶")
            elif self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
                self.player.play()
                self.playlist_button.setText("❚❚")         
    def start_playlist(self):
        if not self.playlist_files: return
        self.stop_all_music(); self.playlist_mode = True; self.playlist_index = 0; self.player.setLoops(QMediaPlayer.Loops.Once); self.play_next_in_playlist(); self.playlist_button.setText("❚❚")
    def play_next_in_playlist(self):
        if self.playlist_mode and self.playlist_files:
            self.player.setSource(QUrl.fromLocalFile(self.playlist_files[self.playlist_index])); self.player.play(); self.playlist_index = (self.playlist_index + 1) % len(self.playlist_files)
        else: self.stop_all_music()
    def toggle_single_track(self, button):
        if button == self.current_playing_button:
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState: self.player.pause(); button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            elif self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState: self.player.play(); button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.stop_all_music(); self.playlist_mode = False; self.player.setLoops(QMediaPlayer.Loops.Infinite); path = button.property("audio_path"); self.player.setSource(QUrl.fromLocalFile(path)); self.player.play(); self.current_playing_button = button; button.setText(""); button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)); button.setProperty("playing", "true"); button.style().polish(button)
    def stop_all_music(self):
        self.player.stop(); self.playlist_mode = False
        if hasattr(self, 'playlist_button'):
            self.playlist_button.setText("▶")
        self.deactivate_all_buttons()
    def create_settings_button(self): 
        btn = QPushButton(self); btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)); 
        btn.setFixedSize(32, 32); btn.clicked.connect(self.toggle_settings_panel); return btn
    def create_exit_button(self): btn = QPushButton("✕", self);  btn.setFixedSize(32, 32); btn.clicked.connect(self.close); return btn; btn.setFixedSize(32, 32); btn.clicked.connect(self.close); return btn
    
    def toggle_settings_panel(self):
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
        else:
            self.settings_panel.load_settings_to_ui()
            self.settings_panel.adjustSize()
            self.settings_panel.move((self.width() - self.settings_panel.width()) // 2, (self.height() - self.settings_panel.height()) // 2)
            self.settings_panel.show()
            
    def _update_styles(self):
        hp = self.width() * self.settings.get("zen_padding_horiz", 15) // 100; vp = self.height() * self.settings.get("zen_padding_vert", 10) // 100
        font_family = self.settings.get("zen_font_family", "Georgia"); font_size = self.settings.get("zen_font_size", 18); accent_color = self.settings.get("accent_color", "#007bff")
        self.main_layout.setContentsMargins(hp, vp, hp, vp)
        is_dark = self.settings.get("theme", "dark") == "dark"; is_transparent = self.settings.get("zen_editor_transparent", True)
        
        editor_bg_str = self.settings.get("dark_theme_bg") if is_dark else self.settings.get("light_theme_bg")
        editor_bg = QColor(editor_bg_str)
        if is_transparent: editor_bg.setAlpha(20 if is_dark else 215)
        
        default_editor_color = self.settings.get("dark_theme_text") if is_dark else self.settings.get("light_theme_text")
        editor_color = self.settings.get("zen_font_color") or default_editor_color
        alignment_str = self.settings.get("zen_alignment", "left")
        alignment = Qt.AlignmentFlag.AlignJustify if alignment_str == "justify" else Qt.AlignmentFlag.AlignLeft
        self.editor.setAlignment(alignment)
        indent = self.settings.get("zen_first_line_indent", 0)
        
        editor_bg_rgba = f"rgba({editor_bg.red()}, {editor_bg.green()}, {editor_bg.blue()}, {editor_bg.alphaF()})"
        
        scrollbar_handle_color = "rgba(255, 255, 255, 0.2)" if is_dark else "rgba(0, 0, 0, 0.2)"
        scrollbar_handle_hover_color = "rgba(255, 255, 255, 0.4)" if is_dark else "rgba(0, 0, 0, 0.4)"

        editor_stylesheet = f"""
            QTextEdit {{
                background-color: {editor_bg_rgba};
                border: none;
                font-family: '{font_family}';
                font-size: {font_size}pt;
                color: {editor_color};
            }}
            
            /* Стилизация вертикальной полосы прокрутки */
            QScrollBar:vertical {{
                border: none;
                background: transparent; /* Фон самой полосы делаем прозрачным */
                width: 8px; /* Ширина */
                margin: 0px 0px 0px 0px;
            }}
            
            /* Стилизация ползунка */
            QScrollBar::handle:vertical {{
                background: {scrollbar_handle_color};
                border-radius: 4px; /* Скругляем углы */
                min-height: 25px; /* Минимальная высота ползунка */
            }}
            
            /* Ползунок при наведении */
            QScrollBar::handle:vertical:hover {{
                background: {scrollbar_handle_hover_color};
            }}
            
            /* Убираем кнопки со стрелками сверху и снизу */
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
        self.editor.setStyleSheet(editor_stylesheet)
        

        
        cursor = self.editor.textCursor()
        block_format = cursor.blockFormat()
        block_format.setTextIndent(indent)
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setBlockFormat(block_format)
        cursor.clearSelection()
        self.editor.setTextCursor(cursor)
        
        panel_bg = "rgba(0,0,0,0.5)" if is_dark else "rgba(255,255,255,0.6)"; btn_border = "rgba(255,255,255,0.7)" if is_dark else "rgba(0,0,0,0.4)"; btn_bg = "rgba(0,0,0,0.4)" if is_dark else "rgba(255,255,255,0.4)"; btn_color = "white" if is_dark else "black"; btn_hover_bg = "rgba(255,255,255,0.3)" if is_dark else "rgba(0,0,0,0.1)"
        self.audio_panel.setStyleSheet(f'QWidget#audioPanel {{ background: {panel_bg}; border-radius: 15px; }} QPushButton {{ border: 1px solid {btn_border}; border-radius: 15px; background-color: {btn_bg}; color: {btn_color}; font-size: 11pt; font-weight: bold; }} QPushButton:hover {{ background-color: {btn_hover_bg}; }} QPushButton[playing="true"] {{ background-color: {accent_color}; border-color: #ffffff; color: white; }}')
        floating_btn_bg = "rgba(30,30,30,0.5)" if is_dark else "rgba(240,240,240,0.7)"
        floating_btn_color = "#e0e0e0" if is_dark else "#333333" # Светлый крестик для тёмной темы и наоборот
        

        settings_btn_style = f"background: {floating_btn_bg}; border-radius: 16px;"
        self.settings_button.setStyleSheet(settings_btn_style)

        exit_btn_style = f"""
            QPushButton {{
                background: {floating_btn_bg}; 
                color: {floating_btn_color};
                border-radius: 16px;
                border: none;
                font-family: 'Arial'; 
                font-size: 14pt; 
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #dc3545;
                color: white;
            }}
        """
        self.exit_button.setStyleSheet(exit_btn_style)

        text_color = '#ccc' if is_dark else '#333'; pomodoro_button_bg = "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.05)"; pomodoro_style = f"background-color: transparent; border: none; font-size: 10pt; color: {text_color}; padding: 2px 5px;"
        self.pomodoro_title_label.setStyleSheet(f"background-color: transparent; color: {text_color}; font-weight:bold;"); self.pomodoro_label.setStyleSheet(f"background-color: transparent; font-size: 14pt; font-weight: bold; color: {text_color};"); self.pomodoro_start_button.setStyleSheet(pomodoro_style + f" QPushButton:hover {{ background-color: {pomodoro_button_bg}; border-radius: 5px; }}"); self.pomodoro_reset_button.setStyleSheet(pomodoro_style + f" QPushButton:hover {{ background-color: {pomodoro_button_bg}; border-radius: 5px; }}"); self.word_count_label.setStyleSheet(f"background-color: transparent; border: none; color: {text_color}; padding: 5px;")
    
    def update_background(self):
        bg_path = self.settings.get("zen_bg_path"); self.background_pixmap = QPixmap(bg_path) if bg_path and os.path.exists(bg_path) else None; self.update()
    
    def update_zen_settings(self, new_settings): 
        self.settings = new_settings
        self.settings_updated_for_saving.emit(self.settings.copy())
        self._update_styles()
        self.update_background()

    def resizeEvent(self, event):
        self.audio_panel.move(20, self.height() - self.audio_panel.height() - 20); self.settings_button.move(self.width() - self.settings_button.width() - 20, self.height() - self.settings_button.height() - 20); self.exit_button.move(self.width() - self.exit_button.width() - 20, 20)
        if self.settings_panel.isVisible(): self.settings_panel.move((self.width() - self.settings_panel.width()) // 2, (self.height() - self.settings_panel.height()) // 2)
        super().resizeEvent(event)
    def showEvent(self, event): self._update_styles(); super().showEvent(event)
    def deactivate_all_buttons(self):
        if self.current_playing_button:
            self.current_playing_button.setText(self.current_playing_button.property("original_text")); self.current_playing_button.setIcon(QIcon())
        self.current_playing_button = None
        for btn in self.audio_panel.findChildren(QPushButton, "audio_button"): btn.setProperty("playing", "false"); btn.style().polish(btn)
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F11: self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.blockSignals(True); self.zen_saved_and_closed.emit(self.editor.toPlainText())
        else: super().keyPressEvent(event)
    def closeEvent(self, event):
        self.stop_all_music(); self.pomodoro_timer.stop(); self.pomodoro_running = False
        if self.settings_panel.isVisible(): self.settings_panel.hide()
        if not self.signalsBlocked(): self.zen_exited.emit(self.editor.toPlainText())
        event.accept()
    def paintEvent(self, event):
        painter = QPainter(self)
        if self.background_pixmap: painter.drawPixmap(self.rect(), self.background_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else:
            theme_color_str = self.settings.get("dark_theme_bg") if self.settings.get("theme") == "dark" else self.settings.get("light_theme_bg")
            painter.fillRect(self.rect(), QColor(theme_color_str))


class SettingsPanel(QWidget):
    settings_changed = pyqtSignal(dict)
    def __init__(self, current_settings, loc_manager, parent=None):
        super().__init__(parent); self.settings = current_settings.copy(); self.loc = loc_manager; self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint); self.setObjectName("SettingsPanel")
        
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(15, 15, 15, 15)
        title_layout = QHBoxLayout(); self.title_label = QLabel(); title_layout.addWidget(self.title_label); title_layout.addStretch(); close_btn = QPushButton("✕"); close_btn.setFixedSize(24, 24); close_btn.clicked.connect(self.hide); title_layout.addWidget(close_btn); main_layout.addLayout(title_layout)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        self.color_widgets = {}

        self.create_general_tab()
        self.create_appearance_tab()
        self.create_zen_editor_tab()

        self.connect_signals()
        self.load_settings_to_ui()
        self.retranslate_ui()
        self.apply_styles()
        
    def create_general_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        lang_layout = QHBoxLayout(); self.lang_label = QLabel(); lang_layout.addWidget(self.lang_label); self.lang_combo = QComboBox(); lang_layout.addWidget(self.lang_combo, 1); layout.addLayout(lang_layout)
        self.theme_group = QButtonGroup(self); theme_box = QHBoxLayout(); self.theme_label = QLabel(); self.main_dark_radio = QRadioButton(); self.main_light_radio = QRadioButton(); self.theme_group.addButton(self.main_dark_radio); self.theme_group.addButton(self.main_light_radio); theme_box.addWidget(self.theme_label); theme_box.addWidget(self.main_light_radio); theme_box.addWidget(self.main_dark_radio); theme_box.addStretch(); layout.addLayout(theme_box)
        self.pos_group = QButtonGroup(self); pos_box = QHBoxLayout(); self.pos_label = QLabel(); self.trigger_left_radio = QRadioButton(); self.trigger_right_radio = QRadioButton(); self.pos_group.addButton(self.trigger_left_radio); self.pos_group.addButton(self.trigger_right_radio); pos_box.addWidget(self.pos_label); pos_box.addWidget(self.trigger_left_radio); pos_box.addWidget(self.trigger_right_radio); pos_box.addStretch(); layout.addLayout(pos_box)
        layout.addStretch()
        self.general_tab = tab
        self.tab_widget.addTab(tab, "")
    
    def create_appearance_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        
        def create_color_picker(setting_key):
            h_layout = QHBoxLayout(); label = QLabel(); swatch = QLabel(); swatch.setFixedSize(20, 20); swatch.setStyleSheet("border: 1px solid #888;"); btn = QPushButton()
            h_layout.addWidget(label, 1); h_layout.addWidget(swatch); h_layout.addWidget(btn)
            self.color_widgets[setting_key] = (label, swatch, btn)
            return h_layout
        
        layout.addLayout(create_color_picker("accent_color"))
        layout.addLayout(create_color_picker("light_theme_bg"))
        layout.addLayout(create_color_picker("light_theme_text"))
        layout.addLayout(create_color_picker("light_theme_list_text"))
        layout.addLayout(create_color_picker("dark_theme_bg"))
        layout.addLayout(create_color_picker("dark_theme_text"))
        layout.addLayout(create_color_picker("dark_theme_list_text"))

        layout.addSpacing(15)
        bg_layout = QHBoxLayout(); self.zen_bg_label = QLabel(); self.bg_path_edit = QLineEdit(); self.browse_button = QPushButton(); self.clear_bg_button = QPushButton(); bg_layout.addWidget(self.zen_bg_label); bg_layout.addWidget(self.bg_path_edit, 1); bg_layout.addWidget(self.browse_button); bg_layout.addWidget(self.clear_bg_button); layout.addLayout(bg_layout)
        self.transparent_checkbox = QCheckBox(); layout.addWidget(self.transparent_checkbox)
        layout.addStretch()
        self.appearance_tab = tab
        self.tab_widget.addTab(tab, "")
        
    def create_zen_editor_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        font_layout = QHBoxLayout(); self.font_label = QLabel(); self.font_family_combo = QFontComboBox(); self.size_label = QLabel(); self.font_size_spin = QSpinBox(); self.font_size_spin.setRange(8, 72); font_layout.addWidget(self.font_label); font_layout.addWidget(self.font_family_combo, 1); font_layout.addWidget(self.size_label); font_layout.addWidget(self.font_size_spin); layout.addLayout(font_layout)
        
        zen_color_layout = QHBoxLayout()
        self.font_color_label = QLabel()
        self.zen_font_color_swatch = QLabel(); self.zen_font_color_swatch.setFixedSize(20, 20); self.zen_font_color_swatch.setStyleSheet("border: 1px solid #888;")
        self.font_color_btn = QPushButton()
        self.clear_font_color_btn = QPushButton()
        zen_color_layout.addWidget(self.font_color_label, 1); zen_color_layout.addWidget(self.zen_font_color_swatch); zen_color_layout.addWidget(self.font_color_btn); zen_color_layout.addWidget(self.clear_font_color_btn)
        layout.addLayout(zen_color_layout)

        self.zen_align_group = QButtonGroup(self); align_layout = QHBoxLayout(); self.align_label = QLabel(); self.align_left_radio = QRadioButton(); self.align_justify_radio = QRadioButton(); self.zen_align_group.addButton(self.align_left_radio); self.zen_align_group.addButton(self.align_justify_radio); align_layout.addWidget(self.align_label); align_layout.addWidget(self.align_left_radio); align_layout.addWidget(self.align_justify_radio); align_layout.addStretch(); layout.addLayout(align_layout)
        padding_layout = QHBoxLayout(); self.horiz_pad_label = QLabel(); self.horiz_padding = QSpinBox(); self.horiz_padding.setRange(0, 40); self.vert_pad_label = QLabel(); self.vert_padding = QSpinBox(); self.vert_padding.setRange(0, 40); padding_layout.addWidget(self.horiz_pad_label); padding_layout.addWidget(self.horiz_padding); padding_layout.addWidget(self.vert_pad_label); padding_layout.addWidget(self.vert_padding); layout.addLayout(padding_layout)
        indent_layout = QHBoxLayout(); self.indent_label = QLabel(); self.first_line_indent_spin = QSpinBox(); self.first_line_indent_spin.setRange(0, 200); self.first_line_indent_spin.setSuffix(" px"); indent_layout.addWidget(self.indent_label); indent_layout.addWidget(self.first_line_indent_spin); indent_layout.addStretch(); layout.addLayout(indent_layout)
        layout.addStretch()
        self.zen_editor_tab = tab
        self.tab_widget.addTab(tab, "")

    def load_settings_to_ui(self):
        all_widgets = self.findChildren(QWidget)
        for widget in all_widgets:
            if isinstance(widget, (QComboBox, QSpinBox, QCheckBox, QLineEdit, QRadioButton, QPushButton)):
                widget.blockSignals(True)
        
        self.lang_combo.clear()
        for code, name in self.loc.available_languages.items():
            self.lang_combo.addItem(name, code)
        current_lang_code = self.settings.get("language", "ru_RU")
        if current_lang_code in self.loc.available_languages:
            self.lang_combo.setCurrentIndex(list(self.loc.available_languages.keys()).index(current_lang_code))
        
        (self.main_light_radio if self.settings.get("theme") == "light" else self.main_dark_radio).setChecked(True)
        (self.trigger_left_radio if self.settings.get("trigger_pos") == "left" else self.trigger_right_radio).setChecked(True)
        
        self.bg_path_edit.setText(self.settings.get("zen_bg_path", ""))
        self.transparent_checkbox.setChecked(self.settings.get("zen_editor_transparent", True))
        self.font_family_combo.setCurrentFont(QFont(self.settings.get("zen_font_family", "Georgia")))
        self.font_size_spin.setValue(self.settings.get("zen_font_size", 18))
        (self.align_left_radio if self.settings.get("zen_alignment", "left") == "left" else self.align_justify_radio).setChecked(True)
        self.horiz_padding.setValue(self.settings.get("zen_padding_horiz", 15))
        self.vert_padding.setValue(self.settings.get("zen_padding_vert", 10))
        self.first_line_indent_spin.setValue(self.settings.get("zen_first_line_indent", 0))

        self.update_color_swatches()

        for widget in all_widgets:
            if isinstance(widget, (QComboBox, QSpinBox, QCheckBox, QLineEdit, QRadioButton, QPushButton)):
                widget.blockSignals(False)

    def connect_signals(self):
        self.lang_combo.currentIndexChanged.connect(self.apply_changes)
        self.theme_group.buttonClicked.connect(self.apply_changes)
        self.pos_group.buttonClicked.connect(self.apply_changes)
        
        for key, (_, _, btn) in self.color_widgets.items():
            btn.clicked.connect(lambda _, k=key: self.choose_color(k))

        self.bg_path_edit.editingFinished.connect(self.apply_changes)
        self.browse_button.clicked.connect(self.browse_for_image)
        self.clear_bg_button.clicked.connect(self.clear_background)
        self.transparent_checkbox.stateChanged.connect(self.apply_changes)
        self.font_family_combo.currentFontChanged.connect(self.apply_changes)
        self.font_size_spin.valueChanged.connect(self.apply_changes)
        self.font_color_btn.clicked.connect(lambda: self.choose_color("zen_font_color"))
        self.clear_font_color_btn.clicked.connect(self.clear_font_color)
        self.zen_align_group.buttonClicked.connect(self.apply_changes)
        self.horiz_padding.valueChanged.connect(self.apply_changes)
        self.vert_padding.valueChanged.connect(self.apply_changes)
        self.first_line_indent_spin.valueChanged.connect(self.apply_changes)
    
    def retranslate_ui(self):
        self.title_label.setText(f"<b>{self.loc.get('settings_title')}</b>")
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.general_tab), self.loc.get("settings_tab_general"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.appearance_tab), self.loc.get("settings_tab_appearance"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.zen_editor_tab), self.loc.get("settings_tab_zen"))
        
        self.lang_label.setText(self.loc.get("settings_lang_label"))
        self.theme_label.setText(self.loc.get("settings_theme_label"))
        self.main_light_radio.setText(self.loc.get("settings_light_theme"))
        self.main_dark_radio.setText(self.loc.get("settings_dark_theme"))
        self.pos_label.setText(self.loc.get("settings_trigger_pos_label"))
        self.trigger_left_radio.setText(self.loc.get("settings_trigger_left"))
        self.trigger_right_radio.setText(self.loc.get("settings_trigger_right"))
        
        btn_text = self.loc.get("settings_choose_color_btn")
        for key, (label, _, btn) in self.color_widgets.items():
            label.setText(self.loc.get(f"settings_{key}_label", key))
            btn.setText(btn_text)

        self.zen_bg_label.setText(self.loc.get("settings_zen_bg_label"))
        self.browse_button.setText(self.loc.get("settings_browse_btn"))
        self.clear_bg_button.setText(self.loc.get("settings_clear_btn"))
        self.transparent_checkbox.setText(self.loc.get("settings_transparent_editor"))
        
        self.font_label.setText(self.loc.get("settings_font_label"))
        self.size_label.setText(self.loc.get("settings_size_label"))
        self.font_color_label.setText(self.loc.get("settings_font_color_label"))
        self.font_color_btn.setText(btn_text)
        self.clear_font_color_btn.setText(self.loc.get("settings_clear_btn"))
        self.align_label.setText(self.loc.get("settings_alignment_label"))
        self.align_left_radio.setText(self.loc.get("settings_align_left"))
        self.align_justify_radio.setText(self.loc.get("settings_align_justify"))
        self.horiz_pad_label.setText(self.loc.get("settings_padding_horiz"))
        self.vert_pad_label.setText(self.loc.get("settings_padding_vert"))
        self.indent_label.setText(self.loc.get("settings_first_line_indent"))
        
    def choose_color(self, setting_key):
        current_color = self.settings.get(setting_key, "#ffffff")
        if not current_color: current_color = "#ffffff" 
        color = QColorDialog.getColor(QColor(current_color), self, "Выберите цвет")
        if color.isValid():
            self.settings[setting_key] = color.name()
            self.update_color_swatches()
            self.apply_changes()

    def update_color_swatches(self):
        for key, (_, swatch, _) in self.color_widgets.items():
            swatch.setStyleSheet(f"background-color: {self.settings.get(key)}; border: 1px solid #888;")
        
        zen_color = self.settings.get("zen_font_color", "") or "#00000000" 
        self.zen_font_color_swatch.setStyleSheet(f"background-color: {zen_color}; border: 1px solid #888;")

    def clear_font_color(self): self.settings["zen_font_color"] = ""; self.update_color_swatches(); self.apply_changes()
    def browse_for_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path: self.bg_path_edit.setText(file_path); self.apply_changes()
    def clear_background(self): self.bg_path_edit.setText(""); self.apply_changes()

    def apply_styles(self):
        is_dark = self.settings.get("theme", "light") == "dark"
        bg_color = self.settings.get("dark_theme_bg") if is_dark else self.settings.get("light_theme_bg")
        text_color = self.settings.get("dark_theme_text") if is_dark else self.settings.get("light_theme_text")
        
        panel_bg = QColor(bg_color); panel_bg.setAlpha(245)
        line_edit_bg = "rgba(0,0,0,0.3)" if is_dark else "rgba(255,255,255,0.7)"
        button_bg = "rgba(80,80,80,1)" if is_dark else "#e1e1e1"
        
        panel_bg_rgba = f"rgba({panel_bg.red()}, {panel_bg.green()}, {panel_bg.blue()}, {panel_bg.alphaF()})"
        self.setStyleSheet(f"""
            QWidget#SettingsPanel {{ 
                background-color: {panel_bg_rgba};
                border-radius: 10px; color: {text_color};
            }} 
            QLabel, QCheckBox, QRadioButton {{ color: {text_color}; background: transparent;}} 

            QCheckBox::indicator, QRadioButton::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid #555;
                background-color: {line_edit_bg};
            }}
            QCheckBox::indicator {{
                border-radius: 3px;
            }}
            QRadioButton::indicator {{
                border-radius: 7px; /* делаем круглой */
            }}
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
                background-color: {self.settings.get("accent_color")};
                border-color: {QColor(self.settings.get("accent_color")).darker(115).name()};
            }}
            QRadioButton::indicator:checked {{
                /* Добавляем внутренний кружок для радио-кнопки */
                image: url(:/qt-project.org/styles/commonstyle/images/radiobutton-on-16.png);
            }}
          
            QLineEdit, QSpinBox, QFontComboBox, QComboBox {{ 
                background-color: {line_edit_bg}; border: 1px solid #555; 
                color: {text_color}; padding: 4px; border-radius: 3px;
            }} 
            QComboBox QAbstractItemView {{
                background-color: {line_edit_bg};
                color: {text_color};
                border: 1px solid #555;
                selection-background-color: {self.settings.get("accent_color")};
                outline: 0px; /* Убирает рамку выделения */
            }}
            QPushButton {{ 
                background-color: {button_bg}; color: {text_color}; 
                border: 1px solid #555; padding: 4px 8px; border-radius: 3px;
            }} 
            QPushButton:hover {{ background-color: #555; }}
            QTabWidget::pane {{ border: 1px solid #444; }}
            QTabBar::tab {{ 
                background: {"rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.05)"}; 
                color: {text_color}; padding: 8px 12px;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected, QTabBar::tab:hover {{
                background: {"rgba(255,255,255,0.2)" if is_dark else "rgba(0,0,0,0.1)"};
            }}
            QSpinBox::up-button {{ subcontrol-position: top right; width: 16px; }}
            QSpinBox::down-button {{ subcontrol-position: bottom right; width: 16px; }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{ width: 10px; height: 10px; }}
        """)

    def apply_changes(self):
        self.settings["language"] = self.lang_combo.currentData()
        self.settings["theme"] = "dark" if self.main_dark_radio.isChecked() else "light"
        self.settings["trigger_pos"] = "left" if self.trigger_left_radio.isChecked() else "right"
        self.settings["zen_bg_path"] = self.bg_path_edit.text()
        self.settings["zen_editor_transparent"] = self.transparent_checkbox.isChecked()
        self.settings["zen_font_family"] = self.font_family_combo.currentFont().family()
        self.settings["zen_font_size"] = self.font_size_spin.value()
        self.settings["zen_alignment"] = "justify" if self.align_justify_radio.isChecked() else "left"
        self.settings["zen_padding_horiz"] = self.horiz_padding.value()
        self.settings["zen_padding_vert"] = self.vert_padding.value()
        self.settings["zen_first_line_indent"] = self.first_line_indent_spin.value()
        
        if self.loc.current_lang != self.settings["language"]:
            self.loc.set_language(self.settings["language"])
            
        self.apply_styles()
        self.settings_changed.emit(self.settings.copy())

class MainPopup(QWidget):
    animation_finished_and_hidden = pyqtSignal()
    def __init__(self, data_manager):
        super().__init__()
        self.setObjectName("MainPopup") # Имя для главного окна
        self._is_closing = False
        self.data_manager = data_manager
        self.loc = data_manager.loc_manager
        
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint);
        
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(10, 10, 10, 5); title_bar_layout = QHBoxLayout();
        self.title_label = QLabel("Ассистент"); self.title_label.setObjectName("titleLabel");
        self.close_button = QPushButton("✕"); self.close_button.setFixedSize(24, 24); self.close_button.clicked.connect(self.close);
        title_bar_layout.addWidget(self.title_label); title_bar_layout.addStretch(); title_bar_layout.addWidget(self.close_button); main_layout.addLayout(title_bar_layout);
        self.tasks_panel = TasksPanel(data_manager); self.notes_panel = NotesPanel(data_manager);
        self.status_label = QLabel(); self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight);
        self.splitter = QSplitter(Qt.Orientation.Vertical); self.splitter.addWidget(self.tasks_panel); self.splitter.addWidget(self.notes_panel);
        main_layout.addWidget(self.splitter); main_layout.addWidget(self.status_label); self.close_button.setObjectName("close_button")
        
        self.pos_animation = QPropertyAnimation(self, b"pos"); self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation_group = QParallelAnimationGroup(self); self.animation_group.addAnimation(self.pos_animation); self.animation_group.addAnimation(self.opacity_animation)
        self.animation_group.finished.connect(self.on_animation_finished)
        
        self.set_status_saved(); self.notes_panel.zen_mode_requested.connect(data_manager.enter_zen_mode)
    
    def retranslate_ui(self):
        self.tasks_panel.retranslate_ui()
        self.notes_panel.retranslate_ui()
        self.on_data_changed()
        self.set_status_saved()
        
    def apply_theme(self, settings):
        is_dark = settings.get("theme", "light") == "dark"
        accent_color = settings.get("accent_color", "#007bff")
        bg_color = settings.get("dark_theme_bg") if is_dark else settings.get("light_theme_bg")
        text_color = settings.get("dark_theme_text") if is_dark else settings.get("light_theme_text")
        list_text_color = settings.get("dark_theme_list_text") if is_dark else settings.get("light_theme_list_text")
        component_bg = QColor(bg_color).lighter(115).name() if is_dark else QColor(bg_color).darker(105).name()
        border_color = "#555555" if is_dark else "#ced4da"
        
        stylesheet = f"""
            QWidget#MainPopup {{ 
                background-color: {bg_color}; 
            }}
            QWidget {{
                color: {text_color};
            }} 
            QLabel {{ 
                background-color: transparent; 
            }} 
            QLabel#titleLabel {{ 
                font-size: 14px; font-weight: bold; 
            }} 
            QLineEdit, QTextEdit, QComboBox {{ 
                background-color: {component_bg}; 
                border: 1px solid {border_color}; 
                border-radius: 4px; padding: 5px; 
            }} 
            QListWidget {{ 
                background-color: {component_bg}; 
                border: 1px solid {border_color}; 
            }}
            QListWidget:focus {{
                outline: none;
            }}

            /* --- Стилизация элементов списка --- */
            QListWidget::item {{
                color: {list_text_color};
                padding: 5px; 
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(128, 128, 128, 0.15);
            }}

            /* --- ОТКЛЮЧАЕМ ВЫДЕЛЕНИЕ В СПИСКЕ ЗАДАЧ --- */
            QListWidget#TaskList::item:selected {{
                background-color: transparent;
                color: {list_text_color};
            }}
            
            QListWidget::item:selected {{
                background-color: {accent_color};
                color: white;
            }}
            
            /* --- Стилизация индикатора (галочки) в списке ЗАДАЧ --- */
            QListWidget::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {border_color};
                border-radius: 3px;
                background-color: {component_bg};
            }}
            QListWidget::indicator:checked {{
                background-color: {accent_color};
                border-color: {QColor(accent_color).darker(115).name()};
                /* image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-apply-16.png); */
            }}
            
            QListWidget::item:checked {{
                color: gray;
            }}
            QListWidget#TaskList::item:selected:checked {{
                color: gray;
            }}
            QListWidget::item:selected:checked {{
                color: white;
            }}
            
            QPushButton {{ 
                background-color: {component_bg}; 
                color: {text_color};
                border: 1px solid {border_color}; 
                padding: 5px 10px; border-radius: 4px; 
            }} 
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {border_color};
                background-color: {component_bg};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent_color};
                border-color: {QColor(accent_color).darker(115).name()};
            }}
            QPushButton:hover {{ 
                background-color: {QColor(component_bg).lighter(110).name()}; 
            }} 
            QPushButton#save_button {{ 
                background-color: {accent_color}; color: white; border-color: {accent_color}; font-weight: bold; 
            }} 
            QPushButton#close_button {{ 
                font-family: 'Arial'; font-size: 14px; font-weight: bold; 
                background-color: transparent; color: #888; border: none; 
            }} 
            QPushButton#close_button:hover {{ 
                background-color: #dc3545; color: white; border-radius: 12px; 
            }} 
            QSplitter::handle {{ 
                background-color: {border_color}; height: 3px; 
            }}
            QMenu {{
                background-color: {component_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 5px 25px 5px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {accent_color};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background: {border_color};
                margin-left: 10px;
                margin-right: 10px;
            }}
        """
        self.setStyleSheet(stylesheet)
        # Принудительно обновить стили для всех задач
        for i in range(self.tasks_panel.task_list_widget.count()):
            self.tasks_panel.update_task_item_style(self.tasks_panel.task_list_widget.item(i))
        
    def on_data_changed(self): self.status_label.setText(self.loc.get("unsaved_changes_status")); self.status_label.setStyleSheet("color: #dc3545; font-size: 10px; margin-right: 5px;")
    def set_status_saved(self): self.status_label.setText(self.loc.get("data_saved_status")); self.status_label.setStyleSheet("color: #28a745; font-size: 10px; margin-right: 5px;")

    def show_animated(self, position, from_left=False):
        if self.isVisible(): return
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(position.x(), screen_geo.y(), 380, screen_geo.height())
        ratio = self.data_manager.settings.get("splitter_ratio", [40, 60])
        total_height = self.splitter.height()
        heights = [int(total_height * (r / 100)) for r in ratio]
        self.splitter.setSizes(heights)
        if from_left: start_pos = QPoint(-self.width(), self.y())
        else: start_pos = QPoint(screen_geo.width(), self.y())
        self.pos_animation.setDuration(300); self.pos_animation.setEasingCurve(QEasingCurve.Type.InOutCubic); self.pos_animation.setStartValue(start_pos); self.pos_animation.setEndValue(self.pos())
        self.opacity_animation.setDuration(250); self.opacity_animation.setStartValue(0.0); self.opacity_animation.setEndValue(1.0)
        self.setWindowOpacity(0.0); self.move(start_pos)
        self.show()
        self.animation_group.start()

    def hide_animated(self, to_left=False):
        if not self.isVisible() or self._is_closing: return
        self._is_closing = True
        end_x = -self.width() if to_left else self.screen().geometry().width()
        end_pos = QPoint(end_x, self.y())
        self.pos_animation.setStartValue(self.pos()); self.pos_animation.setEndValue(end_pos)
        self.opacity_animation.setStartValue(1.0); self.opacity_animation.setEndValue(0.0)
        self.animation_group.start()

    def on_animation_finished(self):
        if self.windowOpacity() < 0.1: 
            self.hide()
            self._is_closing = False
            self.animation_finished_and_hidden.emit()
    
    def close(self):
        self.hide_animated(to_left = self.data_manager.settings.get("trigger_pos") == "left")


class TriggerButton(QPushButton):
    def __init__(self, loc_manager):
        super().__init__(">"); self.setObjectName("trigger_button"); self.loc_manager = loc_manager; self.loc = loc_manager; self.settings = DEFAULT_SETTINGS.copy(); self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint); self.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.setFixedSize(20, 100)
        self.main_popup = None; self.about_dialog = None; self.zen_window = None; self.zen_source_timestamp = None; self.pending_zen_data = None; self.is_entering_zen = False; self.note_to_select_after_load = None
        
        self.loc.language_changed.connect(self._on_language_changed)
        self.load_settings()
        self.loc.set_language(self.settings.get("language", "ru_RU"))
        
        self.update_position_and_style();
        self.backup_timer = QTimer(self); self.backup_timer.timeout.connect(self.create_backup); self.backup_timer.start(600000)
        QApplication.instance().aboutToQuit.connect(self.save_app_data)
    
    def _on_language_changed(self):
        if self.main_popup: self.main_popup.retranslate_ui()
        if self.zen_window and self.zen_window.settings_panel:
            self.zen_window.settings_panel.retranslate_ui()
        self.update_position_and_style()

    def update_position_and_style(self):
        screen_geometry = QApplication.primaryScreen().geometry(); pos = self.settings.get("trigger_pos", "right"); accent_color = self.settings.get("accent_color", "#007bff")
        style = f"background-color: {accent_color}; color: white; font-size: 14px; font-weight: bold;"
        if pos == "left": self.move(0, int(screen_geometry.height() * 0.4)); self.setText("<"); style += "border-top-right-radius: 5px; border-bottom-right-radius: 5px; border-left: none;"
        else: self.move(screen_geometry.width() - self.width(), int(screen_geometry.height() * 0.4)); self.setText(">"); style += "border-top-left-radius: 5px; border-bottom-left-radius: 5px; border-right: none;"
        self.setStyleSheet(f"QPushButton#trigger_button {{ {style} }} QPushButton#trigger_button:hover {{ opacity: 0.8; }}")
    
    def show_main_popup(self, note_to_select=None):
        if self.main_popup is None:
            self.note_to_select_after_load = note_to_select
            self.main_popup = MainPopup(self)
            self.main_popup.animation_finished_and_hidden.connect(self.on_popup_closed)
            self.load_app_data()
        
        self.main_popup.retranslate_ui()
        self.main_popup.apply_theme(self.settings); pos = self.settings.get("trigger_pos", "right"); 
        
        screen_geo = QApplication.primaryScreen().availableGeometry()
        popup_x = self.width() if pos == "left" else screen_geo.width() - 380
        player_pos = QPoint(popup_x, screen_geo.y())
        
        self.main_popup.show_animated(player_pos, from_left=(pos == "left"))

    def enter_zen_mode(self, initial_text, timestamp):
        self.pending_zen_data = (initial_text, timestamp); self.is_entering_zen = True
        if self.main_popup and self.main_popup.isVisible():
            self.main_popup.close()
        else:
            self.on_popup_closed()

    def handle_zen_exit(self, text_from_zen, should_clear):
        if self.zen_window: self.zen_window.close(); self.zen_window = None
        self.show()
        self.save_zen_note(self.zen_source_timestamp, text_from_zen)
        note_to_select = None if should_clear else self.zen_source_timestamp
        self.show_main_popup(note_to_select=note_to_select)

    def on_popup_closed(self):
        if self.main_popup: self.save_app_data()
        
        if self.is_entering_zen:
            self.is_entering_zen = False
            initial_text, timestamp = self.pending_zen_data; self.zen_source_timestamp = timestamp; self.pending_zen_data = None; self.hide()
            self.zen_window = ZenModeWindow(initial_text, self.get_settings(), self.loc)
            self.zen_window.settings_updated_for_saving.connect(self.update_settings)
            self.zen_window.zen_exited.connect(lambda text: self.handle_zen_exit(text, should_clear=False))
            self.zen_window.zen_saved_and_closed.connect(lambda text: self.handle_zen_exit(text, should_clear=True))
            self.zen_window.showFullScreen()
        
        if self.main_popup:
            self.main_popup.deleteLater()
            self.main_popup = None

    def update_settings(self, new_settings):
        self.settings = new_settings
        self.save_settings()
        self.update_position_and_style()
        if self.main_popup and self.main_popup.isVisible():
            self.main_popup.apply_theme(new_settings)

    def create_backup(self):
        self.save_app_data()
        if os.path.exists(DATA_FILE):
            try: shutil.copyfile(DATA_FILE, BACKUP_FILE); print(f"Резервная копия создана: {BACKUP_FILE}")
            except Exception as e: print(f"Не удалось создать резервную копию: {e}")
            
    def restore_from_backup(self):
        if not os.path.exists(BACKUP_FILE): QMessageBox.warning(self, "Ошибка", "Файл резервной копии не найден."); return
        reply = QMessageBox.question(self, "Восстановление", "Вы уверены, что хотите восстановить данные из резервной копии?\nВсе текущие несохраненные изменения будут потеряны.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.copyfile(BACKUP_FILE, DATA_FILE);
                if self.main_popup: self.load_app_data()
                QMessageBox.information(self, "Успех", "Данные успешно восстановлены.")
            except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось восстановить данные: {e}")
            
    def export_notes_to_markdown(self):
        self.save_app_data()
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта."); return
        notes = sorted(data.get("notes", []), key=lambda x: x.get('timestamp', ''))
        if not notes: QMessageBox.information(self, "Информация", "Нет заметок для экспорта."); return
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт заметок", "Мои_заметки.md", "Markdown Files (*.md);;Text Files (*.txt)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("# Экспорт заметок\n\n");
                    for note in notes: f.write(f"## Заметка от: {note.get('timestamp', '')}\n\n{note.get('text', '')}\n\n---\n\n")
                QMessageBox.information(self, "Успех", f"Заметки успешно экспортированы в {path}")
            except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать файл: {e}")
    
    def show_about_dialog(self):
        if self.about_dialog is None:
            self.about_dialog = AboutDialog(self)
        screen = self.screen().geometry()
        dlg_size = self.about_dialog.size()
        x = screen.x() + (screen.width() - dlg_size.width()) // 2
        y = screen.y() + (screen.height() - dlg_size.height()) // 2
        self.about_dialog.move(x, y)
        self.about_dialog.exec()
        
    def toggle_popup(self):
        if self.main_popup is None or not self.main_popup.isVisible(): self.show_main_popup()
        else: self.main_popup.close()
        
    def get_settings(self): return self.settings
    
    def main_popup_on_data_changed(self):
        if hasattr(self, 'main_popup') and self.main_popup:
            if self.main_popup.notes_panel.is_dirty: self.main_popup.on_data_changed()
            else: self.main_popup.set_status_saved()

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Ошибка сохранения настроек: {e}")

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            settings = DEFAULT_SETTINGS.copy(); settings.update(loaded_settings); self.settings = settings
        except (FileNotFoundError, json.JSONDecodeError):
            print("Файл настроек не найден, используются значения по умолчанию."); self.settings = DEFAULT_SETTINGS.copy()

    def save_app_data(self):
        if not self.main_popup: return
        data_to_save = {
            "task_lists": self.main_popup.tasks_panel.get_task_lists_data(),
            "active_task_list": self.main_popup.tasks_panel.current_list_name,
            "notes": self.main_popup.notes_panel.get_notes_data(),
            "splitter_state": self.main_popup.splitter.saveState().toHex().data().decode('ascii')
        }
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            if self.main_popup.isVisible(): self.main_popup.set_status_saved()
        except Exception as e: print(f"Ошибка сохранения данных: {e}")

    def load_app_data(self):
        if not self.main_popup: return
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Файл данных не найден."); data = {}
        
        self.main_popup.tasks_panel.load_task_lists(data.get("task_lists", {}), data.get("active_task_list", ""))
        self.main_popup.notes_panel.load_notes(data.get("notes", []))
        
        if self.note_to_select_after_load:
            self.main_popup.notes_panel.find_and_select_note_by_timestamp(self.note_to_select_after_load)
            self.note_to_select_after_load = None
        if self.main_popup.isVisible(): self.main_popup.set_status_saved()
            
    def save_zen_note(self, note_timestamp, new_text):
        if not new_text.strip() and not note_timestamp: return
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): data = {"notes": [], "task_lists": {}}
        
        notes = data.get("notes", []); note_found = False
        if note_timestamp:
            for note in notes:
                if note.get("timestamp") == note_timestamp:
                    note["text"] = new_text; note_found = True; break
        if not note_found:
            new_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            notes.append({"timestamp": new_timestamp, "text": new_text})
            self.zen_source_timestamp = new_timestamp
        
        data["notes"] = notes
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Ошибка сохранения zen-заметки: {e}")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton: self.toggle_popup()
        elif event.button() == Qt.MouseButton.RightButton:
            context_menu = QMenu(self)
            
            # --- НАЧАЛО ИЗМЕНЕНИЙ ---
            # Получаем текущие настройки темы, чтобы меню соответствовало
            settings = self.get_settings()
            is_dark = settings.get("theme", "light") == "dark"
            accent_color = settings.get("accent_color", "#007bff")
            bg_color = settings.get("dark_theme_bg") if is_dark else settings.get("light_theme_bg")
            text_color = settings.get("dark_theme_text") if is_dark else settings.get("light_theme_text")
            border_color = "#555555" if is_dark else "#ced4da"
            component_bg = QColor(bg_color).lighter(115).name() if is_dark else QColor(bg_color).darker(105).name()

            menu_style = f"""
                QMenu {{
                    background-color: {component_bg};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 5px;
                }}
                QMenu::item {{
                    padding: 5px 25px 5px 20px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background-color: {accent_color};
                    color: white;
                }}
                QMenu::separator {{
                    height: 1px;
                    background: {border_color};
                    margin-left: 10px;
                    margin-right: 10px;
                }}
            """
            context_menu.setStyleSheet(menu_style)
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---

            about_action = QAction(self.loc.get("about_menu"), self); about_action.triggered.connect(self.show_about_dialog); context_menu.addAction(about_action)
            export_action = QAction(self.loc.get("export_menu"), self); export_action.triggered.connect(self.export_notes_to_markdown)
            restore_action = QAction(self.loc.get("restore_menu"), self); restore_action.triggered.connect(self.restore_from_backup)
            exit_action = QAction(self.loc.get("exit_menu"), self); exit_action.triggered.connect(QApplication.instance().quit)
            context_menu.addSeparator(); context_menu.addAction(export_action); context_menu.addAction(restore_action); context_menu.addSeparator(); context_menu.addAction(exit_action)
            context_menu.exec(event.globalPosition().toPoint())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    #if os.path.exists(SETTINGS_FILE):
    #    try: os.remove(SETTINGS_FILE); print("Старый файл настроек удален.")
    #    except OSError as e: print(f"Ошибка удаления {SETTINGS_FILE}: {e}")
    #if os.path.exists(DATA_FILE):
    #    try: os.remove(DATA_FILE); print("Старый файл данных удален.")
    #    except OSError as e: print(f"Ошибка удаления {DATA_FILE}: {e}")

    loc_manager = LocalizationManager()
    trigger = TriggerButton(loc_manager)
    trigger.show()
    
    sys.exit(app.exec())