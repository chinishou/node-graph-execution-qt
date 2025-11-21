"""
Sticky Note Item
=================

QGraphicsItem for rendering sticky notes in the network view.
"""

from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsTextItem, QStyleOptionGraphicsItem,
    QWidget, QTextEdit, QGraphicsProxyWidget
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QTextOption

from typing import Optional
from uuid import uuid4, UUID


class StickyNoteItem(QGraphicsItem):
    """
    Graphics item for rendering a sticky note.

    Features:
    - Resizable
    - Editable text
    - Movable
    - Multiple color options
    - Always renders behind nodes
    """

    # Default dimensions
    DEFAULT_WIDTH = 200
    DEFAULT_HEIGHT = 150
    MIN_WIDTH = 100
    MIN_HEIGHT = 80
    RESIZE_HANDLE_SIZE = 12
    HEADER_HEIGHT = 30
    PADDING = 10

    # Color presets
    COLORS = {
        'yellow': QColor(255, 253, 150),
        'green': QColor(200, 255, 200),
        'blue': QColor(200, 230, 255),
        'pink': QColor(255, 200, 230),
        'orange': QColor(255, 220, 180),
        'purple': QColor(230, 200, 255),
    }

    def __init__(self, position: QPointF = None, text: str = "",
                 color: str = 'yellow', width: float = None, height: float = None,
                 note_id: UUID = None, parent=None):
        super().__init__(parent)

        self.note_id = note_id or uuid4()
        self._text = text
        self._color_name = color
        self._width = width or self.DEFAULT_WIDTH
        self._height = height or self.DEFAULT_HEIGHT

        # State
        self._is_selected = False
        self._is_resizing = False
        self._resize_start_pos = None
        self._resize_start_size = None

        # Setup
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(-1)  # Behind nodes

        if position:
            self.setPos(position)

        # Create text item for displaying/editing
        self._text_item = QGraphicsTextItem(self)
        self._text_item.setPos(self.PADDING, self.HEADER_HEIGHT + self.PADDING)
        self._text_item.setTextWidth(self._width - 2 * self.PADDING)
        self._text_item.setPlainText(self._text)
        self._text_item.setDefaultTextColor(QColor(40, 40, 40))

        font = QFont("Arial", 10)
        self._text_item.setFont(font)

        # Make text editable on double-click
        self._text_item.setTextInteractionFlags(Qt.NoTextInteraction)

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle."""
        return QRectF(0, 0, self._width, self._height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the sticky note."""
        painter.setRenderHint(QPainter.Antialiasing)

        # Get color
        color = self.COLORS.get(self._color_name, self.COLORS['yellow'])

        # Draw main body
        painter.setBrush(QBrush(color))

        if self.isSelected():
            painter.setPen(QPen(QColor(100, 150, 255), 2))
        else:
            painter.setPen(QPen(color.darker(110), 1))

        painter.drawRoundedRect(0, 0, self._width, self._height, 5, 5)

        # Draw header area (slightly darker)
        header_color = color.darker(105)
        painter.setBrush(QBrush(header_color))
        painter.setPen(Qt.NoPen)

        painter.drawRoundedRect(0, 0, self._width, self.HEADER_HEIGHT, 5, 5)
        painter.drawRect(0, self.HEADER_HEIGHT - 5, self._width, 5)

        # Draw header text
        painter.setPen(QPen(QColor(60, 60, 60)))
        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(self.PADDING, 0, self._width - 2 * self.PADDING, self.HEADER_HEIGHT),
                        Qt.AlignVCenter | Qt.AlignLeft, "Note")

        # Draw resize handle if selected
        if self.isSelected():
            handle_rect = self._get_resize_handle_rect()
            painter.setBrush(QBrush(QColor(100, 150, 255)))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawRect(handle_rect)

    def _get_resize_handle_rect(self) -> QRectF:
        """Get the resize handle rectangle."""
        return QRectF(
            self._width - self.RESIZE_HANDLE_SIZE,
            self._height - self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE
        )

    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            # Check if clicking on resize handle
            if self.isSelected():
                handle_rect = self._get_resize_handle_rect()
                if handle_rect.contains(event.pos()):
                    self._is_resizing = True
                    self._resize_start_pos = event.scenePos()
                    self._resize_start_size = (self._width, self._height)
                    event.accept()
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        if self._is_resizing:
            delta = event.scenePos() - self._resize_start_pos
            new_width = max(self.MIN_WIDTH, self._resize_start_size[0] + delta.x())
            new_height = max(self.MIN_HEIGHT, self._resize_start_size[1] + delta.y())

            self._width = new_width
            self._height = new_height
            self._text_item.setTextWidth(self._width - 2 * self.PADDING)

            self.prepareGeometryChange()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if self._is_resizing:
            self._is_resizing = False
            self._resize_start_pos = None
            self._resize_start_size = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to edit text."""
        if event.button() == Qt.LeftButton:
            # Enable text editing
            self._text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
            self._text_item.setFocus()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        """Handle focus out."""
        # Disable text editing when focus is lost
        self._text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        self._text = self._text_item.toPlainText()
        super().focusOutEvent(event)

    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemSelectedChange:
            self._is_selected = value
            self.update()

        return super().itemChange(change, value)

    # Getters and setters
    def get_text(self) -> str:
        """Get the note text."""
        return self._text_item.toPlainText()

    def set_text(self, text: str):
        """Set the note text."""
        self._text = text
        self._text_item.setPlainText(text)

    def get_color(self) -> str:
        """Get the color name."""
        return self._color_name

    def set_color(self, color_name: str):
        """Set the color."""
        if color_name in self.COLORS:
            self._color_name = color_name
            self.update()

    def get_size(self) -> tuple:
        """Get the size (width, height)."""
        return (self._width, self._height)

    def set_size(self, width: float, height: float):
        """Set the size."""
        self._width = max(self.MIN_WIDTH, width)
        self._height = max(self.MIN_HEIGHT, height)
        self._text_item.setTextWidth(self._width - 2 * self.PADDING)
        self.prepareGeometryChange()
        self.update()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        pos = self.pos()
        return {
            'id': str(self.note_id),
            'x': pos.x(),
            'y': pos.y(),
            'width': self._width,
            'height': self._height,
            'text': self.get_text(),
            'color': self._color_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'StickyNoteItem':
        """Create from dictionary."""
        note_id = UUID(data['id']) if 'id' in data else None
        position = QPointF(data.get('x', 0), data.get('y', 0))

        return cls(
            position=position,
            text=data.get('text', ''),
            color=data.get('color', 'yellow'),
            width=data.get('width', cls.DEFAULT_WIDTH),
            height=data.get('height', cls.DEFAULT_HEIGHT),
            note_id=note_id
        )
