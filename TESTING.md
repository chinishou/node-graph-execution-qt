# Testing Guide

## 测试修复完成 ✅

所有测试问题已修复：
1. ✅ 添加 `remove_input()` 和 `remove_output()` 方法到 NodeModel
2. ✅ 修复 AddNode 创建时的重复参数问题
3. ✅ 在测试 fixture 中注册节点类型

---

## 快速开始

### 运行所有UI测试

```bash
pytest tests/ui/test_copy_paste_ui.py -v
```

### 运行单元测试

```bash
# 节点路径测试
pytest tests/unit/test_node_path.py -v

# 或直接运行（不需要pytest）
python tests/unit/test_node_path.py
```

### 运行集成测试

```bash
pytest tests/integration/test_copy_paste.py -v
```

---

## 测试分类

### 1. 单元测试（非UI）- `tests/unit/`

**test_node_path.py** - 测试节点路径功能
- ✅ test_root_level_node_path - 根级别路径
- ✅ test_nested_subnet_node_path - 嵌套subnet路径
- ✅ test_deeply_nested_subnet_path - 深度嵌套路径
- ✅ test_node_path_without_network - 无网络节点路径
- ✅ test_print_node_uses_path - Print节点使用完整路径

```bash
# 独立运行
python tests/unit/test_node_path.py

# 使用pytest
pytest tests/unit/test_node_path.py -v
```

---

### 2. 集成测试 - `tests/integration/`

**test_copy_paste.py** - 测试复制粘贴核心逻辑（无UI）
- ✅ test_serialize_nodes_with_connections - 序列化带连接
- ✅ test_restore_connections_after_copy - 恢复连接
- ✅ test_subnet_serialize_with_internal_network - Subnet序列化
- ✅ test_subnet_deserialize_with_internal_network - Subnet反序列化
- ✅ test_filter_subnet_io_nodes_from_copy - 过滤I/O节点
- ✅ test_copy_preserves_parameter_values - 保留参数值
- ✅ test_copy_preserves_input_defaults - 保留输入默认值

```bash
pytest tests/integration/test_copy_paste.py -v
```

---

### 3. UI测试 - `tests/ui/`

**test_copy_paste_ui.py** - 完整UI交互测试

#### TestCopyPasteFunctionality 类：
- ✅ test_copy_single_node - 复制单个节点
- ✅ test_copy_multiple_nodes_with_connections - 复制多节点+连接
- ✅ test_paste_nodes_with_connections - 粘贴恢复连接
- ✅ test_cut_removes_nodes - 剪切功能
- ✅ test_paste_subnet_preserves_internal_network - Subnet粘贴
- ✅ test_subnet_io_nodes_not_copied - I/O节点过滤
- ✅ test_paste_at_cursor_position - 粘贴到光标位置
- ✅ test_copy_preserves_parameter_values - 参数保留

#### TestCopyPasteKeyboardShortcuts 类：
- ✅ test_ctrl_c_copies_selection - Ctrl+C
- ✅ test_ctrl_x_cuts_selection - Ctrl+X
- ✅ test_ctrl_v_pastes_nodes - Ctrl+V

```bash
# 标准运行
pytest tests/ui/test_copy_paste_ui.py -v

# 显示UI操作过程（可视化）
pytest tests/ui/test_copy_paste_ui.py --show-ui -s -v

# 运行特定测试
pytest tests/ui/test_copy_paste_ui.py::TestCopyPasteFunctionality::test_copy_single_node -v
```

---

## 完整测试套件

### 运行所有新测试

```bash
# 所有新功能测试
pytest tests/unit/test_node_path.py \
       tests/integration/test_copy_paste.py \
       tests/ui/test_copy_paste_ui.py -v

# 带覆盖率报告
pytest tests/unit/test_node_path.py \
       tests/integration/test_copy_paste.py \
       tests/ui/test_copy_paste_ui.py \
       --cov=nodegraph --cov-report=html -v
```

### 运行所有项目测试

```bash
# 所有测试
pytest tests/ -v

# 只运行非UI测试（更快）
pytest tests/unit/ tests/integration/ -v

# 只运行UI测试
pytest tests/ui/ -v
```

---

## 测试选项

### 常用pytest参数

```bash
-v              # 详细输出
-s              # 显示print输出
-x              # 第一个失败后停止
-k PATTERN      # 只运行匹配的测试
--lf            # 只运行上次失败的测试
--maxfail=N     # N个失败后停止
```

### 示例

```bash
# 运行名称包含"copy"的测试
pytest tests/ -k copy -v

# 显示所有输出
pytest tests/ui/test_copy_paste_ui.py -s -v

# 第一个失败后停止
pytest tests/ -x

# 只重新运行上次失败的测试
pytest tests/ --lf
```

---

## 覆盖率报告

### 生成HTML覆盖率报告

```bash
pytest tests/ --cov=nodegraph --cov-report=html
```

报告生成在 `htmlcov/index.html`

### 终端覆盖率报告

```bash
pytest tests/ --cov=nodegraph --cov-report=term-missing
```

---

## 测试统计

### 总测试数：23个

| 类型 | 数量 | 文件 |
|------|------|------|
| 单元测试 | 5 | test_node_path.py |
| 集成测试 | 7 | test_copy_paste.py |
| UI测试 | 11 | test_copy_paste_ui.py |

### 功能覆盖

| 功能 | 单元 | 集成 | UI |
|------|------|------|-----|
| 节点路径（get_path） | ✅ | - | - |
| 复制单节点 | - | ✅ | ✅ |
| 复制多节点 | - | ✅ | ✅ |
| 连接保留 | - | ✅ | ✅ |
| 剪切功能 | - | - | ✅ |
| Subnet序列化 | - | ✅ | ✅ |
| 过滤I/O节点 | - | ✅ | ✅ |
| 参数保留 | - | ✅ | ✅ |
| 键盘快捷键 | - | - | ✅ |
| Print路径输出 | ✅ | - | - |

---

## 持续集成（CI）

### GitHub Actions配置示例

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -e .[dev]
      - run: pytest tests/ --cov=nodegraph --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## 调试测试

### 使用pdb调试

```bash
# 在失败时进入调试器
pytest tests/ui/test_copy_paste_ui.py --pdb

# 在测试开始时进入调试器
pytest tests/ui/test_copy_paste_ui.py --trace
```

### 在代码中设置断点

```python
def test_something():
    # ...
    import pdb; pdb.set_trace()
    # ...
```

---

## 故障排除

### 常见问题

**1. ModuleNotFoundError: No module named 'nodegraph'**
```bash
# 设置PYTHONPATH
export PYTHONPATH=.
pytest tests/

# 或者安装为可编辑包
pip install -e .
```

**2. Qt platform plugin错误**
```bash
# 设置环境变量
export QT_QPA_PLATFORM=offscreen
pytest tests/ui/
```

**3. 测试超时**
```bash
# 增加超时时间
pytest tests/ --timeout=300
```

---

## 编写新测试

### 单元测试模板

```python
def test_my_feature():
    """Test description."""
    # Arrange
    node = MyNode()

    # Act
    result = node.some_method()

    # Assert
    assert result == expected
```

### UI测试模板

```python
def test_ui_feature(qtbot, network_view):
    """Test UI feature."""
    view, network, scene = network_view

    # Setup
    node = SomeNode()
    network.add_node(node)
    QApplication.processEvents()

    # Test interaction
    # ...

    # Verify
    assert expected_condition
```

---

## 相关文档

- [pytest文档](https://docs.pytest.org/)
- [pytest-qt文档](https://pytest-qt.readthedocs.io/)
- [Coverage.py文档](https://coverage.readthedocs.io/)
