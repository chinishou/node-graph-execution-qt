# Node Graph Execution Qt

基于 PySide6/PyQt6 的 Houdini 风格节点式编程框架。

## 特性

- **水平布局** - Houdini 风格的节点网络编辑器
- **属性面板** - 实时编辑节点参数
- **子图节点** - 支持模块化和封装
- **Python 节点** - 直接在节点中编写 Python 代码
- **自定义节点** - 简单的 API 让用户创建自己的节点
- **JSON 序列化** - 保存和加载节点网络
- **Python 导出** - 将节点网络导出为纯 Python 脚本
- **撤销/重做** - 完整的操作历史

## 使用场景

1. **节点式 Qt Designer** - 可视化构建 Qt UI
2. **快速原型开发** - Junior 开发者通过节点快速理解和修改
3. **代码复用** - 将常用功能封装为节点，最大化复用
4. **Senior 开发优化** - 专注于底层节点实现，提供高质量组件

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from nodegraph import NetworkEditor
from qtpy.QtWidgets import QApplication

app = QApplication([])
editor = NetworkEditor()
editor.show()
app.exec()
```

## 创建自定义节点

```python
from nodegraph.nodes.base import BaseNode
from nodegraph.parameters import FloatParameter

class AddNode(BaseNode):
    """加法节点"""

    category = "Math"

    def __init__(self):
        super().__init__()
        self.add_input("a", data_type="float")
        self.add_input("b", data_type="float")
        self.add_output("result", data_type="float")

    def cook(self, **inputs):
        a = inputs.get("a", 0.0)
        b = inputs.get("b", 0.0)
        return {"result": a + b}
```

## 架构

详见 [ARCHITECTURE.md](ARCHITECTURE.md)

## 开发状态

当前版本: **0.1.0-alpha**

- [x] 架构设计
- [ ] 核心 Model 层
- [ ] View 层实现
- [ ] 属性面板
- [ ] 自定义节点系统
- [ ] JSON 序列化
- [ ] Python 导出

## 许可证

MIT License

## 参考项目

- [QtNodes](https://github.com/paceholder/nodeeditor)
- [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt)
- [PyFlow](https://github.com/pedroCabrera/PyFlow)
- [Nodezator](https://github.com/IndieSmiths/nodezator)
