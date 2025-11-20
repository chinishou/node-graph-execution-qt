"""
Main Window
===========

Main application window for the node editor.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence

from typing import Optional

from ..core.models import NetworkModel
from ..core.registry import NodeRegistry
from ..core.serialization import JSONSerializer
from .network.network_scene import NetworkScene
from .network.network_view import NetworkView
from .widgets.parameters_pane import ParametersPane
from .widgets.output_pane import OutputPane


class MainWindow(QMainWindow):
    """
    Main window for the node editor application.

    Contains:
    - Network view (center)
    - Parameters pane (right)
    - Output pane (bottom)
    - Menu bar and toolbar
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._network_model: Optional[NetworkModel] = None
        self._current_file: Optional[str] = None

        self._setup_ui()
        self._setup_menus()
        self._setup_connections()
        self._register_default_nodes()

        # Create new network
        self.new_network()

        # Restore settings
        self._restore_settings()

    def _setup_ui(self):
        """Setup the UI."""
        self.setWindowTitle("Node Graph Editor")
        self.setMinimumSize(1024, 768)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main splitter (horizontal)
        self._main_splitter = QSplitter(Qt.Horizontal)

        # Network view
        self._network_view = NetworkView()
        self._main_splitter.addWidget(self._network_view)

        # Right panel with parameters
        self._parameters_pane = ParametersPane()
        self._parameters_pane.setMinimumWidth(250)
        self._parameters_pane.setMaximumWidth(400)
        self._main_splitter.addWidget(self._parameters_pane)

        # Set splitter sizes
        self._main_splitter.setSizes([700, 300])

        # Vertical splitter for main content and output
        self._vertical_splitter = QSplitter(Qt.Vertical)
        self._vertical_splitter.addWidget(self._main_splitter)

        # Output pane
        self._output_pane = OutputPane()
        self._output_pane.setMinimumHeight(100)
        self._output_pane.setMaximumHeight(300)
        self._vertical_splitter.addWidget(self._output_pane)

        # Set vertical splitter sizes
        self._vertical_splitter.setSizes([600, 150])

        main_layout.addWidget(self._vertical_splitter)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
            }
            QSplitter::handle {
                background-color: #3c3c3c;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #dcdcdc;
            }
            QMenuBar::item:selected {
                background-color: #4c4c4c;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #dcdcdc;
                border: 1px solid #5c5c5c;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QToolBar {
                background-color: #3c3c3c;
                border: none;
                spacing: 4px;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #dcdcdc;
            }
        """)

    def _setup_menus(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_network)
        file_menu.addAction(new_action)

        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        delete_action = QAction("Delete", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self._delete_selected)
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        execute_all_action = QAction("Execute All", self)
        execute_all_action.setShortcut("Ctrl+Shift+E")
        execute_all_action.triggered.connect(self._execute_all)
        edit_menu.addAction(execute_all_action)

        # View menu
        view_menu = menubar.addMenu("View")

        frame_all_action = QAction("Frame All", self)
        frame_all_action.setShortcut("F")
        frame_all_action.triggered.connect(self._network_view.frame_selection)
        view_menu.addAction(frame_all_action)

        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("H")
        reset_zoom_action.triggered.connect(self._network_view.reset_zoom)
        view_menu.addAction(reset_zoom_action)

    def _setup_connections(self):
        """Setup signal connections."""
        # Connect network view selection to parameters pane
        self._network_view.node_selected.connect(self._on_node_selected)

        # Connect print output signal
        from ..nodes.utils import print_output_signal
        print_output_signal.connect(self._on_print_output)

    def _register_default_nodes(self):
        """Register default node types."""
        from ..nodes.operators.math_nodes import (
            AddNode, SubtractNode, MultiplyNode, DivideNode
        )
        from ..nodes.operators.convert_node import ConvertNode
        from ..nodes.utils import PrintNode, DisplayNode
        from ..nodes.base import (
            IntVariable, FloatVariable, StringVariable, BoolVariable
        )

        # Math nodes
        NodeRegistry.register(AddNode)
        NodeRegistry.register(SubtractNode)
        NodeRegistry.register(MultiplyNode)
        NodeRegistry.register(DivideNode)

        # Conversion nodes
        NodeRegistry.register(ConvertNode)

        # Utility nodes
        NodeRegistry.register(PrintNode)
        NodeRegistry.register(DisplayNode)

        # Variable nodes
        NodeRegistry.register(IntVariable)
        NodeRegistry.register(FloatVariable)
        NodeRegistry.register(StringVariable)
        NodeRegistry.register(BoolVariable)

    def _on_node_selected(self, node):
        """Handle node selection."""
        self._parameters_pane.set_node(node)

    def _on_print_output(self, node_name: str, text: str):
        """Handle print output from nodes."""
        self._output_pane.append_output(node_name, text)

    def new_network(self):
        """Create a new network."""
        self._network_model = NetworkModel("Untitled")
        self._current_file = None

        # Create scene
        scene = NetworkScene(self._network_model)
        self._network_view.set_scene(scene)

        # Clear output
        self._output_pane.clear()

        # Update title
        self._update_title()

        # Log
        self._output_pane.append_info("New network created")

    def open_file(self):
        """Open a network file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Network",
            "",
            "Node Graph Files (*.json);;All Files (*)"
        )

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """Load network from file."""
        try:
            self._network_model = JSONSerializer.load(file_path)
            self._current_file = file_path

            # Create scene
            scene = NetworkScene(self._network_model)
            self._network_view.set_scene(scene)

            # Update title
            self._update_title()

            # Log
            self._output_pane.append_info(f"Opened: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def save_file(self):
        """Save the current network."""
        if self._current_file:
            self._save_to_file(self._current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        """Save the network to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Network",
            "",
            "Node Graph Files (*.json);;All Files (*)"
        )

        if file_path:
            if not file_path.endswith(".json"):
                file_path += ".json"
            self._save_to_file(file_path)

    def _save_to_file(self, file_path: str):
        """Save network to file."""
        try:
            JSONSerializer.save(self._network_model, file_path)
            self._current_file = file_path

            # Update title
            self._update_title()

            # Log
            self._output_pane.append_info(f"Saved: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def _update_title(self):
        """Update window title."""
        name = self._network_model.name if self._network_model else "Untitled"
        if self._current_file:
            name = self._current_file.split("/")[-1]
        self.setWindowTitle(f"Node Graph Editor - {name}")

    def _delete_selected(self):
        """Delete selected items."""
        scene = self._network_view.scene()
        if hasattr(scene, 'delete_selected'):
            scene.delete_selected()

    def _execute_all(self):
        """Execute all nodes in the network."""
        if not self._network_model:
            return

        try:
            # Get execution order
            nodes = self._network_model.get_execution_order()

            # Execute each node
            for node in nodes:
                node.cook()

            # Log
            self._output_pane.append_info(f"Executed {len(nodes)} nodes")

            # Update parameters pane
            self._parameters_pane.refresh()

        except Exception as e:
            self._output_pane.append_error(f"Execution error: {e}")

    def _restore_settings(self):
        """Restore window settings."""
        settings = QSettings("NodeGraph", "Editor")

        # Restore geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        """Handle window close."""
        # Save settings
        settings = QSettings("NodeGraph", "Editor")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

        event.accept()
