import importlib
import math
import sys
import random
import json
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QTransform
import pyautogui
import importlib.util

g = 2


class ScreenPet(QLabel):
    def __init__(self, skin):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.skin = skin

        options = {}

        with open(f"{self.skin}/options.json", mode='r') as file:
            options = json.load(file)

        mirror = QTransform().scale(-1, 1)

        self.rotateWriting = options["rotateWriting"]

        self.jumpHeight = options["jumpHeight"]
        self.maxspeed = options["maxSpeed"]

        self.scale = QTransform().scale(options["size"] / QPixmap(f"{self.skin}/frame_1.png").height(),
                                        options["size"] / QPixmap(f"{self.skin}/frame_1.png").height())

        self.animation = {
            "left": [QPixmap(f"{self.skin}/frame_{i}.png").transformed(self.scale) for i in
                     range(1, options["move"] + 1)],
            "right": [QPixmap(f"{self.skin}/frame_{i}.png").transformed(mirror).transformed(self.scale) for i in
                      range(1, options["move"] + 1)],
            "tackle_left": [QPixmap(f"{self.skin}/tackle_{i}.png").transformed(self.scale) for i in
                            range(1, options["tackle"] + 1)],
            "tackle_right": [QPixmap(f"{self.skin}/tackle_{i}.png").transformed(mirror).transformed(self.scale) for i in
                             range(1, options["tackle"] + 1)],
            "writing_left": [QPixmap(f"{self.skin}/writing_{i}.png").transformed(self.scale) for i in
                             range(1, options["writing"] + 1)],
            "writing_right": [QPixmap(f"{self.skin}/writing_{i}.png").transformed(mirror).transformed(self.scale) for i
                              in
                              range(1, options["writing"] + 1)],
            "dragging": [QPixmap(f"{self.skin}/dragging_{i}.png").transformed(self.scale) for i in
                         range(1, options["dragging"] + 1)],
            "falling_left": [QPixmap(f"{self.skin}/falling_{i}.png").transformed(self.scale) for i in
                             range(1, options["falling"] + 1)],
            "falling_right": [QPixmap(f"{self.skin}/falling_{i}.png").transformed(mirror).transformed(self.scale) for i
                              in
                              range(1, options["falling"] + 1)]
        }

        self.frames = self.animation["left"]
        self.current_frame = 0
        self.setPixmap(self.frames[self.current_frame])

        self.resize(self.frames[0].size())
        self.move(100, 100)

        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.next_frame)
        self.anim_timer.start(180)

        self.physics = QTimer()
        self.physics.timeout.connect(self.gravity)
        self.physics.start(20)

        self.brain = QTimer()
        self.brain.timeout.connect(self.think)
        self.brain.start(10000)

        self.moved = False
        self.vy = 0
        self.vx = 0

        self.customActions = {}

        customNum = 0
        while f"custom{customNum}" in options.keys() and f"custom{customNum}_chance" in options.keys() and f"custom{customNum}_length" in options.keys():
            try:
                if options[f"custom{customNum}"] != "":
                    module_name = options[f"custom{customNum}"]
                    spec = importlib.util.spec_from_file_location(module_name, f"{self.skin}/{module_name}.py")
                    foo = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = foo
                    spec.loader.exec_module(foo)
                    self.customActions[module_name] = [foo, options[f"custom{customNum}_chance"], options[f"custom{customNum}_rotate"]]
                    self.animation[module_name + "_left"] = [
                        QPixmap(f"{self.skin}/{module_name}_{i}.png").transformed(self.scale) for i in
                        range(1, options[f"custom{customNum}_length"] + 1)]
                    self.animation[module_name + "_right"] = [
                        QPixmap(f"{self.skin}/{module_name}_{i}.png").transformed(mirror).transformed(self.scale) for i in
                        range(1, options[f"custom{customNum}_length"] + 1)]
                else:
                    print("Error while loading", options[f"custom{customNum}"])
            except Exception:
                print("Error while loading", options[f"custom{customNum}"])
            customNum += 1

        if "main_script" in options.keys():
            module_name = options["main_script"]
            print(module_name)
            spec = importlib.util.spec_from_file_location(module_name, f"{self.skin}/{module_name}.py")
            self.main_func = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = self.main_func
            spec.loader.exec_module(self.main_func)

            def run_main_func():
                params = {
                    "current_frame": self.current_frame,
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.size().width(),
                    "height": self.size().height(),
                    "cur_thought": self.thoughts,
                    "mouseX": pyautogui.position()[0],
                    "mouseY": pyautogui.position()[1]
                }
                new_params = self.main_func.tick(params)
                self.current_frame = new_params["current_frame"]
                self.move(new_params["x"], new_params["y"])
                self.thoughts = new_params["cur_thought"]

            if hasattr(self.main_func, "tick"):
                self.main_func_timer = QTimer()
                self.main_func_timer.timeout.connect(run_main_func)
                self.main_func_timer.start(100)
            else:
                print("No tick function found")


        with open("chances.json", mode='r') as file:
            data = json.load(file)
            chances = [data[i] for i in data.keys()]
            multiplier = 1
            while any([int(i * multiplier) != i * multiplier for i in chances]) and multiplier <= 1000:
                multiplier *= 10
            chances = [i * multiplier for i in chances]
            sumi = sum(chances)
            possible = []
            for i in data.keys():
                possible += int(data[i] * multiplier) * [i]

            self.available_actions = possible

        for customAction in self.customActions.keys():
            self.available_actions += int(self.customActions[customAction][1] * multiplier) * [customAction + "_custom"]

        self.targetX = 100
        self.dragging = False
        self.tackling = False
        self.thoughts = "writing"

        self.show()

    def close_pet(self):
        self.close()

    def next_frame(self):
        oldHeight = self.size().height()
        newHeight = self.frames[0].size().height()
        if oldHeight != newHeight:
            self.move(self.x(), self.y() + (oldHeight - newHeight))

        if len(self.thoughts.split("_")) >= 2 and self.thoughts.split("_")[-1] == "custom":
            actionName = self.thoughts.split("_")
            del actionName[-1]
            actionName = "_".join(actionName)
            if self.customActions[actionName][2]:
                if pyautogui.position()[0] > self.x():
                    self.frames = self.animation[actionName + "_right"]
                else:
                    self.frames = self.animation[actionName + "_left"]

        if self.size() != self.frames[0].size():
            self.resize(self.frames[0].size())
        if self.thoughts == "move" or self.thoughts == "following":
            if abs(self.vy) + abs(self.vx) != 0:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.setPixmap(self.frames[self.current_frame])
            else:
                self.current_frame = 0
                self.setPixmap(self.frames[self.current_frame])
        elif len(self.thoughts.split("_")) >= 2 and self.thoughts.split("_")[-1] == "custom":
            actionName = self.thoughts.split("_")
            del actionName[-1]
            actionName = "_".join(actionName)
            if hasattr(self.customActions[actionName][0], "animate"):
                params = {
                    "current_frame": self.current_frame,
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.size().width(),
                    "height": self.size().height(),
                    "cur_thought": self.thoughts,
                    "mouseX": pyautogui.position()[0],
                    "mouseY": pyautogui.position()[1]
                }
                self.current_frame = max(self.customActions[actionName][0].animate(params) % len(self.frames), 0)
                self.setPixmap(self.frames[self.current_frame])
            else:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.setPixmap(self.frames[self.current_frame])
        else:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.setPixmap(self.frames[self.current_frame])

    def gravity(self):
        if not self.dragging:
            screen_geometry = QApplication.primaryScreen().geometry()
            pet_size = self.size()

            new_x = self.x()
            if self.y() < screen_geometry.height() - pet_size.height():
                self.vy -= g
            new_y = min(screen_geometry.height() - pet_size.height(),
                        self.y() - self.vy)

            if self.y() == screen_geometry.height() - pet_size.height() and self.vy < 0:
                self.vy = 0
                if self.frames == self.animation["falling_left"] or self.frames == self.animation["falling_right"]:
                    if self.thoughts == "move":
                        self.frames = self.animation["right"]
                    if self.thoughts == "tackle":
                        self.frames = self.animation["tackle_left"]
                    if self.thoughts == "writing":
                        self.frames = self.animation["writing_left"]
                    if self.thoughts == "following":
                        self.frames = self.animation["right"]
                    if len(self.thoughts.split("_")) >= 2 and self.thoughts.split("_")[-1] == "custom":
                        actionName = self.thoughts.split("_")
                        del actionName[-1]
                        actionName = "_".join(actionName)
                        self.frames = self.animation[actionName + "_left"]

            if self.y() != new_y:
                if pyautogui.position()[0] > self.x():
                    self.frames = self.animation["falling_right"]
                else:
                    self.frames = self.animation["falling_left"]
                self.move(new_x, new_y)
            else:
                self.move_pet()

    def move_pet(self):
        screen_geometry = QApplication.primaryScreen().geometry()

        if self.thoughts == "move" or self.thoughts == "following":
            if self.thoughts == "following":
                new_targetX = pyautogui.position()[0] - self.size().width() if self.frames == self.animation[
                    "left"] else pyautogui.position()[0]
                if abs(new_targetX - self.x()) >= self.size().width():
                    self.targetX = new_targetX
                if self.y() > pyautogui.position()[1] and abs(self.y() - pyautogui.position()[1]) <= (
                        self.size().height() * (
                        self.size().height() / self.jumpHeight)) and self.y() == screen_geometry.height() - self.size().height() and abs(
                    new_targetX - self.x()) <= self.size().width() * 2:
                    self.vy = int(
                        20 * math.sin(2 * ((abs(self.y() - pyautogui.position()[1])) / (self.size().height() * 1.3))))
                    new_y = self.y() - self.vy
                else:
                    new_y = self.y()
            else:
                new_y = self.y()
            if self.x() < self.targetX and self.y() == new_y:
                self.frames = self.animation["right"]
                self.vx = self.maxspeed if abs(self.x() - self.targetX) >= 10 else 1
            elif self.x() > self.targetX and self.y() == new_y:
                self.frames = self.animation["left"]
                self.vx = -self.maxspeed if abs(self.x() - self.targetX) >= 10 else -1
            else:
                self.vx = 0

            new_x = self.x() + self.vx

            if self.vx != 0:
                self.move(new_x, new_y)
        elif self.thoughts == "writing" and self.rotateWriting:
            if pyautogui.position()[0] > self.x():
                self.frames = self.animation["writing_right"]
            else:
                self.frames = self.animation["writing_left"]
        elif self.thoughts == "tackle":
            if pyautogui.position()[0] > self.x():
                self.frames = self.animation["tackle_right"]
            else:
                self.frames = self.animation["tackle_left"]
            self.tackle_mouse_if_close()

    def think(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        pet_size = self.size()

        self.thoughts = random.choice(self.available_actions)
        self.tackling = False

        if not self.dragging:
            if self.thoughts == 'move':
                self.targetX = random.randint(pet_size.width(), screen_geometry.width() - pet_size.width())
            elif self.thoughts == 'tackle':
                self.tackling = True
            elif self.thoughts == "writing":
                self.frames = self.animation["writing_left"]
            elif len(self.thoughts.split("_")) >= 2 and self.thoughts.split("_")[-1] == "custom":
                actionName = self.thoughts.split("_")
                del actionName[-1]
                actionName = "_".join(actionName)
                self.frames = self.animation[actionName + "_left"]
                params = {
                    "current_frame": self.current_frame,
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.size().width(),
                    "height": self.size().height(),
                    "cur_thought": self.thoughts,
                    "mouseX": pyautogui.position()[0],
                    "mouseY": pyautogui.position()[1]
                }
                if hasattr(self.customActions[actionName][0], "action"):
                    self.customActions[actionName][0].start(params)
                else:
                    print("Error while preforming action. No available action")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.frames = self.animation["dragging"]
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.setPixmap(self.frames[self.current_frame])
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def tackle_mouse_if_close(self):
        if self.tackling:
            pet_pos = self.pos()
            pet_size = self.size()
            pet_center_x = pet_pos.x() + pet_size.width() // 2
            pet_center_y = pet_pos.y() + pet_size.height() // 2

            mouse_x, mouse_y = pyautogui.position()

            dx = mouse_x - pet_center_x
            dy = mouse_y - pet_center_y

            distance = (dx ** 2 + dy ** 2) ** 0.5

            tackle_radius = 40
            push_distance = 30

            if distance < tackle_radius and distance != 0:
                nx = dx / distance
                ny = dy / distance

                new_mouse_x = int(pet_center_x + nx * (tackle_radius + push_distance))
                new_mouse_y = int(pet_center_y + ny * (tackle_radius + push_distance))

                screen_width, screen_height = pyautogui.size()
                new_mouse_x = max(0, min(new_mouse_x, screen_width - 1))
                new_mouse_y = max(0, min(new_mouse_y, screen_height - 1))

                pyautogui.moveTo(new_mouse_x, new_mouse_y, duration=0.2)
