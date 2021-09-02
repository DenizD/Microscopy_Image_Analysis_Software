from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider, QLabel, QPushButton, QLineEdit, QWidget, QHBoxLayout
from PyQt5.QtGui import QIntValidator

class CustomSlider(QSlider):
    def __init__(self, parent, name, valueChanged=None, range=(0,100)):
        QSlider.__init__(self, Qt.Horizontal, parent)
        self.name = name
        self.setStyleSheet(f'background: {name};')
        self.setRange(*range)
        self.valueChanged.connect(valueChanged)


class CustomButton(QWidget):
    def __init__(self, parent, name, onPressed=None, args=None):
        QWidget.__init__(self, parent)

        self.btn = QPushButton(name)
        if args:
            self.btn.clicked.connect(lambda checked, arg=args: onPressed(arg))
        else:
            self.btn.clicked.connect(lambda checked, arg=args: onPressed())

        self.label = QLabel()

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.btn)
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)


class CustomLineEdit(QLineEdit):
    def __init__(self, parent, name, onChanged=None):
        QLineEdit.__init__(self, "", parent)

        self.setValidator(QIntValidator())
        self.setFixedWidth(200)
        self.setMaxLength(4)
        self.setPlaceholderText(name)
        self.textChanged.connect(onChanged)
 
