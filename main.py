import sys
import random
import json
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap
import pyautogui

g = 2
class DesktopPet(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        options = {}

        with open("options.json", mode='r') as file:
            options = json.load(file)

        self.animation = {
            "left": [QPixmap(f"frame_{i}.png") for i in range(1, options["left"] + 1)],
            "right": [QPixmap(f"frame_{i}_r.png") for i in range(1, options["right"] + 1)],
            "tackle_left": [QPixmap(f"tackle_{i}.png") for i in range(1, options["tackle_left"] + 1)],
            "tackle_right": [QPixmap(f"tackle_{i}_r.png") for i in range(1, options["tackle_right"] + 1)],
            "writing": [QPixmap(f"writing_{i}.png") for i in range(1, options["writing"] + 1)],
            "dragging": [QPixmap(f"dragging_{i}.png") for i in range(1, options["dragging"] + 1)],
            "falling": [QPixmap(f"falling_{i}.png") for i in range(1, options["falling"] + 1)],
        }

        self.frames = self.animation["left"]
        self.current_frame = 0
        self.setPixmap(self.frames[self.current_frame])

        self.resize(self.frames[0].size())
        self.move(100, 100)

        # Timer for animation frames
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
        self.maxspeed = 2
        self.vy = 0
        self.vx = 0

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

            random.shuffle(possible)
            self.available_actions = possible

        self.targetX = 100
        self.dragging = False
        self.tackling = False
        self.thoughts = "move"

    def next_frame(self):
        if self.size !=  self.frames[0].size():
            self.resize(self.frames[0].size())
        if self.thoughts == "move":
            if (self.vy) + abs(self.vx) != 0:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.setPixmap(self.frames[self.current_frame])
            else:
                if self.current_frame != 3 and len(self.frames) >= 4:
                    self.current_frame = 3
                    self.setPixmap(self.frames[self.current_frame])
        elif self.thoughts == "tackle" or self.thoughts == "writing" or self.thoughts == "":
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
                        self.y() - self.vy) if self.y() < screen_geometry.height() - pet_size.height() else self.y()

            if self.y() == screen_geometry.height() - pet_size.height():
                self.vy = 0
                if self.frames == self.animation["falling"]:
                    if self.thoughts == "move":
                        self.frames = self.animation["right"]
                    if self.thoughts == "tackle":
                        self.frames = self.animation["tackle_left"]
                    if self.thoughts == "writing":
                        self.frames = self.animation["writing"]

            if self.y() != new_y:
                self.frames = self.animation["falling"]
                self.move(new_x, new_y)
            else:
                self.move_pet()

    def move_pet(self):
        if self.thoughts == "move":
            new_y = self.y()
            if self.x() < self.targetX:
                self.frames = self.animation["right"]
                self.vx = self.maxspeed if abs(self.x() - self.targetX) >= 10 else 1
            elif self.x() > self.targetX:
                self.frames = self.animation["left"]
                self.vx = -self.maxspeed if abs(self.x() - self.targetX) >= 10 else -1
            else:
                self.vx = 0

            new_x = self.x() + self.vx

            if self.vx != 0:
                self.move(new_x, new_y)
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
                self.frames = self.animation["writing"]

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())
