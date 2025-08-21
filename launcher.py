import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QComboBox, QDialog, QMessageBox, QSlider, QScrollArea, QFormLayout, QCheckBox
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
from screenpet import ScreenPet


class OptionsDialog(QDialog):
    def __init__(self, owner, base):
        super().__init__()
        self.owner = owner
        self.setWindowTitle(base.get("options", "Options"))
        self.setGeometry(400, 400, 350, 400)

        main_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)

        self.rotate_checkbox = QCheckBox(base.get("rotate_on_chilling", "Rotate on chilling"))
        self.rotate_checkbox.setChecked(base["rotateWriting"])
        scroll_layout.addRow(self.rotate_checkbox)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(base["maxSpeed"])
        self.speed_label = QLabel(str(self.speed_slider.value()))
        self.speed_slider.valueChanged.connect(lambda val: self.speed_label.setText(str(val)))
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        scroll_layout.addRow(QLabel(base.get("speed", "Speed:")), speed_layout)

        self.jump_slider = QSlider(Qt.Horizontal)
        self.jump_slider.setMinimum(0)
        self.jump_slider.setMaximum(720)
        self.jump_slider.setValue(base["jumpHeight"])
        self.jump_label = QLabel(str(self.jump_slider.value()))
        self.jump_slider.valueChanged.connect(lambda val: self.jump_label.setText(str(val)))
        jump_layout = QHBoxLayout()
        jump_layout.addWidget(self.jump_slider)
        jump_layout.addWidget(self.jump_label)
        scroll_layout.addRow(QLabel(base.get("jump_height", "Jump height:")), jump_layout)

        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(80)
        self.size_slider.setMaximum(720)
        self.size_slider.setValue(base["size"])
        self.size_label = QLabel(str(self.size_slider.value()))
        self.size_slider.valueChanged.connect(lambda val: self.size_label.setText(str(val)))
        size_layout = QHBoxLayout()
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_label)
        scroll_layout.addRow(QLabel(base.get("sizeText", "Size (in px):")), size_layout)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        buttons_layout = QHBoxLayout()
        save_btn = QPushButton(base.get("save", "Save"))
        cancel_btn = QPushButton(base.get("cancel", "Cancel"))
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        save_btn.clicked.connect(self.save_options)
        cancel_btn.clicked.connect(self.reject)

    def save_options(self):
        options = {
            "rotate_on_chilling": self.rotate_checkbox.isChecked(),
            "speed": self.speed_slider.value(),
            "jump_height": self.jump_slider.value(),
            "size": self.size_slider.value()
        }
        self.owner(options)
        self.accept()


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen-Pet Launcher")
        self.setWindowIcon(QIcon("MyPc.png"))
        self.setGeometry(100, 100, 400, 350)

        self.pet = None
        self.skin_folder = None
        self.languages_path = os.path.join(os.getcwd(), "languages")
        self.translations = {}
        self.current_language = "en"

        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()
        buttons_layout = QHBoxLayout()

        self.language_combo = QComboBox()
        self.load_languages()
        self.language_combo.currentIndexChanged.connect(self.change_language)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Language:"))
        top_bar.addWidget(self.language_combo)

        self.skin_icon_label = QLabel()
        self.skin_icon_label.setFixedSize(64, 64)
        self.skin_icon_label.setStyleSheet("border: 1px solid gray;")
        self.skin_icon_label.setAlignment(Qt.AlignCenter)

        self.folder_name_label = QLabel("")
        self.folder_name_label.setAlignment(Qt.AlignCenter)

        self.change_skin_btn = QPushButton()
        self.change_skin_btn.clicked.connect(self.change_skin)

        self.options_btn = QPushButton()
        self.options_btn.clicked.connect(self.open_options)

        self.launch_pet_btn = QPushButton()
        self.launch_pet_btn.clicked.connect(self.launch_pet)

        self.hide_pet_btn = QPushButton()
        self.hide_pet_btn.clicked.connect(self.hide_pet)
        self.hide_pet_btn.hide()

        buttons_layout.addWidget(self.change_skin_btn)
        buttons_layout.addWidget(self.options_btn)
        buttons_layout.addWidget(self.launch_pet_btn)
        buttons_layout.addWidget(self.hide_pet_btn)

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.skin_icon_label, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.folder_name_label)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        self.load_language_texts(self.current_language)

    def load_languages(self):
        if not os.path.exists(self.languages_path):
            os.makedirs(self.languages_path)
        files = [f for f in os.listdir(self.languages_path) if f.endswith(".json")]
        languages = [os.path.splitext(f)[0] for f in files]
        if not languages:
            default_en = {
                "change_skin": "Change Skin",
                "options": "Options",
                "launch_pet": "Launch Pet",
                "hide_pet": "Hide Pet",
                "language_label": "Language:"
            }
            with open(os.path.join(self.languages_path, "en.json"), "w", encoding="utf-8") as f:
                json.dump(default_en, f, indent=4)
            languages = ["en"]
        self.language_combo.addItems([self.get_language_name(i) + f" ({i})" for i in languages])

    def get_language_name(self, filename):
        with open(os.path.join(self.languages_path, f"{filename}.json"), encoding="utf-8") as file:
            return json.load(file)["language_name"]

    def load_language_texts(self, lang_code):
        path = os.path.join(self.languages_path, f"{lang_code}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load language file: {e}")
            self.translations = {}

        self.change_skin_btn.setText(self.translations.get("change_skin", "Change Skin"))
        self.options_btn.setText(self.translations.get("options", "Options"))
        self.launch_pet_btn.setText(self.translations.get("launch_pet", "Launch Pet"))
        self.hide_pet_btn.setText(self.translations.get("hide_pet", "Hide Pet"))

        top_bar_layout = self.layout().itemAt(0)
        if top_bar_layout is not None:
            label_widget = top_bar_layout.itemAt(top_bar_layout.count() - 2).widget()
            if label_widget:
                label_widget.setText(self.translations.get("language_label", "Language:"))

    def change_language(self, index):
        lang_code = self.language_combo.currentText().split(" ")[1][1:]
        lang_code = lang_code[:len(lang_code) - 1]
        self.current_language = lang_code
        self.load_language_texts(lang_code)

    def change_skin(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Skin Folder", os.getcwd())
        if folder:
            self.skin_folder = folder
            icon_path = os.path.join(folder, "icon.png")
            if os.path.isfile(icon_path):
                pixmap = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.skin_icon_label.setPixmap(pixmap)
            else:
                self.skin_icon_label.clear()
                self.skin_icon_label.setText("No icon.png found")

            folder_name = os.path.basename(os.path.normpath(folder))
            self.folder_name_label.setText(folder_name)

    def open_options(self):
        if self.skin_folder != "":
            with open(f"{self.skin_folder}/options.json") as file:
                data = json.load(file)
            params = self.translations.copy()
            for i in data.keys():
                params[i] = data[i]
            dlg = OptionsDialog(self.apply_options, params)
            dlg.exec_()

    def apply_options(self, arg):
        with open(f"{self.skin_folder}/options.json") as file:
            data = json.load(file)
        data["rotateWriting"] = arg["rotate_on_chilling"]
        data["maxSpeed"] = arg["speed"]
        data["jumpHeight"] = arg["jump_height"]
        data["size"] = arg["size"]

        with open(f"{self.skin_folder}/options.json", mode='w+') as file:
            json.dump(data, file)

    def launch_pet(self):
        if self.pet is None:
            self.pet = ScreenPet(skin=self.skin_folder)
            self.launch_pet_btn.hide()
            self.hide_pet_btn.show()
        else:
            QMessageBox.information(self, "Info", "Pet is already running.")

    def hide_pet(self):
        if self.pet:
            self.pet.close_pet()
            self.pet = None
            self.hide_pet_btn.hide()
            self.launch_pet_btn.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec_())
