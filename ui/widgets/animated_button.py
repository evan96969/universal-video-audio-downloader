"""
MediaFlow — Animated Button widget.
Provides smooth background color transition on hover using QVariantAnimation.
"""

from PySide6.QtCore import QVariantAnimation
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor

class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None, default_color="#f8f9fa", hover_color="#e9ecef", text_color="#212529"):
        super().__init__(text, parent)
        self._default_color = QColor(default_color)
        self._hover_color = QColor(hover_color)
        self._current_color = self._default_color
        self._text_color = text_color
        
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(250)
        self.animation.valueChanged.connect(self._update_stylesheet)
        
        self._update_stylesheet(self._current_color)

    def setColors(self, default_color, hover_color, text_color="#ffffff"):
        self._default_color = QColor(default_color)
        self._hover_color = QColor(hover_color)
        self._text_color = text_color
        self._current_color = self._default_color
        self._update_stylesheet(self._current_color)

    def _update_stylesheet(self, color):
        self._current_color = color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                color: {self._text_color};
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:disabled {{
                background-color: #e9ecef;
                color: #adb5bd;
            }}
        """)

    def enterEvent(self, event):
        if self.isEnabled():
            self.animation.stop()
            self.animation.setStartValue(self._current_color)
            self.animation.setEndValue(self._hover_color)
            self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isEnabled():
            self.animation.stop()
            self.animation.setStartValue(self._current_color)
            self.animation.setEndValue(self._default_color)
            self.animation.start()
        super().leaveEvent(event)
