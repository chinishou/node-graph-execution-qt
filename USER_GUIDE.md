# User Guide

Node Graph Execution Qt - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Interface](#user-interface)
4. [Creating Networks](#creating-networks)
5. [Working with Nodes](#working-with-nodes)
6. [Working with Connections](#working-with-connections)
7. [Parameters and Properties](#parameters-and-properties)
8. [Subnet Nodes](#subnet-nodes)
9. [Saving and Loading](#saving-and-loading)
10. [Keyboard Shortcuts](#keyboard-shortcuts)
11. [Tips and Tricks](#tips-and-tricks)

---

## Introduction

Node Graph Execution Qt is a visual programming environment inspired by Houdini's node-based workflow. It allows you to create programs by connecting nodes together, making it easy to:

- Build data processing pipelines visually
- Prototype ideas quickly
- Reuse components across projects
- Understand complex logic at a glance

---

## Getting Started

### Installation

```bash
# Install from source
git clone https://github.com/chinishou/node-graph-execution-qt.git
cd node-graph-execution-qt
pip install -e ".[qt]"
```

### Launching the Editor

```bash
python run_editor.py
```

### First Steps

1. The editor opens with an empty network
2. Press **Tab** or **Right-click** to open the node palette
3. Select a node type (e.g., **Math > Add**)
4. The node appears in the network
5. Connect nodes by dragging from output (right side) to input (left side)
6. Double-click a node to execute it

---

## User Interface

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│  File  Edit  View  Help                          [Menu Bar] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────┬──────────────────┐ │
│  │                                     │  Parameters      │ │
│  │                                     │  Pane            │ │
│  │                                     │  ┌──────────────┐│ │
│  │     Network Editor                  │  │ Node: Add    ││ │
│  │                                     │  ├──────────────┤│ │
│  │     [Node Graph Area]               │  │ Input Defs   ││ │
│  │                                     │  │ a: 0.0       ││ │
│  │                                     │  │ b: 0.0       ││ │
│  │                                     │  ├──────────────┤│ │
│  │                                     │  │ Parameters   ││ │
│  │                                     │  │ type: float  ││ │
│  │                                     │  └──────────────┘│ │
│  │                                     │  [Execute]       │ │
│  └─────────────────────────────────────┴──────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Output                                                │  │
│  │  Print: 5.0                                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Interface Components

1. **Menu Bar**: File operations, execution, view controls
2. **Network Editor**: Visual canvas for placing and connecting nodes
3. **Parameters Pane**: Edit properties of selected node
4. **Output Pane**: View results from Print nodes

---

## Creating Networks

### Example: Simple Math Calculation

**Goal**: Calculate `(5 + 3) * 2`

**Steps**:

1. **Create value nodes**:
   - Press Tab → Variables → Float
   - Create three Float nodes
   - Set values: 5, 3, and 2

2. **Create operator nodes**:
   - Press Tab → Math → Add
   - Press Tab → Math → Multiply

3. **Connect nodes**:
   ```
   Float(5) ──┐
              ├──> Add ──> Multiply ──> Print
   Float(3) ──┘              ↑
                             │
   Float(2) ─────────────────┘
   ```

4. **Create output**:
   - Press Tab → Utils → Print
   - Connect Multiply's result to Print's input

5. **Execute**:
   - Double-click Print node
   - See result "16.0" in Output pane

---

## Working with Nodes

### Creating Nodes

**Method 1: Tab Key**
- Press **Tab** anywhere in the network
- Type to filter (e.g., "add" for AddNode)
- Click to create

**Method 2: Right-Click Menu**
- Right-click on empty space
- Navigate category menu
- Click node type

### Node Categories

- **Math**: Add, Subtract, Multiply, Divide
- **Operators**: Convert (type conversion)
- **Utils**: Print, Display
- **Variables**: Int, Float, String, Bool
- **Subnet**: SubnetNode, SubnetInputNode, SubnetOutputNode

### Node Anatomy

```
┌─────────────────────────────────┐
│          Node Name              │  ← Header
├─────────────────────────────────┤
│ ○ input1                        │  ← Input connectors (left)
│ ○ input2                        │
│                        output ○ │  ← Output connectors (right)
└─────────────────────────────────┘
```

**Color Coding**:
- Blue ● : int
- Orange ● : float
- Green ● : str
- Red ● : bool
- Gray ● : any (dynamic type)

### Selecting Nodes

- **Single selection**: Click on node
- **Multi-selection**: Ctrl+Click additional nodes
- **Box selection**: Press **F** and drag to select area

### Moving Nodes

- **Drag**: Click and drag node body
- **Multi-move**: Select multiple nodes, drag any selected node

### Deleting Nodes

- Select node(s)
- Press **Delete** key
- Connections are automatically removed

### Executing Nodes

**Method 1: Double-Click**
- Double-click node to execute it and all dependencies

**Method 2: Context Menu**
- Right-click node → Execute

**Method 3: Execute All**
- Menu: Edit → Execute All
- Executes entire network in dependency order

---

## Working with Connections

### Creating Connections

**Method 1: Drag from Output to Input**
1. Click and hold on output connector (right side)
2. Drag to input connector (left side)
3. Release to create connection

**Method 2: Drag from Input to Output**
1. Click and hold on input connector
2. Drag to output connector
3. Release to create connection

### Connection Rules

- ✓ Output → Input: Allowed
- ✓ Same type (int → int): Allowed
- ✓ Any type (`any`): Compatible with everything
- ✗ Output → Output: Not allowed
- ✗ Input → Input: Not allowed
- ✗ Input with existing connection: Old connection replaced

### Deleting Connections

**Method 1: Select and Delete**
1. Click on connection line
2. Press **Delete**

**Method 2: Disconnect Input**
- Create new connection to same input
- Old connection is automatically removed

### Connection Visualization

Connections use Bezier curves:
- Color matches source connector type
- Dashed line while dragging
- Solid line when connected

---

## Parameters and Properties

### Parameters Pane

When you select a node, the Parameters Pane shows:

1. **Input Defaults**: Default values for unconnected inputs
2. **Parameters**: Node-specific settings
3. **Outputs**: Read-only output values (after execution)

### Editing Input Defaults

**For Disconnected Inputs**:
- Type value directly in field
- Values are automatically converted to correct type

**Example**:
```
Input Defaults:
┌──────────────┐
│ a: [5.0   ] │  ← Float input (orange ●)
│ b: [3     ] │  ← Can type "3", auto-converts to 3.0
└──────────────┘
```

**For Connected Inputs**:
- Field is grayed out and disabled
- Value comes from connected node

### Parameter Types

Different input types have different widgets:

- **Float/Int**: Spinbox (type number)
- **String**: Text field
- **Bool**: Checkbox
- **Dropdown**: Combo box (e.g., type selection)

### Type Conversion

The system automatically converts string inputs to appropriate types:

| Input   | Type    | Result  |
|---------|---------|---------|
| "3"     | int     | 3       |
| "3.14"  | float   | 3.14    |
| "3"     | any     | 3 (int) |
| "3.14"  | any     | 3.14 (float) |
| "text"  | any     | "text" (string) |

---

## Subnet Nodes

### What are Subnets?

Subnets allow you to encapsulate a group of nodes into a single reusable node.

**Benefits**:
- Organize complex networks
- Create reusable components
- Hide implementation details
- Recursive nesting supported

### Creating a Subnet

1. Create **SubnetNode**:
   - Tab → Subnet → SubnetNode

2. **Double-click** SubnetNode to enter it

3. Inside the subnet, create nodes:
   - **SubnetInputNode**: Creates input on parent subnet
   - **SubnetOutputNode**: Creates output on parent subnet
   - **Regular nodes**: Internal logic

4. **Example** (Add subnet):
   ```
   Inside "AddTwo" subnet:

   SubnetInput(a) ──> Add <── Float(2)
                       │
                       v
              SubnetOutput(result)
   ```

5. Return to parent network:
   - Use breadcrumb navigation
   - Or close subnet view

6. The SubnetNode now has connectors:
   ```
   AddTwo:
   ○ a (input)
                result ○ (output)
   ```

### Subnet I/O Nodes

**SubnetInputNode**:
- Appears as OUTPUT connector externally
- Passes values from parent into subnet

**SubnetOutputNode**:
- Appears as INPUT connector externally
- Passes values from subnet to parent

**Parameters**:
- `connector_name`: Name of external connector
- `data_type`: Type of connector
- `default_value`: Default if not connected

### Recursive Type Resolution

Subnets can chain together:

```
Float(1) → SubnetA(convert to int) → SubnetB(use int) → Print
```

The type system automatically resolves through the chain:
- SubnetB's internal input sees `int` type
- Even though it's connected to SubnetA's output
- Which internally converts from float to int

---

## Saving and Loading

### Saving Networks

**Menu: File → Save**
- Saves to current file
- If no file, prompts for filename

**Menu: File → Save As**
- Always prompts for filename
- Useful for creating variations

**File Format**: JSON (`.json`)

### Loading Networks

**Menu: File → Open**
- Browse for `.json` file
- Replaces current network

### What is Saved?

- All nodes (type, name, position)
- All connections
- All parameter values
- All input default values
- Subnet internal networks
- Network name

### Example JSON Structure

```json
{
  "version": "1.0",
  "name": "MyNetwork",
  "nodes": {
    "uuid-123": {
      "node_type": "AddNode",
      "name": "Add",
      "position": [100, 200],
      "parameters": {
        "type": "float"
      },
      "inputs": {
        "a": {"default_value": 5.0},
        "b": {"default_value": 3.0}
      }
    }
  },
  "connections": [...]
}
```

---

## Keyboard Shortcuts

| Shortcut          | Action                           |
|-------------------|----------------------------------|
| **Tab**           | Open node creation menu          |
| **Delete**        | Delete selected nodes/connections|
| **F**             | Frame selected (box select mode) |
| **H**             | Home view (reset zoom/pan)       |
| **Ctrl+S**        | Save network                     |
| **Ctrl+O**        | Open network                     |
| **Ctrl+N**        | New network                      |
| **Middle Mouse**  | Pan view (drag)                  |
| **Scroll Wheel**  | Zoom in/out                      |
| **Ctrl+Z**        | Undo (future)                    |
| **Ctrl+Y**        | Redo (future)                    |

---

## Tips and Tricks

### Organizing Your Network

**1. Use Descriptive Names**
- Select node
- Edit name in Parameters Pane
- Example: "Add" → "AddSpeed", "CalculateTotal", etc.

**2. Horizontal Layout**
- Flow left-to-right (like Houdini)
- Inputs on left, outputs on right
- Makes data flow obvious

**3. Group Related Nodes**
- Keep related nodes close together
- Use subnets for complex groups

**4. Color Coding**
- Pay attention to connector colors
- Mismatched types may indicate errors

### Performance

**Large Networks (100+ nodes)**:
- Use subnets to break into smaller pieces
- Only execute what you need
- Avoid unnecessary connections

### Debugging

**Check Execution**:
1. Add Print nodes at key points
2. Execute and check Output pane
3. Verify intermediate values

**Check Types**:
- Look at connector colors
- Ensure types match or use `any`
- Use ConvertNode for explicit conversion

**Check Connections**:
- Click node to see highlighted connections
- Verify data flow direction

### Common Patterns

**1. Constants**:
```
Float(value) → [use in multiple places]
```
Create variable nodes for reusable values.

**2. Type Conversion**:
```
Float(3.14) → Convert(to int) → Print
```
Use ConvertNode to change types explicitly.

**3. Multi-Input Operations**:
```
Value1 ──┐
Value2 ──┼──> Add ──> Result
Value3 ──┘
```
Some nodes accept multiple inputs.

**4. Subnet as Function**:
```
CreateSubnet("Multiply By 10"):
  Input(x) → Multiply(x * 10) → Output(result)

Use it:
  Float(5) → MultiplyBy10 → Print
  Result: 50.0
```

### Troubleshooting

**Problem**: Node palette doesn't appear
- **Solution**: Click in network area first (to focus)
- Try right-click instead of Tab

**Problem**: Can't connect two nodes
- **Solution**: Check connector types (colors)
- Ensure output → input direction
- Use `any` type for flexibility

**Problem**: Execution doesn't update output
- **Solution**: Check if node is connected
- Verify input values in Parameters Pane
- Try double-clicking node again

**Problem**: Type error (e.g., "can't add float and str")
- **Solution**: Check Input Defaults
- String values should auto-convert
- Try using ConvertNode explicitly

**Problem**: Subnet doesn't have connectors
- **Solution**: Add SubnetInputNode/SubnetOutputNode inside
- Ensure connector names are unique
- Call `sync_io_nodes()` if creating programmatically

---

## Advanced Features

### Python Nodes (Advanced)

PythonNode allows custom Python code:

1. Create PythonNode
2. Edit `code` parameter
3. Write Python function:
   ```python
   def compute(inputs):
       a = inputs.get("input", 0)
       return {"output": a * 2}
   ```

### Network Execution Order

Execution uses topological sorting:
1. Evaluates dependencies first
2. Caches results (nodes only execute once)
3. Pull-based (lazy evaluation)

### Custom Nodes (Developers)

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for creating custom node types.

---

## Getting Help

### Resources

- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Examples**: `examples/` directory
- **Tests**: `tests/` directory (see test code for usage)

### Support

- **Issues**: [GitHub Issues](https://github.com/chinishou/node-graph-execution-qt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/chinishou/node-graph-execution-qt/discussions)

---

## Glossary

- **Node**: A processing unit with inputs, outputs, and logic
- **Connector**: Input or output port on a node
- **Connection**: Link between an output and input connector
- **Parameter**: Node configuration setting
- **Network**: Graph of connected nodes
- **Subnet**: Encapsulated subgraph as a reusable node
- **Cook**: Execute a node (Houdini terminology)
- **Dirty**: Node needs re-execution (data has changed)

---

## Next Steps

1. **Try the Examples**:
   - Run `python examples/basic_network.py`
   - Study `examples/custom_node.py`

2. **Build Your First Network**:
   - Start with simple math operations
   - Experiment with subnets
   - Try saving and loading

3. **Learn Advanced Topics**:
   - Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
   - Create custom nodes
   - Explore the API

Happy node graphing! 🎨
