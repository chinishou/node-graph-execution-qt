# Node Graph Execution Qt - 架构规划

## 项目概述

基于 PySide6/PyQt6 实现的 Houdini 风格节点式编程框架，支持可视化编程和代码复用。

### 核心目标
- 提供节点式的 Qt Designer 替代方案
- Junior 开发者：通过节点工具快速理解和修改
- Senior 开发者：专注底层代码优化
- 最大化代码（节点）重复使用

### 技术栈
- **UI框架**: PySide6/PyQt6 (QtPy兼容层)
- **Python**: 3.8+
- **序列化**: JSON
- **未来分离**: node-graph-core (业务逻辑核心)

---

## 核心架构设计

### 三层架构（参考 QtNodes）

```
┌─────────────────────────────────────────────────┐
│         Application Layer (UI)                  │
│  - NetworkEditor (主编辑器)                      │
│  - ParametersPane (属性面板)                     │
│  - NodePalette (节点选板)                        │
└─────────────────────────────────────────────────┘
                      ↓↑
┌─────────────────────────────────────────────────┐
│         View Layer (Qt Graphics)                │
│  - NetworkView (QGraphicsView)                  │
│  - NodeGraphicsItem (节点图形项)                 │
│  - ConnectorGraphicsItem (连接线)                │
└─────────────────────────────────────────────────┘
                      ↓↑
┌─────────────────────────────────────────────────┐
│         Model Layer (Core Logic)                │
│  - NetworkModel (图数据模型)                     │
│  - NodeModel (节点数据)                          │
│  - ParameterModel (参数数据)                     │
│  - ConnectorModel (连接数据)                     │
└─────────────────────────────────────────────────┘
                      ↓↑
┌─────────────────────────────────────────────────┐
│    Future: node-graph-core (业务逻辑分离)        │
│  - 执行引擎                                      │
│  - 数据流评估                                    │
│  - Python代码生成                                │
└─────────────────────────────────────────────────┘
```

### 解耦策略

**Model-View 完全分离**
- Model 层不依赖任何 Qt Widgets
- Model 可以 headless 运行（CLI、测试）
- View 层仅负责可视化表现

**插件化接口**
- 节点注册系统：`NodeRegistry`
- 参数类型系统：`ParameterTypeRegistry`
- 执行引擎接口：`ExecutionEngine` (未来分离到 core)

---

## 目录结构

```
node-graph-execution-qt/
├── nodegraph/                    # 主包
│   ├── __init__.py
│   ├── core/                     # 核心模型层（未来迁移到 node-graph-core）
│   │   ├── __init__.py
│   │   ├── models/               # 数据模型
│   │   │   ├── network_model.py
│   │   │   ├── node_model.py
│   │   │   ├── parameter_model.py
│   │   │   └── connector_model.py
│   │   ├── registry/             # 注册系统
│   │   │   ├── node_registry.py
│   │   │   └── parameter_registry.py
│   │   ├── serialization/        # 序列化
│   │   │   ├── json_serializer.py
│   │   │   └── python_exporter.py
│   │   └── execution/            # 执行引擎（占位，未来分离）
│   │       ├── executor.py
│   │       └── evaluator.py
│   │
│   ├── views/                    # 视图层
│   │   ├── __init__.py
│   │   ├── network/              # 网络视图
│   │   │   ├── network_view.py
│   │   │   ├── network_scene.py
│   │   │   └── layout_manager.py
│   │   ├── nodes/                # 节点图形项
│   │   │   ├── base_node_item.py
│   │   │   ├── python_node_item.py
│   │   │   └── subnet_node_item.py
│   │   ├── connectors/           # 连接线
│   │   │   ├── connector_item.py
│   │   │   └── connector_painter.py
│   │   └── widgets/              # UI 小部件
│   │       ├── parameters_pane.py
│   │       ├── node_palette.py
│   │       └── code_editor.py
│   │
│   ├── nodes/                    # 内置节点库
│   │   ├── __init__.py
│   │   ├── base/                 # 基础节点
│   │   │   ├── base_node.py
│   │   │   ├── python_node.py
│   │   │   └── subnet_node.py
│   │   ├── operators/            # 运算符节点
│   │   ├── logic/                # 逻辑节点
│   │   └── utils/                # 工具节点
│   │
│   ├── parameters/               # 参数类型系统
│   │   ├── __init__.py
│   │   ├── base_parameter.py
│   │   ├── int_parameter.py
│   │   ├── float_parameter.py
│   │   ├── string_parameter.py
│   │   └── color_parameter.py
│   │
│   └── utils/                    # 工具模块
│       ├── undo_stack.py
│       ├── logger.py
│       └── houdini_colors.py
│
├── examples/                     # 示例
│   ├── basic_network.py
│   ├── custom_node.py
│   └── subnet_example.py
│
├── tests/                        # 测试
│   ├── test_models/
│   ├── test_serialization/
│   └── test_nodes/
│
├── docs/                         # 文档
│   ├── getting_started.md
│   ├── custom_nodes.md
│   └── api_reference.md
│
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```

---

## 开发优先级

### Phase 1: 核心架构 (P0 - 最高优先级)

#### 1.1 数据模型层
- [x] `NetworkModel` - 图数据结构
- [x] `NodeModel` - 节点基类
- [x] `ParameterModel` - 参数系统
- [x] `ConnectorModel` - 连接模型

#### 1.2 节点系统
- [x] `BaseNode` - 基础节点抽象类
- [x] `PythonNode` - Python 代码节点
- [x] `SubnetNode` - 子图节点
- [x] `NodeRegistry` - 节点注册系统

#### 1.3 参数系统
- [x] `BaseParameter` - 参数基类
- [x] 基础类型：int, float, string, bool
- [x] `ParametersPane` - 属性面板 UI

#### 1.4 自定义节点 API
```python
from nodegraph.nodes.base import BaseNode
from nodegraph.parameters import FloatParameter, StringParameter

class MyCustomNode(BaseNode):
    """用户自定义节点示例"""

    category = "Custom"

    def __init__(self):
        super().__init__()

        # 定义输入
        self.add_input("input1", data_type="float")
        self.add_input("input2", data_type="float")

        # 定义输出
        self.add_output("result", data_type="float")

        # 定义参数
        self.add_parameter("multiplier", FloatParameter(default=1.0))

    def cook(self, **inputs):
        """执行节点逻辑"""
        val1 = inputs.get("input1", 0.0)
        val2 = inputs.get("input2", 0.0)
        multiplier = self.parameter("multiplier").value()

        result = (val1 + val2) * multiplier
        return {"result": result}
```

### Phase 2: 视图层 (P1)

#### 2.1 基础渲染
- [ ] `NetworkView` - QGraphicsView 主视图
- [ ] `NetworkScene` - QGraphicsScene
- [ ] `BaseNodeItem` - 节点图形项（Houdini 风格）
- [ ] `ConnectorItem` - 连接线渲染

#### 2.2 交互
- [ ] 拖拽创建节点
- [ ] 拖拽连接
- [ ] 节点选择/多选
- [ ] 平移/缩放画布

### Phase 3: 序列化与导出 (P1)

#### 3.1 JSON 序列化
```json
{
  "version": "1.0",
  "network": {
    "nodes": [
      {
        "id": "node_001",
        "type": "AddNode",
        "position": [100, 200],
        "parameters": {
          "value": 42
        }
      }
    ],
    "connectors": [
      {
        "from_node": "node_001",
        "from_output": "result",
        "to_node": "node_002",
        "to_input": "input1"
      }
    ]
  }
}
```

#### 3.2 Python 导出
```python
# 自动生成的 Python 代码
def generated_network():
    # Node: node_001 (AddNode)
    node_001_result = add_function(input1=10, input2=20)

    # Node: node_002 (MultiplyNode)
    node_002_result = multiply_function(
        input1=node_001_result,
        multiplier=2.0
    )

    return node_002_result
```

### Phase 4: 高级功能 (P2 - 次要优先级)

- [ ] 撤销/重做系统
- [ ] 水平布局优化
- [ ] 节点搜索/过滤
- [ ] 快捷键系统
- [ ] 主题/样式系统

---

## Houdini 风格命名规范

### 术语对照表

| 概念 | Houdini 术语 | 本项目命名 |
|------|-------------|-----------|
| 节点图 | Network | `Network` |
| 节点 | Node | `Node` |
| 输入/输出 | Connector | `Connector` / `Port` |
| 参数 | Parameter / Parm | `Parameter` |
| 子网络 | Subnet | `Subnet` |
| 执行 | Cook | `cook()` / `evaluate()` |
| 参数面板 | Parameters Pane | `ParametersPane` |

### 类命名约定
- Model 类: `XxxModel` (如 `NodeModel`)
- View 类: `XxxView` / `XxxItem` (如 `NetworkView`, `NodeGraphicsItem`)
- Widget 类: `XxxPane` / `XxxWidget` (如 `ParametersPane`)
- 节点类: `XxxNode` (如 `PythonNode`)

---

## 与 node-graph-core 的集成接口

### 接口定义（未来迁移）

```python
# 在 nodegraph/core/interfaces.py

class IExecutionEngine(ABC):
    """执行引擎接口 - 未来由 node-graph-core 实现"""

    @abstractmethod
    def evaluate_network(self, network_model: 'NetworkModel') -> dict:
        """评估整个网络"""
        pass

    @abstractmethod
    def cook_node(self, node_model: 'NodeModel') -> Any:
        """执行单个节点"""
        pass

class IPythonExporter(ABC):
    """Python 导出接口"""

    @abstractmethod
    def export_to_python(self, network_model: 'NetworkModel') -> str:
        """导出为 Python 代码"""
        pass
```

### 插件化加载

```python
# 未来加载 node-graph-core
from nodegraph.core.interfaces import IExecutionEngine

# 默认使用内置实现
engine = DefaultExecutionEngine()

# 或加载外部核心
try:
    from node_graph_core import AdvancedExecutionEngine
    engine = AdvancedExecutionEngine()
except ImportError:
    pass
```

---

## 技术细节

### 数据流模型

- **Pull-based evaluation** (懒惰求值，类似 Houdini)
- 节点只在需要时 cook
- 支持缓存和 dirty 标记

### 参数变化传播

```python
# 参数变化 -> 标记节点 dirty -> 触发重新 cook
parameter.value_changed.connect(node.mark_dirty)
node.dirty_changed.connect(network.propagate_dirty)
```

### 撤销/重做系统

- 使用 Qt 的 `QUndoStack`
- 所有操作封装为 `QUndoCommand`
- 支持宏命令（批量操作）

---

## 示例用例

### 用例 1: 节点式 Qt Designer

```python
# 创建 UI 布局节点
layout = VBoxLayoutNode()
button1 = PushButtonNode(text="Click Me")
label1 = LabelNode(text="Result")

# 连接信号
button1.output("clicked") >> label1.input("setText")
```

### 用例 2: 数据处理管道

```python
# 读取数据
data_source = CSVReaderNode(file_path="data.csv")

# 数据处理
filtered = FilterNode(condition="value > 100")
transformed = MapNode(function=lambda x: x * 2)

# 输出结果
output = CSVWriterNode(file_path="output.csv")

# 构建管道
data_source >> filtered >> transformed >> output
```

---

## 下一步行动

1. **创建项目基础结构**
   - 初始化 Python 包
   - 配置 requirements.txt
   - 设置 pytest

2. **实现核心 Model 层**
   - `NetworkModel`
   - `NodeModel`
   - `ParameterModel`

3. **实现基础节点**
   - `BaseNode`
   - `PythonNode`
   - 节点注册系统

4. **实现属性面板**
   - `ParametersPane` UI
   - 参数类型系统

5. **单元测试**
   - Model 层测试
   - 序列化测试

---

## 性能考虑

- 大规模网络（1000+ 节点）的渲染优化
- 延迟加载子图
- 连接线使用 QPainterPath 缓存
- 视口剔除（Viewport Culling）

---

## 扩展性设计

### 自定义节点包

用户可以创建独立的节点包：

```
my_custom_nodes/
├── __init__.py
├── nodes/
│   ├── my_node.py
│   └── another_node.py
└── package.json  # 节点包元数据
```

加载自定义包：

```python
from nodegraph import NodeRegistry

registry = NodeRegistry.instance()
registry.load_package("path/to/my_custom_nodes")
```

---

## 许可证

MIT License (建议)

---

## 参考资料

- QtNodes: https://github.com/paceholder/nodeeditor
- NodeGraphQt: https://github.com/jchanvfx/NodeGraphQt
- PyFlow: https://github.com/pedroCabrera/PyFlow
- Houdini Documentation: https://www.sidefx.com/docs/
