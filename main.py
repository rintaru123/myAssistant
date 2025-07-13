import sys
import json
import os
import re
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QHBoxLayout, QCheckBox, QTextEdit, QSplitter,
                             QStyle, QMenu, QDialog, QFileDialog, QDialogButtonBox,
                             QRadioButton, QMessageBox, QSpinBox, QInputDialog, QComboBox,
                             QFontComboBox, QButtonGroup, QColorDialog, QStackedLayout)
from PyQt6.QtCore import Qt, QPoint, QUrl, QPropertyAnimation, QEasingCurve, pyqtSignal, QByteArray, QSize, QTimer, QEvent, QParallelAnimationGroup
from PyQt6.QtGui import QAction, QMouseEvent, QPalette, QKeyEvent, QPainter, QPixmap, QColor, QFont, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# --- Константы ---
DATA_FILE = "tasks_and_notes.json"
BACKUP_FILE = "tasks_and_notes.json.bak"
DEFAULT_SETTINGS = {
    "theme": "light", "trigger_pos": "right", "accent_color": "#007bff",
    "zen_bg_path": "", "zen_editor_transparent": True, "zen_theme": "light",
    "zen_padding_horiz": 15, "zen_padding_vert": 10,
    "zen_font_family": "Calibri", "zen_font_size": 17
}
POMODORO_WORK_TIME = 25*60
POMODORO_BREAK_TIME = 5 * 60

# --- Вспомогательные классы ---
class TaskItemWidget(QWidget):
    task_updated = pyqtSignal()
    edit_requested = pyqtSignal(object)
    edit_finished = pyqtSignal()

    def __init__(self, text, is_completed=False):
        super().__init__(); self.original_text = text
        self.stacked_layout = QStackedLayout(); self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        display_widget = QWidget()
        layout = QHBoxLayout(); layout.setContentsMargins(5, 5, 5, 5)
        self.checkbox = QCheckBox(); self.checkbox.stateChanged.connect(self._on_state_changed)
        self.label = QLabel(text); self.label.installEventFilter(self)
        self.delete_button = QPushButton(); self.delete_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)); self.delete_button.setFixedSize(24, 24); self.delete_button.setStyleSheet("QPushButton { border: none; } QPushButton:hover { background-color: #ffe0e0; border-radius: 5px; }")
        layout.addWidget(self.delete_button); layout.addWidget(self.checkbox); layout.addWidget(self.label, 1); display_widget.setLayout(layout)
        edit_widget = QWidget()
        edit_layout = QHBoxLayout(); edit_layout.setContentsMargins(5, 5, 5, 5)
        self.edit_input = QLineEdit(text); self.edit_input.returnPressed.connect(self._confirm_edit)
        self.edit_input.setMinimumHeight(28) 
        confirm_btn = QPushButton(); confirm_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)); confirm_btn.setFixedSize(24, 24); confirm_btn.clicked.connect(self._confirm_edit)
        cancel_btn = QPushButton(); cancel_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)); cancel_btn.setFixedSize(24, 24); cancel_btn.clicked.connect(self._cancel_edit)
        edit_layout.addWidget(self.edit_input, 1); edit_layout.addWidget(confirm_btn); edit_layout.addWidget(cancel_btn); edit_widget.setLayout(edit_layout)
        self.stacked_layout.addWidget(display_widget); self.stacked_layout.addWidget(edit_widget); self.setLayout(self.stacked_layout)
        self.checkbox.setChecked(is_completed); self.update_style(is_completed)
    def eventFilter(self, source, event):
        if source is self.label and event.type() == QEvent.Type.MouseButtonDblClick:
            if not self.is_completed():
                self.edit_requested.emit(self) 
            return True
        return super().eventFilter(source, event)
    def switch_to_edit_mode(self): 
        self.edit_input.setText(self.original_text); self.stacked_layout.setCurrentIndex(1); self.edit_input.setFocus(); self.edit_input.selectAll()
    def _confirm_edit(self):
        new_text = self.edit_input.text().strip()
        if new_text and new_text != self.original_text:
            self.original_text = new_text; self.label.setText(new_text)
        self.stacked_layout.setCurrentIndex(0)
        self.edit_finished.emit() 
    def _cancel_edit(self):
        self.stacked_layout.setCurrentIndex(0)
        self.edit_finished.emit() 
    def _on_state_changed(self, state): self.update_style(state == Qt.CheckState.Checked.value); self.task_updated.emit()
    def update_style(self, is_completed):
        font = self.label.font(); font.setStrikeOut(is_completed); self.label.setFont(font); palette = self.label.palette()
        color = self.palette().color(QPalette.ColorRole.PlaceholderText) if is_completed else self.palette().color(QPalette.ColorRole.WindowText)
        palette.setColor(QPalette.ColorRole.WindowText, color); self.label.setPalette(palette)
    def is_completed(self): return self.checkbox.isChecked()

class NoteListItemWidget(QWidget):
    delete_requested = pyqtSignal()
    def __init__(self, timestamp_str):
        super().__init__()
        self.stacked_layout = QStackedLayout(); self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        normal_widget = QWidget()
        normal_layout = QHBoxLayout(); normal_layout.setContentsMargins(5, 2, 5, 2)
        self.label = QLabel(timestamp_str); font = self.label.font(); font.setPointSize(9); self.label.setFont(font); self.label.setStyleSheet("color: gray;")
        self.delete_button = QPushButton(); self.delete_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)); self.delete_button.setFixedSize(20, 20); self.delete_button.setIconSize(QSize(12, 12)); self.delete_button.setStyleSheet("QPushButton { border: none; } QPushButton:hover { background-color: #ffe0e0; border-radius: 5px; }"); self.delete_button.setToolTip("Удалить заметку"); self.delete_button.clicked.connect(self._show_confirm_ui)
        normal_layout.addWidget(self.delete_button); normal_layout.addWidget(self.label, 1); normal_widget.setLayout(normal_layout)
        confirm_widget = QWidget()
        confirm_layout = QHBoxLayout(); confirm_layout.setContentsMargins(5, 2, 5, 2)
        confirm_label = QLabel("Удалить?"); confirm_label.setStyleSheet("color: #dc3545; font-size: 9pt;")
        confirm_btn = QPushButton(); confirm_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)); confirm_btn.setFixedSize(20, 20); confirm_btn.setIconSize(QSize(14, 14)); confirm_btn.setStyleSheet("QPushButton { border: none; color: green; } QPushButton:hover { background-color: #e0ffe0; border-radius: 5px; }"); confirm_btn.setToolTip("Да, удалить"); confirm_btn.clicked.connect(self.delete_requested.emit)
        cancel_btn = QPushButton(); cancel_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)); cancel_btn.setFixedSize(20, 20); cancel_btn.setIconSize(QSize(12, 12)); cancel_btn.setStyleSheet("QPushButton { border: none; color: red; } QPushButton:hover { background-color: #ffe0e0; border-radius: 5px; }"); cancel_btn.setToolTip("Отмена"); cancel_btn.clicked.connect(self._show_normal_ui)
        confirm_layout.addStretch(); confirm_layout.addWidget(confirm_label); confirm_layout.addWidget(confirm_btn); confirm_layout.addWidget(cancel_btn); confirm_widget.setLayout(confirm_layout)
        self.stacked_layout.addWidget(normal_widget); self.stacked_layout.addWidget(confirm_widget); self.setLayout(self.stacked_layout)
    def _show_confirm_ui(self): self.stacked_layout.setCurrentIndex(1)
    def _show_normal_ui(self): self.stacked_layout.setCurrentIndex(0)

class NoteEditor(QTextEdit):
    save_and_new_requested = pyqtSignal()
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.save_and_new_requested.emit()
        else: super().keyPressEvent(event)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("О программе"); self.setFixedSize(450, 400); layout = QVBoxLayout(self)
        info_label = QLabel("<h3>Мой Ассистент v1.0</h3>"
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
                            "<p><a target='_blank' href='https://www.bensound.com/free-music-for-videos'>Music by https://www.bensound.com/free-music-for-videos</a><br>"
                             "License code: DAHEOFFMQKTP738K<br>"
                            "Artist: : Benjamin Tissot<br>"
                            "Filename: relaxing.mp3</p>"
                            "<p><a target='_blank' href='https://www.bensound.com/royalty-free-music'>Music: Bensound.com/royalty-free-music</a><br>"
                            "License code: WDY7EPJS4MVS7QLQ<br>"
                            "Artist: : Benjamin Lazzarus<br>"
                            "Filename: slowlife.mp3</p>"
                            "<a target='_blank' href='https://icons8.com/icon/gkW5yexEuzan/left-handed'>Левша</a> иконка от <a target='_blank' href='https://icons8.com'>Icons8</a>")
        
        info_label.setWordWrap(True); layout.addWidget(info_label)
        info_label.setOpenExternalLinks(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok); buttons.accepted.connect(self.accept); layout.addWidget(buttons)

class TasksPanel(QWidget):
    def __init__(self, data_manager):
        super().__init__(); self.data_manager = data_manager
        
        self.currently_editing_widget = None
        layout = QVBoxLayout(); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(10); add_task_layout = QHBoxLayout(); self.task_input = QLineEdit(); self.task_input.setPlaceholderText("Новая задача..."); self.add_button = QPushButton("Добавить"); self.add_button.clicked.connect(self.add_task_from_input); self.task_input.returnPressed.connect(self.add_task_from_input); add_task_layout.addWidget(self.task_input); add_task_layout.addWidget(self.add_button)
        filter_layout = QHBoxLayout(); self.hide_completed_checkbox = QCheckBox("Скрыть выполненные"); self.hide_completed_checkbox.stateChanged.connect(self.filter_tasks); filter_layout.addStretch(); filter_layout.addWidget(self.hide_completed_checkbox)
        self.task_list_widget = QListWidget(); layout.addLayout(add_task_layout); layout.addLayout(filter_layout); layout.addWidget(self.task_list_widget); self.setLayout(layout)
    def add_task(self, text, is_completed=False):
        if not text: return
        task_item_widget = TaskItemWidget(text, is_completed)
        task_item_widget.delete_button.clicked.connect(lambda ch, w=task_item_widget: self.delete_task(w))
        task_item_widget.task_updated.connect(self.on_task_updated)

        task_item_widget.edit_requested.connect(self.handle_edit_request)
        task_item_widget.edit_finished.connect(self.handle_edit_finish)
        list_item = QListWidgetItem(); list_item.setSizeHint(task_item_widget.sizeHint()); self.task_list_widget.addItem(list_item); self.task_list_widget.setItemWidget(list_item, task_item_widget); self.filter_tasks()
    

    def handle_edit_request(self, widget_to_edit):

        if self.currently_editing_widget and self.currently_editing_widget != widget_to_edit:
            self.currently_editing_widget._cancel_edit()

        self.currently_editing_widget = widget_to_edit
        self.currently_editing_widget.switch_to_edit_mode()

    def handle_edit_finish(self):

        self.currently_editing_widget = None
        self.data_manager.save_data()

    def on_task_updated(self): self.filter_tasks(); self.data_manager.save_data()
    def filter_tasks(self, state=None):
        hide = self.hide_completed_checkbox.isChecked()
        for i in range(self.task_list_widget.count()):
            item = self.task_list_widget.item(i); widget = self.task_list_widget.itemWidget(item)
            if widget: item.setHidden(hide and widget.is_completed())
    def add_task_from_input(self):
        task_text = self.task_input.text().strip()
        if task_text: self.add_task(task_text); self.task_input.clear(); self.data_manager.save_data()
    def delete_task(self, task_widget_to_delete):
        for i in range(self.task_list_widget.count()):
            if self.task_list_widget.itemWidget(self.task_list_widget.item(i)) == task_widget_to_delete: self.task_list_widget.takeItem(i); break
        self.data_manager.save_data()
    def get_tasks_data(self):
        tasks = []
        for i in range(self.task_list_widget.count()):
            widget = self.task_list_widget.itemWidget(self.task_list_widget.item(i))
            if widget: tasks.append({"text": widget.original_text, "completed": widget.is_completed()})
        return tasks
    def load_tasks(self, tasks_data):
        self.task_list_widget.clear()
        for t in tasks_data: self.add_task(t['text'], t['completed'])
        self.filter_tasks()

class NotesPanel(QWidget):
    zen_mode_requested = pyqtSignal(str, str)
    def __init__(self, data_manager):
        super().__init__(); self.data_manager = data_manager; self.current_note_item = None; self.saved_text = ""; self.is_dirty = False; self.all_tags = set(); layout = QVBoxLayout(); layout.setContentsMargins(0, 5, 0, 0); layout.setSpacing(5); self.notes_editor = NoteEditor(); self.notes_editor.setPlaceholderText("Выберите заметку..."); self.notes_editor.textChanged.connect(self.on_editor_text_changed); self.notes_editor.save_and_new_requested.connect(self.handle_save_and_new); button_layout = QHBoxLayout(); save_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton); new_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon); zen_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton); self.save_button = QPushButton("Сохранить"); self.save_button.setIcon(save_icon); self.save_button.setObjectName("save_button"); self.new_button = QPushButton("Новая"); self.new_button.setIcon(new_icon); self.zen_button = QPushButton("Zen"); self.zen_button.setIcon(zen_icon); self.save_button.clicked.connect(self.save_current_note); self.new_button.clicked.connect(lambda: self.clear_for_new_note(force=False)); self.zen_button.clicked.connect(self.open_zen_mode); button_layout.addWidget(self.new_button); button_layout.addWidget(self.zen_button); button_layout.addStretch(); button_layout.addWidget(self.save_button); filter_layout = QHBoxLayout(); self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Поиск по тексту..."); self.search_input.textChanged.connect(self.filter_notes); self.tag_filter_combo = QComboBox(); self.tag_filter_combo.addItem("Все теги"); self.tag_filter_combo.currentIndexChanged.connect(self.filter_notes); filter_layout.addWidget(self.search_input, 1); filter_layout.addWidget(self.tag_filter_combo); self.note_list_widget = QListWidget(); self.note_list_widget.currentItemChanged.connect(self.display_selected_note); layout.addWidget(QLabel("Редактор заметок:")); layout.addWidget(self.notes_editor, 1); layout.addLayout(button_layout); layout.addLayout(filter_layout); layout.addWidget(self.note_list_widget, 1); self.setLayout(layout)
    def find_tags(self, text): return set(re.findall(r'#(\w+)', text))
    def update_tag_filter(self):
        current_selection = self.tag_filter_combo.currentText(); self.tag_filter_combo.blockSignals(True); self.tag_filter_combo.clear(); self.tag_filter_combo.addItem("Все теги"); sorted_tags = sorted(list(self.all_tags)); self.tag_filter_combo.addItems(sorted_tags); index = self.tag_filter_combo.findText(current_selection)
        if index != -1: self.tag_filter_combo.setCurrentIndex(index)
        self.tag_filter_combo.blockSignals(False)
    def filter_notes(self):
        search_text = self.search_input.text().lower(); selected_tag = self.tag_filter_combo.currentText()
        for i in range(self.note_list_widget.count()):
            item = self.note_list_widget.item(i); note_data = item.data(Qt.ItemDataRole.UserRole); note_text = note_data.get('text', ''); note_timestamp = note_data.get('timestamp', ''); text_match = search_text in (note_timestamp + ' ' + note_text).lower(); tag_match = (selected_tag == "Все теги") or (f"#{selected_tag}" in note_text); item.setHidden(not (text_match and tag_match))
    def display_selected_note(self, current_item, previous_item):
        if previous_item and self.is_dirty: self.save_current_note()
        if not current_item:
            if self.current_note_item is not None: self.clear_for_new_note(force=True)
            return
        self.current_note_item = current_item
        note_data = self.current_note_item.data(Qt.ItemDataRole.UserRole)
        source_text = note_data.get("text", ""); self.notes_editor.setMarkdown(source_text); self.saved_text = source_text; self.on_editor_text_changed()
    def save_current_note(self):
        text = self.notes_editor.toMarkdown().strip()
        if not self.current_note_item and not text.strip(): return
        new_tags = self.find_tags(text); self.all_tags.update(new_tags); self.update_tag_filter()
        if self.current_note_item:
            note_data = self.current_note_item.data(Qt.ItemDataRole.UserRole); note_data["text"] = text; self.current_note_item.setData(Qt.ItemDataRole.UserRole, note_data)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); note_data = {"timestamp": timestamp, "text": text}; new_item = self._add_note_item(note_data); self.current_note_item = new_item; self.note_list_widget.blockSignals(True); self.note_list_widget.setCurrentItem(new_item); self.note_list_widget.blockSignals(False)
        self.saved_text = text; self.on_editor_text_changed(); self.data_manager.save_data()
    def load_notes(self, notes_data):
        self.note_list_widget.clear(); self.all_tags.clear()
        sorted_notes = sorted(notes_data, key=lambda x: x.get('timestamp', ''), reverse=True)
        for note in sorted_notes:
            self._add_note_item(note); self.all_tags.update(self.find_tags(note.get("text", "")))
        self.update_tag_filter(); self.clear_for_new_note(force=True)
    def open_zen_mode(self):
        self.save_if_dirty(); text = self.notes_editor.toMarkdown(); timestamp = ""
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
        self.notes_editor.clear(); self.saved_text = ""; self.on_editor_text_changed(); self.notes_editor.setPlaceholderText("Начните писать...")
    def handle_save_and_new(self): self.save_current_note(); self.clear_for_new_note(force=True)
    def on_editor_text_changed(self):
        self.is_dirty = (self.notes_editor.toMarkdown().strip() != self.saved_text.strip()); self.data_manager.main_popup_on_data_changed()
    def save_if_dirty(self):
        if self.is_dirty: self.save_current_note()
    def _add_note_item(self, note_data):
        list_item = QListWidgetItem(); list_item.setData(Qt.ItemDataRole.UserRole, note_data); item_widget = NoteListItemWidget(note_data["timestamp"])
        item_widget.delete_requested.connect(lambda li=list_item: self._perform_delete_note(li))
        list_item.setSizeHint(item_widget.sizeHint()); self.note_list_widget.insertItem(0, list_item); self.note_list_widget.setItemWidget(list_item, item_widget); return list_item
    def _perform_delete_note(self, item_to_delete):
        if self.current_note_item == item_to_delete: self.clear_for_new_note(force=True)
        row = self.note_list_widget.row(item_to_delete); self.note_list_widget.takeItem(row); self.data_manager.save_data()
    def get_notes_data(self): return [self.note_list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.note_list_widget.count())]

class ZenModeWindow(QWidget):
    zen_exited = pyqtSignal(str); zen_saved_and_closed = pyqtSignal(str); settings_updated_for_saving = pyqtSignal(dict)
    def __init__(self, initial_text, settings):
        super().__init__(); self.settings = settings; self.background_pixmap = None; self.player = QMediaPlayer(); self.audio_output = QAudioOutput(); self.player.setAudioOutput(self.audio_output); self.current_playing_button = None; self.playlist_mode = False; self.playlist_files = []; self.playlist_index = 0; self.player.mediaStatusChanged.connect(self.handle_media_status_change); self.pomodoro_timer = QTimer(self); self.pomodoro_timer.timeout.connect(self.update_pomodoro); self.pomodoro_time_left = POMODORO_WORK_TIME; self.is_work_time = True; self.pomodoro_running = False; self.pomodoro_player = QMediaPlayer(); self.pomodoro_audio_output = QAudioOutput(); self.pomodoro_player.setAudioOutput(self.pomodoro_audio_output)
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__)); sound_path = os.path.join(script_dir, "pomodoro_end.wav")
            if os.path.exists(sound_path): self.pomodoro_player.setSource(QUrl.fromLocalFile(sound_path))
        except NameError: pass
        self.main_layout = QVBoxLayout(self); self.main_layout.setSpacing(0); self.main_layout.setContentsMargins(0, 0, 0, 0); self.pomodoro_panel = self.create_pomodoro_panel(); self.main_layout.addWidget(self.pomodoro_panel); self.editor = QTextEdit()
        self.editor.setMarkdown(initial_text)
        self.main_layout.addWidget(self.editor); self.word_count_label = QLabel("Слов: 0"); self.main_layout.addWidget(self.word_count_label); self.editor.textChanged.connect(self.update_word_count); self.update_word_count(); self.audio_panel = self.create_audio_panel(); self.settings_panel = ZenSettingsPanel(self.settings, self); self.settings_panel.hide(); self.settings_button = self.create_settings_button(); self.exit_button = self.create_exit_button(); self.settings_panel.settings_changed.connect(self.update_zen_settings); self.editor.setFocus(); self.update_background(); self._update_styles()
    def create_pomodoro_panel(self):
        panel = QWidget(); layout = QHBoxLayout(panel); layout.setContentsMargins(10, 5, 10, 5); self.pomodoro_title_label = QLabel("<b>Pomodoro:</b>"); self.pomodoro_label = QLabel("25:00"); self.pomodoro_start_button = QPushButton("Старт"); self.pomodoro_start_button.clicked.connect(self.start_pause_pomodoro); self.pomodoro_reset_button = QPushButton("Сброс"); self.pomodoro_reset_button.clicked.connect(self.reset_pomodoro); layout.addWidget(self.pomodoro_title_label); layout.addWidget(self.pomodoro_label); layout.addWidget(self.pomodoro_start_button); layout.addWidget(self.pomodoro_reset_button); layout.addStretch(); return panel
    def start_pause_pomodoro(self):
        self.pomodoro_running = not self.pomodoro_running
        if self.pomodoro_running: self.pomodoro_timer.start(1000); self.pomodoro_start_button.setText("Пауза")
        else: self.pomodoro_timer.stop(); self.pomodoro_start_button.setText("Старт")
    def reset_pomodoro(self):
        self.pomodoro_timer.stop(); self.pomodoro_running = False; self.is_work_time = True; self.pomodoro_time_left = POMODORO_WORK_TIME; self.pomodoro_start_button.setText("Старт"); self.update_pomodoro_label()
    def update_pomodoro(self):
        if not self.pomodoro_running: return
        self.pomodoro_time_left -= 1; self.update_pomodoro_label()
        if self.pomodoro_time_left <= 0:
            if self.pomodoro_player.source().isValid(): self.pomodoro_player.play()
            self.is_work_time = not self.is_work_time; self.pomodoro_time_left = POMODORO_WORK_TIME if self.is_work_time else POMODORO_BREAK_TIME
    def update_pomodoro_label(self):
        mins, secs = divmod(self.pomodoro_time_left, 60); self.pomodoro_label.setText(f"{mins:02d}:{secs:02d}")
    def update_word_count(self):
        text = self.editor.toPlainText(); word_count = len(text.split()) if text else 0; self.word_count_label.setText(f"Слов: {word_count}")
    def create_audio_panel(self):
        panel = QWidget(self); panel.setObjectName("audioPanel"); layout = QHBoxLayout(panel); layout.setContentsMargins(10, 5, 10, 5)
        try: script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError: script_dir = os.getcwd()
        audio_dir = os.path.join(script_dir, "zen_audio"); self.playlist_files = []
        if os.path.isdir(audio_dir):
            self.playlist_files = sorted([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))])
            if self.playlist_files:
                self.playlist_button = QPushButton(); self.playlist_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)); self.playlist_button.setToolTip("Запустить/Пауза плейлист"); self.playlist_button.setFixedSize(30, 30); self.playlist_button.clicked.connect(self.toggle_playlist); layout.addWidget(self.playlist_button)
                self.stop_button = QPushButton(); self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)); self.stop_button.setToolTip("Остановить музыку"); self.stop_button.setFixedSize(30, 30); self.stop_button.clicked.connect(self.stop_all_music); layout.addWidget(self.stop_button)
            for i, file_path in enumerate(self.playlist_files):
                btn = QPushButton(f"{i + 1}"); btn.setFixedSize(30, 30); btn.setObjectName("audio_button"); btn.setProperty("audio_path", file_path); btn.setProperty("original_text", f"{i+1}"); btn.clicked.connect(lambda ch, b=btn: self.toggle_single_track(b)); layout.addWidget(btn)
        panel.adjustSize(); return panel
    def handle_media_status_change(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.playlist_mode: self.play_next_in_playlist()
    def toggle_playlist(self):
        if not self.playlist_mode: self.start_playlist()
        else:
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState: self.player.pause(); self.playlist_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            elif self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState: self.player.play(); self.playlist_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
    def start_playlist(self):
        if not self.playlist_files: return
        self.stop_all_music(); self.playlist_mode = True; self.playlist_index = 0; self.player.setLoops(QMediaPlayer.Loops.Once); self.play_next_in_playlist(); self.playlist_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
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
        if hasattr(self, 'playlist_button'): self.playlist_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.deactivate_all_buttons()
    def create_settings_button(self): btn = QPushButton(self); btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)); btn.setFixedSize(32, 32); btn.clicked.connect(self.toggle_settings_panel); return btn
    def create_exit_button(self): btn = QPushButton(self); btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)); btn.setFixedSize(32, 32); btn.clicked.connect(self.close); return btn
    def toggle_settings_panel(self):
        if self.settings_panel.isVisible(): self.settings_panel.hide()
        else: self.settings_panel.adjustSize(); self.settings_panel.move((self.width() - self.settings_panel.width()) // 2, (self.height() - self.settings_panel.height()) // 2); self.settings_panel.show()
    def _update_styles(self):
        hp = self.width() * self.settings.get("zen_padding_horiz", 15) // 100; vp = self.height() * self.settings.get("zen_padding_vert", 10) // 100
        font_family = self.settings.get("zen_font_family", "Georgia"); font_size = self.settings.get("zen_font_size", 18); accent_color = self.settings.get("accent_color", "#007bff")
        self.main_layout.setContentsMargins(hp, vp, hp, vp)
        is_dark = self.settings.get("zen_theme", "dark") == "dark"; is_transparent = self.settings.get("zen_editor_transparent", True)
        editor_bg = "rgba(0,0,0,0.2)" if is_dark and is_transparent else "#3c3c3c" if is_dark else "rgba(245,245,245,0.85)" if is_transparent else "#f8f9fa"; editor_color = "#f0f0f0" if is_dark else "#212529"
        self.editor.setStyleSheet(f"QTextEdit {{ background-color: {editor_bg}; border: none; font-family: '{font_family}'; font-size: {font_size}pt; color: {editor_color}; }}")
        panel_bg = "rgba(0,0,0,0.5)" if is_dark else "rgba(255,255,255,0.6)"; btn_border = "rgba(255,255,255,0.7)" if is_dark else "rgba(0,0,0,0.4)"; btn_bg = "rgba(0,0,0,0.4)" if is_dark else "rgba(255,255,255,0.4)"; btn_color = "white" if is_dark else "black"; btn_hover_bg = "rgba(255,255,255,0.3)" if is_dark else "rgba(0,0,0,0.1)"
        self.audio_panel.setStyleSheet(f'QWidget#audioPanel {{ background: {panel_bg}; border-radius: 15px; }} QPushButton {{ border: 1px solid {btn_border}; border-radius: 15px; background-color: {btn_bg}; color: {btn_color}; font-size: 11pt; font-weight: bold; }} QPushButton:hover {{ background-color: {btn_hover_bg}; }} QPushButton[playing="true"] {{ background-color: {accent_color}; border-color: #ffffff; color: white; }}')
        floating_btn_bg = "rgba(30,30,30,0.5)" if is_dark else "rgba(240,240,240,0.7)"; floating_btn_style = f"background: {floating_btn_bg}; border-radius: 16px;"; self.settings_button.setStyleSheet(floating_btn_style); self.exit_button.setStyleSheet(floating_btn_style); text_color = '#ccc' if is_dark else '#333'; pomodoro_button_bg = "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.05)"; pomodoro_style = f"background-color: transparent; border: none; font-size: 10pt; color: {text_color}; padding: 2px 5px;"
        self.pomodoro_title_label.setStyleSheet(f"background-color: transparent; color: {text_color}; font-weight:bold;"); self.pomodoro_label.setStyleSheet(f"background-color: transparent; font-size: 14pt; font-weight: bold; color: {text_color};"); self.pomodoro_start_button.setStyleSheet(pomodoro_style + f" QPushButton:hover {{ background-color: {pomodoro_button_bg}; border-radius: 5px; }}"); self.pomodoro_reset_button.setStyleSheet(pomodoro_style + f" QPushButton:hover {{ background-color: {pomodoro_button_bg}; border-radius: 5px; }}"); self.word_count_label.setStyleSheet(f"background-color: transparent; border: none; color: {text_color}; padding: 5px;")
    def update_background(self):
        bg_path = self.settings.get("zen_bg_path"); self.background_pixmap = QPixmap(bg_path) if bg_path and os.path.exists(bg_path) else None; self.update()
    def update_zen_settings(self, new_settings): self.settings = new_settings; self.settings_updated_for_saving.emit(new_settings); self._update_styles(); self.update_background()
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
            self.blockSignals(True); self.zen_saved_and_closed.emit(self.editor.toMarkdown())
        else: super().keyPressEvent(event)
    def closeEvent(self, event):
        self.stop_all_music(); self.pomodoro_timer.stop(); self.pomodoro_running = False
        if self.settings_panel.isVisible(): self.settings_panel.hide()
        if not self.signalsBlocked(): self.zen_exited.emit(self.editor.toMarkdown())
        event.accept()
    def paintEvent(self, event):
        painter = QPainter(self)
        if self.background_pixmap: painter.drawPixmap(self.rect(), self.background_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else: theme_color = QColor("#2b2b2b") if self.settings.get("zen_theme") == "dark" else QColor("#f0f0f0"); painter.fillRect(self.rect(), theme_color)

class ZenSettingsPanel(QWidget):
    settings_changed = pyqtSignal(dict)
    def __init__(self, current_settings, parent=None):
        super().__init__(parent); self.settings = current_settings.copy(); self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint); layout = QVBoxLayout(self); layout.setContentsMargins(15, 15, 15, 15); title_layout = QHBoxLayout(); title_layout.addWidget(QLabel("<b>Настройки</b>")); title_layout.addStretch(); close_btn = QPushButton("✕"); close_btn.setFixedSize(24, 24); close_btn.clicked.connect(self.hide); title_layout.addWidget(close_btn); 
        self.pos_group = QButtonGroup(self); trigger_pos_box = QHBoxLayout(); self.trigger_left_radio = QRadioButton("Слева"); self.trigger_right_radio = QRadioButton("Справа"); self.pos_group.addButton(self.trigger_left_radio); self.pos_group.addButton(self.trigger_right_radio)
        if self.settings.get("trigger_pos", "right") == "left": self.trigger_left_radio.setChecked(True)
        else: self.trigger_right_radio.setChecked(True)
        trigger_pos_box.addWidget(QLabel("<b>Позиция кнопки:</b>")); trigger_pos_box.addWidget(self.trigger_left_radio); trigger_pos_box.addWidget(self.trigger_right_radio); trigger_pos_box.addStretch()
        self.theme_group = QButtonGroup(self); main_theme_box = QHBoxLayout(); self.main_dark_radio = QRadioButton("Тёмная"); self.main_light_radio = QRadioButton("Светлая"); self.theme_group.addButton(self.main_dark_radio); self.theme_group.addButton(self.main_light_radio)
        if self.settings.get("theme") == "light": self.main_light_radio.setChecked(True)
        else: self.main_dark_radio.setChecked(True)
        main_theme_box.addWidget(QLabel("<b>Общая тема:</b>")); main_theme_box.addWidget(self.main_light_radio); main_theme_box.addWidget(self.main_dark_radio); main_theme_box.addStretch()
        self.pos_group.buttonClicked.connect(self.apply_changes); self.theme_group.buttonClicked.connect(self.apply_changes)
        accent_layout = QHBoxLayout(); self.accent_color_btn = QPushButton("Выбрать цвет..."); self.accent_color_btn.clicked.connect(self.choose_accent_color); accent_layout.addWidget(QLabel("<b>Акцентный цвет:</b>")); accent_layout.addWidget(self.accent_color_btn); accent_layout.addStretch()
        bg_layout = QHBoxLayout(); self.bg_path_edit = QLineEdit(self.settings.get("zen_bg_path", "")); self.bg_path_edit.editingFinished.connect(self.apply_changes); browse_button = QPushButton("Обзор..."); browse_button.clicked.connect(self.browse_for_image); clear_bg_button = QPushButton("Удалить фон"); clear_bg_button.clicked.connect(self.clear_background); bg_layout.addWidget(QLabel("Фон Zen:")); bg_layout.addWidget(self.bg_path_edit); bg_layout.addWidget(browse_button); bg_layout.addWidget(clear_bg_button); self.transparent_checkbox = QCheckBox("Прозрачный редактор в Zen"); self.transparent_checkbox.setChecked(self.settings.get("zen_editor_transparent", True)); self.transparent_checkbox.stateChanged.connect(self.apply_changes); 
        font_layout = QHBoxLayout(); self.font_family_combo = QFontComboBox(); self.font_family_combo.setCurrentFont(QFont(self.settings.get("zen_font_family", "Georgia"))); self.font_family_combo.currentFontChanged.connect(self.apply_changes); self.font_size_spin = QSpinBox(); self.font_size_spin.setRange(8, 72); self.font_size_spin.setValue(self.settings.get("zen_font_size", 18)); self.font_size_spin.valueChanged.connect(self.apply_changes); font_layout.addWidget(QLabel("Шрифт:")); font_layout.addWidget(self.font_family_combo, 1); font_layout.addWidget(QLabel("Размер:")); font_layout.addWidget(self.font_size_spin)
        padding_layout = QHBoxLayout(); self.horiz_padding = QSpinBox(); self.horiz_padding.setRange(0, 40); self.horiz_padding.setValue(self.settings.get("zen_padding_horiz", 15)); self.horiz_padding.valueChanged.connect(self.apply_changes); self.vert_padding = QSpinBox(); self.vert_padding.setRange(0, 40); self.vert_padding.setValue(self.settings.get("zen_padding_vert", 10)); self.vert_padding.valueChanged.connect(self.apply_changes); padding_layout.addWidget(QLabel("Гор. отступ (%):")); padding_layout.addWidget(self.horiz_padding); padding_layout.addWidget(QLabel("Верт. отступ (%):")); padding_layout.addWidget(self.vert_padding); layout.addLayout(title_layout); layout.addLayout(trigger_pos_box); layout.addLayout(main_theme_box); layout.addLayout(accent_layout); layout.addSpacing(10); layout.addWidget(QLabel("<b>Настройки Zen Mode:</b>")); layout.addLayout(bg_layout); layout.addLayout(font_layout); layout.addWidget(self.transparent_checkbox); layout.addLayout(padding_layout); self.apply_styles()
    def choose_accent_color(self):
        color = QColorDialog.getColor(QColor(self.settings.get("accent_color", "#007bff")), self, "Выберите акцентный цвет")
        if color.isValid(): self.settings["accent_color"] = color.name(); self.apply_changes()
    def browse_for_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__));
                #path_to_save = file_path
                if os.path.commonpath([file_path, script_dir]) == script_dir: path_to_save = os.path.relpath(file_path, script_dir)
                else: path_to_save = file_path
            except (NameError, Exception): path_to_save = file_path
            self.bg_path_edit.setText(path_to_save); self.apply_changes()
    def clear_background(self): self.bg_path_edit.setText(""); self.apply_changes()
    def apply_styles(self):
        is_dark = self.settings.get("theme", "light") == "dark"; bg_color = "rgba(50,50,50,0.95)" if is_dark else "rgba(240,240,240,0.95)"; text_color = "white" if is_dark else "black"; line_edit_bg = "rgba(0,0,0,0.3)" if is_dark else "rgba(255,255,255,0.7)"; button_bg = "rgba(80,80,80,1)" if is_dark else "#f0f0f0"; button_text = "white" if is_dark else "black"; self.setStyleSheet(f"QWidget {{ background-color: {bg_color}; border-radius: 10px; color: {text_color};}} QLabel, QCheckBox, QRadioButton {{ color: {text_color};}} QLineEdit, QSpinBox, QFontComboBox {{ background-color: {line_edit_bg}; border: 1px solid #555; color: {text_color}; padding: 4px; border-radius: 3px;}} QSpinBox::up-button, QSpinBox::down-button {{ width: 20px; height: 12px; }} QPushButton {{ background-color: {button_bg}; color: {button_text}; border: 1px solid #555; padding: 4px 8px; border-radius: 3px;}} QPushButton:hover {{ background-color: #555; }}")
    def apply_changes(self):
        self.settings["theme"] = "dark" if self.main_dark_radio.isChecked() else "light"; self.settings["trigger_pos"] = "left" if self.trigger_left_radio.isChecked() else "right"; self.settings["zen_bg_path"] = self.bg_path_edit.text(); self.settings["zen_editor_transparent"] = self.transparent_checkbox.isChecked(); self.settings["zen_theme"] = self.settings["theme"]; self.settings["zen_padding_horiz"] = self.horiz_padding.value(); self.settings["zen_padding_vert"] = self.vert_padding.value(); self.settings["zen_font_family"] = self.font_family_combo.currentFont().family(); self.settings["zen_font_size"] = self.font_size_spin.value(); self.apply_styles(); self.settings_changed.emit(self.settings)

class MainPopup(QWidget):
    animation_finished_and_hidden = pyqtSignal()
    def __init__(self, data_manager):
        super().__init__(); self._is_closing = False; self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint); self.setFixedSize(380, 640); main_layout = QVBoxLayout(self); main_layout.setContentsMargins(10, 10, 10, 5); title_bar_layout = QHBoxLayout(); title_label = QLabel("Ассистент v1.0"); title_label.setObjectName("titleLabel"); self.close_button = QPushButton("✕"); self.close_button.setFixedSize(24, 24); self.close_button.clicked.connect(self.close); title_bar_layout.addWidget(title_label); title_bar_layout.addStretch(); title_bar_layout.addWidget(self.close_button); main_layout.addLayout(title_bar_layout); self.tasks_panel = TasksPanel(data_manager); self.notes_panel = NotesPanel(data_manager); self.status_label = QLabel(); self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight); self.splitter = QSplitter(Qt.Orientation.Vertical); self.splitter.addWidget(self.tasks_panel); self.splitter.addWidget(self.notes_panel); self.splitter.setSizes([220, 420]); main_layout.addWidget(self.splitter); main_layout.addWidget(self.status_label); self.setLayout(main_layout); self.close_button.setObjectName("close_button")
        self.pos_animation = QPropertyAnimation(self, b"pos"); self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation_group = QParallelAnimationGroup(self); self.animation_group.addAnimation(self.pos_animation); self.animation_group.addAnimation(self.opacity_animation)
        self.animation_group.finished.connect(self.on_animation_finished)
        self.set_status_saved(); self.notes_panel.zen_mode_requested.connect(data_manager.enter_zen_mode)
    def apply_theme(self, settings):
        is_dark = settings.get("theme", "light") == "dark"; accent_color = settings.get("accent_color", "#007bff")

        dark_stylesheet = f"QWidget {{ background-color: #2b2b2b; color: #bbbbbb; }} QLabel {{ color: #bbbbbb; }} QLabel#titleLabel {{ font-size: 14px; font-weight: bold; }} QLineEdit, QTextEdit, QComboBox {{ background-color: #3c3c3c; color: #bbbbbb; border: 1px solid #555; border-radius: 4px; padding: 5px; }} QListWidget {{ background-color: #3c3c3c; border: 1px solid #555; }} QListWidget::item {{ border-radius: 4px; padding: 2px; }} QListWidget::item:hover {{ background-color: rgba(255, 255, 255, 0.1); }} QListWidget::item:selected {{ background-color: {accent_color}; }} QListWidget::item:selected QLabel {{ color: white; }} QPushButton {{ background-color: #555; color: #f0f0f0; border: 1px solid #666; padding: 5px 10px; border-radius: 4px; }} QCheckBox {{ color: #bbbbbb; }} QPushButton:hover {{ background-color: #666; }} QPushButton#save_button {{ background-color: {accent_color}; color: white; border-color: {accent_color}; font-weight: bold; }} QPushButton#save_button:hover {{ opacity: 0.8; }} QPushButton#close_button {{ font-family: 'Arial'; font-size: 14px; font-weight: bold; background-color: transparent; color: #888; border: none; }} QPushButton#close_button:hover {{ background-color: #dc3545; color: white; border-radius: 12px; }} QSplitter::handle {{ background-color: #555; height: 3px; }} QCheckBox::indicator {{ border: 1px solid #777; width: 14px; height: 14px; border-radius: 7px; background-color: #3c3c3c; }} QCheckBox::indicator:hover {{ border-color: #999; }} QCheckBox::indicator:checked {{ background-color: {accent_color}; border-color: {accent_color}; }}"
        light_stylesheet = f"QWidget {{ background-color: #f8f9fa; color: #212529; }} QLabel#titleLabel {{ font-size: 14px; font-weight: bold; }} QLineEdit, QTextEdit, QComboBox {{ background-color: #ffffff; border: 1px solid #ced4da; border-radius: 4px; padding: 5px; }} QListWidget::item {{ border-radius: 4px; padding: 2px; }} QListWidget::item:hover {{ background-color: #e9ecef; }} QListWidget::item:selected {{ background-color: {accent_color}; }} QListWidget::item:selected QLabel {{ color: gray; }} QPushButton {{ background-color: #f0f0f0; border: 1px solid #ced4da; padding: 5px 10px; border-radius: 4px; }} QPushButton:hover {{ background-color: #e9ecef; border-color: #adb5bd; }} QCheckBox {{ color: #212529; }} QPushButton#save_button {{ background-color: {accent_color}; color: white; border-color: {accent_color}; font-weight: bold; }} QPushButton#save_button:hover {{ opacity: 0.8; }} QPushButton#close_button {{ font-family: 'Arial'; font-size: 14px; font-weight: bold; background-color: transparent; color: #6c757d; border: none; }} QPushButton#close_button:hover {{ background-color: #dc3545; color: white; border-radius: 12px; }} QSplitter::handle {{ height: 3px; }} QCheckBox::indicator {{ border: 1px solid #aaa; width: 14px; height: 14px; border-radius: 7px; background-color: #fff; }} QCheckBox::indicator:hover {{ border-color: #888; }} QCheckBox::indicator:checked {{ background-color: {accent_color}; border-color: {accent_color}; }}"
        self.setStyleSheet(dark_stylesheet if is_dark else light_stylesheet)
    def on_data_changed(self): self.status_label.setText("Несохраненные изменения..."); self.status_label.setStyleSheet("color: #dc3545; font-size: 10px; margin-right: 5px;")
    def set_status_saved(self): self.status_label.setText("Данные сохранены"); self.status_label.setStyleSheet("color: #28a745; font-size: 10px; margin-right: 5px;")
    

    def show_animated(self, position, from_left=False):
        if from_left: start_pos = QPoint(-self.width(), position.y())
        else: start_pos = QPoint(QApplication.primaryScreen().geometry().width(), position.y())
        self.pos_animation.setDuration(300); self.pos_animation.setEasingCurve(QEasingCurve.Type.InOutCubic); self.pos_animation.setStartValue(start_pos); self.pos_animation.setEndValue(position)
        self.opacity_animation.setDuration(250); self.opacity_animation.setStartValue(0.0); self.opacity_animation.setEndValue(1.0)
        self.setWindowOpacity(0.0); self.move(start_pos)
        QTimer.singleShot(5, self.show) 
        self.animation_group.start()
        
    def hide_animated(self, to_left=False):
        if to_left: end_pos = QPoint(-self.width(), self.y())
        else: end_pos = QPoint(self.screen().geometry().width(), self.y())
        self.pos_animation.setStartValue(self.pos()); self.pos_animation.setEndValue(end_pos); self.pos_animation.setDuration(300); self.pos_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.opacity_animation.setStartValue(1.0); self.opacity_animation.setEndValue(0.0); self.opacity_animation.setDuration(250)
        self.animation_group.start()
        
    def on_animation_finished(self):
        if self.windowOpacity() < 0.1: self.animation_finished_and_hidden.emit(); self.close()
    def closeEvent(self, event):
        if not self._is_closing:
            self._is_closing = True; event.ignore()
            to_left = self.property("data_manager").settings.get("trigger_pos") == "left"
            self.hide_animated(to_left=to_left)
        else: event.accept()

class TriggerButton(QPushButton):
    def __init__(self):
        super().__init__(">"); self.setObjectName("trigger_button"); self.settings = DEFAULT_SETTINGS.copy(); self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint); self.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.setFixedSize(20, 100)
        self.main_popup = None; self.about_dialog = None; self.zen_window = None; self.zen_source_timestamp = None; self.pending_zen_data = None; self.is_entering_zen = False; self.note_to_select_after_load = None
        self.load_data(); self.update_position_and_style();
        self.backup_timer = QTimer(self); self.backup_timer.timeout.connect(self.create_backup); self.backup_timer.start(600000)
        QApplication.instance().aboutToQuit.connect(self.save_data_on_exit)
    def update_position_and_style(self):
        screen_geometry = QApplication.primaryScreen().geometry(); pos = self.settings.get("trigger_pos", "right"); accent_color = self.settings.get("accent_color", "#007bff")
        style = f"background-color: {accent_color}; color: white; font-size: 14px; font-weight: bold;"
        if pos == "left": self.move(0, int(screen_geometry.height() * 0.4)); self.setText("<"); style += "border-top-right-radius: 5px; border-bottom-right-radius: 5px; border-left: none;"
        else: self.move(screen_geometry.width() - self.width(), int(screen_geometry.height() * 0.4)); self.setText(">"); style += "border-top-left-radius: 5px; border-bottom-left-radius: 5px; border-right: none;"
        self.setStyleSheet(f"QPushButton#trigger_button {{ {style} }} QPushButton#trigger_button:hover {{ opacity: 0.8; }}")
    def show_main_popup(self, note_to_select=None):
        if self.main_popup is None:
            self.note_to_select_after_load = note_to_select
            self.main_popup = MainPopup(self); self.main_popup.setProperty("data_manager", self); self.main_popup.animation_finished_and_hidden.connect(self.on_popup_closed); self.load_data()
        self.main_popup.apply_theme(self.settings); pos = self.settings.get("trigger_pos", "right"); y_pos = self.y() + self.height() // 2 - self.main_popup.height() // 2
        if pos == "left": player_pos = QPoint(self.width(), y_pos)
        else: player_pos = QPoint(self.screen().geometry().width() - self.main_popup.width(), y_pos)
        self.show(); self.main_popup.show_animated(player_pos, from_left=(pos == "left"))
    def enter_zen_mode(self, initial_text, timestamp):
        self.pending_zen_data = (initial_text, timestamp); self.is_entering_zen = True
        if self.main_popup: self.main_popup.close()
        else: self.on_popup_closed()
    def handle_zen_exit(self, text_from_zen, should_clear):
        if self.zen_window: self.zen_window.close(); self.zen_window = None
        saved_timestamp = self.save_zen_note(self.zen_source_timestamp, text_from_zen)
        note_to_select = None if should_clear else saved_timestamp
        self.show_main_popup(note_to_select=note_to_select)
    def on_popup_closed(self):
        self.save_data(); self.main_popup = None
        if self.is_entering_zen:
            self.is_entering_zen = False
            initial_text, timestamp = self.pending_zen_data; self.zen_source_timestamp = timestamp; self.pending_zen_data = None; self.hide()
            self.zen_window = ZenModeWindow(initial_text, self.get_settings())
            self.zen_window.settings_updated_for_saving.connect(self.update_settings)
            self.zen_window.zen_exited.connect(lambda text: self.handle_zen_exit(text, should_clear=False))
            self.zen_window.zen_saved_and_closed.connect(lambda text: self.handle_zen_exit(text, should_clear=True))
            self.zen_window.showFullScreen()
    def update_settings(self, new_settings):
        self.settings = new_settings; self.save_data(); self.update_position_and_style()
        if self.main_popup and self.main_popup.isVisible(): self.main_popup.apply_theme(new_settings)
    def create_backup(self):
        self.save_data()
        if os.path.exists(DATA_FILE):
            try: shutil.copyfile(DATA_FILE, BACKUP_FILE); print(f"Резервная копия создана: {BACKUP_FILE}")
            except Exception as e: print(f"Не удалось создать резервную копию: {e}")
    def restore_from_backup(self):
        if not os.path.exists(BACKUP_FILE): QMessageBox.warning(self, "Ошибка", "Файл резервной копии не найден."); return
        reply = QMessageBox.question(self, "Восстановление", "Вы уверены, что хотите восстановить данные из резервной копии?\nВсе текущие несохраненные изменения будут потеряны.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.copyfile(BACKUP_FILE, DATA_FILE); 
                if self.main_popup: self.load_data(); self.main_popup.apply_theme(self.settings)
                QMessageBox.information(self, "Успех", "Данные успешно восстановлены.")
            except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось восстановить данные: {e}")
    def export_notes_to_markdown(self):
        self.save_data()
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
        if self.about_dialog is None: self.about_dialog = AboutDialog(self)
        self.about_dialog.exec()
    def toggle_popup(self):
        if self.main_popup is None or not self.main_popup.isVisible(): self.show_main_popup()
        else: self.main_popup.close()
    def get_settings(self): return self.settings
    def main_popup_on_data_changed(self):
        if hasattr(self, 'main_popup') and self.main_popup:
            if self.main_popup.notes_panel.is_dirty: self.main_popup.on_data_changed()
            else: self.main_popup.set_status_saved()
    def save_data_on_exit(self): self.save_data()
    def save_data(self):
        data_to_save = {};
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: data_to_save = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): pass
        data_to_save["settings"] = self.settings
        if self.main_popup: data_to_save["tasks"] = self.main_popup.tasks_panel.get_tasks_data(); data_to_save["notes"] = self.main_popup.notes_panel.get_notes_data(); data_to_save["splitter_state"] = self.main_popup.splitter.saveState().toHex().data().decode('ascii')
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            if self.main_popup and self.main_popup.isVisible(): self.main_popup.set_status_saved()
        except Exception as e: print(f"Ошибка сохранения данных: {e}")
    def load_data(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): print("Файл данных не найден."); data = {}
        self.settings = DEFAULT_SETTINGS.copy(); self.settings.update(data.get("settings", {}))
        self.update_position_and_style()
        if self.main_popup:
            self.main_popup.tasks_panel.load_tasks(data.get("tasks", [])); self.main_popup.notes_panel.load_notes(data.get("notes", []))
            splitter_state_hex = data.get("splitter_state")
            if splitter_state_hex:
                splitter_state = QByteArray.fromHex(splitter_state_hex.encode('ascii'))
                if not splitter_state.isEmpty(): self.main_popup.splitter.restoreState(splitter_state)
            if self.note_to_select_after_load:
                self.main_popup.notes_panel.find_and_select_note_by_timestamp(self.note_to_select_after_load); self.note_to_select_after_load = None
            if self.main_popup.isVisible(): self.main_popup.set_status_saved()
    def save_zen_note(self, note_timestamp, new_text):
        if not new_text.strip() and not note_timestamp: return None
        data = {"settings": self.settings, "tasks": [], "notes": []}
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): pass
        notes = data.get("notes", []); note_found = False
        if note_timestamp:
            for note in notes:
                if note.get("timestamp") == note_timestamp: note["text"] = new_text; note_found = True; break
        if not note_found:
            new_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            notes.append({"timestamp": new_timestamp, "text": new_text}); note_timestamp = new_timestamp
        data["notes"] = notes
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Ошибка сохранения zen-заметки: {e}")
        return note_timestamp
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton: self.toggle_popup()
        elif event.button() == Qt.MouseButton.RightButton:
            context_menu = QMenu(self)
            about_action = QAction("О программе...", self); about_action.triggered.connect(self.show_about_dialog); context_menu.addAction(about_action)
            export_action = QAction("Экспорт заметок в Markdown...", self); export_action.triggered.connect(self.export_notes_to_markdown)
            restore_action = QAction("Восстановить из резервной копии...", self); restore_action.triggered.connect(self.restore_from_backup)
            exit_action = QAction("Выход", self); exit_action.triggered.connect(QApplication.instance().quit)
            context_menu.addSeparator(); context_menu.addAction(export_action); context_menu.addAction(restore_action); context_menu.addSeparator(); context_menu.addAction(exit_action)
            context_menu.exec(event.globalPosition().toPoint())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    trigger = TriggerButton()
    trigger.show()
    sys.exit(app.exec())