"""
Tests for StickyNoteItem UI Component
======================================

Test sticky note functionality:
- Creation and positioning
- Text editing
- Color and size management
- Resizing
- Selection
- Serialization
"""

import pytest
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from PySide6.QtTest import QTest
from uuid import UUID

from nodegraph.views.notes.sticky_note_item import StickyNoteItem


@pytest.fixture
def scene(qtbot):
    """Create a QGraphicsScene for testing sticky notes."""
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)
    return scene


class TestStickyNoteCreation:
    """Tests for sticky note creation and basic properties."""

    def test_note_creation_default(self, scene):
        """Test creating a sticky note with default parameters."""
        note = StickyNoteItem()
        scene.addItem(note)

        assert note is not None
        assert note.note_id is not None
        assert note.get_text() == ""
        assert note.get_color() == "yellow"
        size = note.get_size()
        assert size[0] == StickyNoteItem.DEFAULT_WIDTH
        assert size[1] == StickyNoteItem.DEFAULT_HEIGHT

    def test_note_creation_with_position(self, scene):
        """Test creating a sticky note at a specific position."""
        position = QPointF(100, 200)
        note = StickyNoteItem(position=position)
        scene.addItem(note)

        assert note.pos() == position

    def test_note_creation_with_text(self, scene):
        """Test creating a sticky note with text."""
        note = StickyNoteItem(text="Hello World")
        scene.addItem(note)

        assert note.get_text() == "Hello World"

    def test_note_creation_with_color(self, scene):
        """Test creating a sticky note with custom color."""
        note = StickyNoteItem(color="green")
        scene.addItem(note)

        assert note.get_color() == "green"

    def test_note_creation_with_size(self, scene):
        """Test creating a sticky note with custom size."""
        note = StickyNoteItem(width=300, height=200)
        scene.addItem(note)

        size = note.get_size()
        assert size[0] == 300
        assert size[1] == 200

    def test_note_creation_with_id(self, scene):
        """Test creating a sticky note with specific ID."""
        test_id = UUID("12345678-1234-5678-1234-567812345678")
        note = StickyNoteItem(note_id=test_id)
        scene.addItem(note)

        assert note.note_id == test_id

    def test_note_z_value(self, scene):
        """Test that sticky notes render behind other items."""
        note = StickyNoteItem()
        scene.addItem(note)

        # Sticky notes should have negative z-value to render behind nodes
        assert note.zValue() == -1

    def test_note_flags(self, scene):
        """Test that sticky notes have correct flags."""
        from PySide6.QtWidgets import QGraphicsItem

        note = StickyNoteItem()
        scene.addItem(note)

        assert note.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        assert note.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        assert note.flags() & QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges


class TestStickyNoteText:
    """Tests for text editing functionality."""

    def test_get_text(self, scene):
        """Test getting note text."""
        note = StickyNoteItem(text="Test Text")
        scene.addItem(note)

        assert note.get_text() == "Test Text"

    def test_set_text(self, scene):
        """Test setting note text."""
        note = StickyNoteItem()
        scene.addItem(note)

        note.set_text("New Text")
        assert note.get_text() == "New Text"

    def test_text_item_exists(self, scene):
        """Test that internal text item exists."""
        note = StickyNoteItem(text="Hello")
        scene.addItem(note)

        assert note._text_item is not None
        assert note._text_item.toPlainText() == "Hello"

    def test_double_click_enables_editing(self, scene, qtbot):
        """Test that double-clicking enables text editing."""
        note = StickyNoteItem(text="Edit Me")
        scene.addItem(note)

        # Initially text should not be editable
        assert note._text_item.textInteractionFlags() == Qt.NoTextInteraction

        # Simulate double-click
        from PySide6.QtGui import QMouseEvent
        event = QMouseEvent(
            QMouseEvent.MouseButtonDblClick,
            QPointF(50, 50),  # Inside the note
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        note.mouseDoubleClickEvent(event)

        # Text should now be editable
        assert note._text_item.textInteractionFlags() == Qt.TextEditorInteraction

    def test_focus_out_disables_editing(self, scene, qtbot):
        """Test that losing focus disables text editing."""
        note = StickyNoteItem(text="Test")
        scene.addItem(note)

        # Enable editing
        note._text_item.setTextInteractionFlags(Qt.TextEditorInteraction)

        # Simulate focus out
        from PySide6.QtGui import QFocusEvent
        event = QFocusEvent(QFocusEvent.FocusOut)
        note.focusOutEvent(event)

        # Text should no longer be editable
        assert note._text_item.textInteractionFlags() == Qt.NoTextInteraction


class TestStickyNoteColor:
    """Tests for color management."""

    def test_get_color(self, scene):
        """Test getting note color."""
        note = StickyNoteItem(color="blue")
        scene.addItem(note)

        assert note.get_color() == "blue"

    def test_set_color(self, scene):
        """Test setting note color."""
        note = StickyNoteItem(color="yellow")
        scene.addItem(note)

        note.set_color("pink")
        assert note.get_color() == "pink"

    def test_set_invalid_color(self, scene):
        """Test that invalid color is ignored."""
        note = StickyNoteItem(color="yellow")
        scene.addItem(note)

        note.set_color("invalid_color")
        # Should keep original color
        assert note.get_color() == "yellow"

    def test_all_color_presets(self, scene):
        """Test all available color presets."""
        colors = ['yellow', 'green', 'blue', 'pink', 'orange', 'purple']

        for color in colors:
            note = StickyNoteItem(color=color)
            scene.addItem(note)
            assert note.get_color() == color
            assert color in StickyNoteItem.COLORS


class TestStickyNoteSize:
    """Tests for size management."""

    def test_get_size(self, scene):
        """Test getting note size."""
        note = StickyNoteItem(width=250, height=180)
        scene.addItem(note)

        size = note.get_size()
        assert size == (250, 180)

    def test_set_size(self, scene):
        """Test setting note size."""
        note = StickyNoteItem()
        scene.addItem(note)

        note.set_size(300, 250)
        size = note.get_size()
        assert size == (300, 250)

    def test_set_size_respects_minimum(self, scene):
        """Test that size cannot go below minimum."""
        note = StickyNoteItem()
        scene.addItem(note)

        # Try to set size below minimum
        note.set_size(50, 50)  # Below MIN_WIDTH and MIN_HEIGHT

        size = note.get_size()
        assert size[0] >= StickyNoteItem.MIN_WIDTH
        assert size[1] >= StickyNoteItem.MIN_HEIGHT

    def test_bounding_rect(self, scene):
        """Test bounding rectangle matches size."""
        note = StickyNoteItem(width=300, height=200)
        scene.addItem(note)

        rect = note.boundingRect()
        assert rect.width() == 300
        assert rect.height() == 200
        assert rect.x() == 0
        assert rect.y() == 0


class TestStickyNoteResizing:
    """Tests for resizing functionality."""

    def test_resize_handle_rect(self, scene):
        """Test resize handle rectangle calculation."""
        note = StickyNoteItem(width=200, height=150)
        scene.addItem(note)

        handle = note._get_resize_handle_rect()

        # Handle should be in bottom-right corner
        assert handle.x() == 200 - StickyNoteItem.RESIZE_HANDLE_SIZE
        assert handle.y() == 150 - StickyNoteItem.RESIZE_HANDLE_SIZE
        assert handle.width() == StickyNoteItem.RESIZE_HANDLE_SIZE
        assert handle.height() == StickyNoteItem.RESIZE_HANDLE_SIZE

    def test_mouse_press_on_resize_handle(self, scene):
        """Test clicking on resize handle starts resizing."""
        note = StickyNoteItem(width=200, height=150)
        scene.addItem(note)
        note.setSelected(True)

        # Create mouse press event on resize handle
        from PySide6.QtGui import QMouseEvent
        handle_pos = QPointF(195, 145)  # Inside resize handle
        event = QMouseEvent(
            QMouseEvent.MouseButtonPress,
            handle_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )

        # Create a simple lambda that returns the scene position
        # (in item coordinates, scenePos equals the pos since item is at origin)
        event.scenePos = lambda: handle_pos

        note.mousePressEvent(event)

        assert note._is_resizing

    def test_mouse_move_while_resizing(self, scene):
        """Test dragging to resize note."""
        note = StickyNoteItem(width=200, height=150)
        scene.addItem(note)
        note.setSelected(True)

        # Start resizing
        note._is_resizing = True
        note._resize_start_pos = QPointF(195, 145)
        note._resize_start_size = (200, 150)

        # Create mouse move event
        from PySide6.QtGui import QMouseEvent
        new_pos = QPointF(245, 195)  # 50 pixels to the right and down
        event = QMouseEvent(
            QMouseEvent.MouseMove,
            new_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        event.scenePos = lambda: new_pos

        note.mouseMoveEvent(event)

        # Size should have increased
        size = note.get_size()
        assert size[0] == 250  # 200 + 50
        assert size[1] == 200  # 150 + 50

    def test_mouse_release_stops_resizing(self, scene):
        """Test releasing mouse stops resizing."""
        note = StickyNoteItem(width=200, height=150)
        scene.addItem(note)

        note._is_resizing = True

        # Create mouse release event
        from PySide6.QtGui import QMouseEvent
        event = QMouseEvent(
            QMouseEvent.MouseButtonRelease,
            QPointF(200, 150),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )

        note.mouseReleaseEvent(event)

        assert not note._is_resizing

    def test_resizing_respects_minimum_size(self, scene):
        """Test that resizing cannot go below minimum size."""
        note = StickyNoteItem(width=200, height=150)
        scene.addItem(note)

        note._is_resizing = True
        note._resize_start_pos = QPointF(195, 145)
        note._resize_start_size = (200, 150)

        # Try to resize to very small size
        from PySide6.QtGui import QMouseEvent
        new_pos = QPointF(50, 50)  # Way smaller than minimum
        event = QMouseEvent(
            QMouseEvent.MouseMove,
            new_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        event.scenePos = lambda: new_pos

        note.mouseMoveEvent(event)

        # Size should be at minimum
        size = note.get_size()
        assert size[0] >= StickyNoteItem.MIN_WIDTH
        assert size[1] >= StickyNoteItem.MIN_HEIGHT


class TestStickyNoteSelection:
    """Tests for selection handling."""

    def test_selection_state(self, scene):
        """Test selection state tracking."""
        note = StickyNoteItem()
        scene.addItem(note)

        assert not note._is_selected

        note.setSelected(True)
        assert note.isSelected()

    def test_item_change_tracks_selection(self, scene):
        """Test that itemChange updates selection state."""
        note = StickyNoteItem()
        scene.addItem(note)

        # Trigger selection change
        note.setSelected(True)

        # _is_selected should be updated
        assert note._is_selected


class TestStickyNoteSerialization:
    """Tests for serialization functionality."""

    def test_to_dict(self, scene):
        """Test serializing note to dictionary."""
        position = QPointF(100, 150)
        note = StickyNoteItem(
            position=position,
            text="Test Note",
            color="green",
            width=250,
            height=180
        )
        scene.addItem(note)

        data = note.to_dict()

        assert data['x'] == 100
        assert data['y'] == 150
        assert data['text'] == "Test Note"
        assert data['color'] == "green"
        assert data['width'] == 250
        assert data['height'] == 180
        assert 'id' in data
        assert isinstance(data['id'], str)

    def test_from_dict(self, scene):
        """Test creating note from dictionary."""
        data = {
            'id': '12345678-1234-5678-1234-567812345678',
            'x': 100,
            'y': 150,
            'text': "Test Note",
            'color': "blue",
            'width': 300,
            'height': 200
        }

        note = StickyNoteItem.from_dict(data)
        scene.addItem(note)

        assert note.pos() == QPointF(100, 150)
        assert note.get_text() == "Test Note"
        assert note.get_color() == "blue"
        size = note.get_size()
        assert size == (300, 200)
        assert str(note.note_id) == data['id']

    def test_from_dict_with_defaults(self, scene):
        """Test creating note from minimal dictionary."""
        data = {}

        note = StickyNoteItem.from_dict(data)
        scene.addItem(note)

        assert note.pos() == QPointF(0, 0)
        assert note.get_text() == ""
        assert note.get_color() == "yellow"
        size = note.get_size()
        assert size[0] == StickyNoteItem.DEFAULT_WIDTH
        assert size[1] == StickyNoteItem.DEFAULT_HEIGHT

    def test_round_trip_serialization(self, scene):
        """Test that serialization and deserialization preserves data."""
        original = StickyNoteItem(
            position=QPointF(50, 75),
            text="Round Trip Test",
            color="pink",
            width=280,
            height=190
        )
        scene.addItem(original)

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = StickyNoteItem.from_dict(data)
        scene.addItem(restored)

        # Verify all properties match
        assert restored.pos() == original.pos()
        assert restored.get_text() == original.get_text()
        assert restored.get_color() == original.get_color()
        assert restored.get_size() == original.get_size()
        assert restored.note_id == original.note_id


class TestStickyNotePainting:
    """Tests for painting and visual rendering."""

    def test_paint_does_not_crash(self, scene):
        """Test that painting does not crash."""
        note = StickyNoteItem(text="Paint Test", color="orange")
        scene.addItem(note)

        # Trigger paint by rendering scene
        from PySide6.QtGui import QImage, QPainter
        image = QImage(400, 300, QImage.Format_ARGB32)
        painter = QPainter(image)
        scene.render(painter)
        painter.end()

        # If we get here, painting succeeded
        assert True

    def test_paint_selected_state(self, scene):
        """Test painting in selected state."""
        note = StickyNoteItem()
        scene.addItem(note)
        note.setSelected(True)

        # Trigger paint
        from PySide6.QtGui import QImage, QPainter
        image = QImage(400, 300, QImage.Format_ARGB32)
        painter = QPainter(image)
        scene.render(painter)
        painter.end()

        # If we get here, painting with selection succeeded
        assert True

    def test_paint_all_colors(self, scene):
        """Test painting with all color options."""
        colors = ['yellow', 'green', 'blue', 'pink', 'orange', 'purple']

        for i, color in enumerate(colors):
            note = StickyNoteItem(
                position=QPointF(i * 50, 0),
                color=color
            )
            scene.addItem(note)

        # Trigger paint
        from PySide6.QtGui import QImage, QPainter
        image = QImage(600, 300, QImage.Format_ARGB32)
        painter = QPainter(image)
        scene.render(painter)
        painter.end()

        # If we get here, painting all colors succeeded
        assert True


def run_all_tests():
    """Run all sticky note tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_all_tests()
