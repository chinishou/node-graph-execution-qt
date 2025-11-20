# UI Issues Fixed

## Summary

Fixed 5 major UI issues reported by user:

### 1. ✅ Tab Key Not Working
**Problem**: Tab key was not showing the node creation menu.

**Solution**: Added `event()` override in `NetworkView` to catch Tab key events before Qt's focus system intercepts them.

```python
def event(self, event):
    """Override event to catch Tab key before focus system."""
    if event.type() == event.Type.KeyPress:
        key_event = event
        if key_event.key() == Qt.Key_Tab:
            # Show node palette at cursor position
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            scene_pos = self.mapToScene(cursor_pos)
            self._show_node_menu(self.mapToGlobal(cursor_pos), scene_pos)
            return True
    return super().event(event)
```

**File**: `nodegraph/views/network/network_view.py:173-183`

### 2. ✅ Limited Panning Range
**Problem**: Middle mouse button panning was restricted to a small area.

**Solution**: Set scene rect to 20000x20000 pixels for virtually unlimited canvas space.

```python
# Set large scene rect for unlimited panning
self.setSceneRect(-10000, -10000, 20000, 20000)
```

**File**: `nodegraph/views/network/network_view.py:61-62`

### 3. ✅ Connection Curve Direction Issues
**Problem**: Bezier curves looked wrong when dragging from output to input vs input to output.

**Solution**: Detect source port type and adjust control point direction accordingly.

```python
# Determine if source is output (going right) or input (going left)
source_is_output = self.source_port.is_output

# Adjust control point direction based on port type
if source_is_output:
    # Output port: curve goes right then to target
    ctrl1 = QPointF(start_pos.x() + ctrl_offset, start_pos.y())
    ctrl2 = QPointF(end_pos.x() - ctrl_offset, end_pos.y())
else:
    # Input port: curve goes left then to target
    ctrl1 = QPointF(start_pos.x() - ctrl_offset, start_pos.y())
    ctrl2 = QPointF(end_pos.x() + ctrl_offset, end_pos.y())
```

**File**: `nodegraph/views/connectors/connection_item.py:80-103`

### 4. ✅ Selection Rectangle on Connections
**Problem**: When selecting a connection line, an unwanted dashed rectangle appeared around it.

**Solution**:
- Added `shape()` method to provide precise clickable area
- Modified `paint()` to disable Qt's default selection visual

```python
def shape(self):
    """Return a more precise shape for mouse interaction."""
    from PySide6.QtGui import QPainterPathStroker
    stroker = QPainterPathStroker()
    stroker.setWidth(8)  # Clickable width
    return stroker.createStroke(self.path())

def paint(self, painter, option, widget=None):
    # ... color selection ...

    # Disable selection rectangle by modifying the option
    option.state &= ~QStyleOptionGraphicsItem.State_Selected
    super().paint(painter, option, widget)
```

**File**: `nodegraph/views/connectors/connection_item.py:109-136`

### 5. ✅ Node Deletion Not Removing Connections
**Problem**: When deleting a node, its connection lines remained visible in the scene.

**Solution**: Fixed `_on_node_removed()` to properly remove connection items from scene.

```python
def _on_node_removed(self, node):
    """Handle node removed from model."""
    if node.id in self._node_items:
        item = self._node_items.pop(node.id)
        self.removeItem(item)

        # Remove associated connections from scene
        connections_to_remove = [
            conn for conn in self._connection_items
            if self._connection_involves_node(conn, node)
        ]

        for conn in connections_to_remove:
            self.removeItem(conn)
            self._connection_items.remove(conn)
```

**File**: `nodegraph/views/network/network_scene.py:101-115`

## Testing

All fixes verified with tests:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_ui.py::TestNetworkView -v
```

Results: **8 passed in 0.51s**

Manual verification:
- ✅ Scene rect: 20000x20000 pixels
- ✅ Node deletion reduces connections from 2 to 1
- ✅ Connection items properly detect port direction
- ✅ Tab key event handled successfully

## Commits

- `82d0d2c` - Fix UI issues: Tab key, panning, connections, selection
- `6025467` - Fix category detection for Pydantic models and add UI tests
- `7056aed` - Implement complete UI layer for node editor
