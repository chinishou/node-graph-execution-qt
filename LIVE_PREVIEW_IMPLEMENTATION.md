# Live Preview 功能實現文檔

本文檔詳細記錄了 Node Graph Execution 系統中 Live Preview 功能的設計與實現。

---

## 目錄

1. [功能概述](#功能概述)
2. [設計決策](#設計決策)
3. [架構說明](#架構說明)
4. [UI 節點系統](#ui-節點系統)
5. [Signal Trigger 機制](#signal-trigger-機制)
6. [Widget 生命週期管理](#widget-生命週期管理)
7. [動態輸入控制](#動態輸入控制)
8. [測試覆蓋](#測試覆蓋)
9. [使用示例](#使用示例)
10. [已知限制](#已知限制)
11. [未來改進](#未來改進)

---

## 功能概述

Live Preview 功能允許用戶通過節點圖構建 Qt UI，並在專用的預覽面板中即時查看和測試 UI。類似於 Qt Designer 的即時預覽功能，但完全通過節點系統驅動。

### 主要特性

- **即時預覽**: 通過節點構建的 UI 可在專用面板中顯示
- **手動刷新模式**: 用戶點擊 "Refresh" 按鈕來更新預覽
- **Signal Trigger 系統**: UI 事件可立即觸發節點執行（push-based）
- **Widget 節點**: 支援多種 Qt widgets (Button, Label, LineEdit, ComboBox)
- **Layout 節點**: 支援 VBox, HBox 佈局
- **Container 節點**: 支援 QWidget, QMainWindow 容器
- **動態輸入**: Layout 和 Container 節點可動態調整子元素數量

---

## 設計決策

### 1. 更新機制：手動刷新 vs 自動更新

**決策：採用手動刷新模式**

**原因：**
- 自動更新會增加系統負擔，每次節點變更都要重建 UI
- 手動刷新給予用戶控制權，可在完成編輯後才更新
- 簡化了 widget 生命週期管理
- 避免頻繁的 widget 創建和銷毀

### 2. Widget 生命週期：快取 vs 每次重建

**決策：每次重建，不使用快取**

**原因：**
- 避免 Qt C++ object 生命週期問題
- 在手動刷新模式下，重建成本可接受
- 代碼更簡單、更安全
- 避免 `Internal C++ object already deleted` 錯誤

**遇到的問題與解決：**
```python
# 錯誤的做法（會導致 crash）
def compute(self):
    if self._cached_widget is None:
        self._cached_widget = QLabel()
    return {"widget": self._cached_widget}

# 正確的做法
def compute(self):
    label = QLabel()  # 每次都創建新的
    return {"widget": label}
```

### 3. Signal 處理：統一採用 Push-based Trigger 模式

**決策：所有 UI Widgets 統一使用 Push-based Trigger**

- **所有 Widgets** (Label, Button, LineEdit, ComboBox): 使用 Event Trigger 模式
  - 立即執行連接的節點
  - Push-based 響應機制
  - 適合觸發操作和即時響應的場景

- **保留數據輸出**：Input Widgets 同時保留數據捕獲功能
  - LineEdit: `current_text` 數據輸出 + `text_changed` trigger 輸出
  - ComboBox: `selected_index`, `selected_text` 數據輸出 + `selection_changed` trigger 輸出
  - 兼顧數據讀取和即時響應兩種需求

---

## 架構說明

### 整體架構

```
┌─────────────────────────────────────────────┐
│           Main Window                       │
│  ┌──────────────┐  ┌──────────────────┐   │
│  │              │  │  Live Preview    │   │
│  │  Node Graph  │  │     Pane         │   │
│  │    Editor    │  │                  │   │
│  │              │  │  ┌────────────┐  │   │
│  │  ┌────┐      │  │  │   Built   │  │   │
│  │  │Node│      │  │  │     UI    │  │   │
│  │  └────┘      │  │  │  Preview  │  │   │
│  │    │         │  │  └────────────┘  │   │
│  │  ┌────┐      │  │                  │   │
│  │  │Node│      │  │  [  Refresh  ]   │   │
│  │  └────┘      │  │                  │   │
│  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────┘
```

### 數據流

```
User Action on Node Graph
        ↓
User clicks "Refresh"
        ↓
LivePreviewPane finds UIRootNode
        ↓
Execute UIRootNode (pull-based)
        ↓
UIRootNode pulls from connected nodes
        ↓
Each node creates fresh widgets
        ↓
Final widget tree returned
        ↓
Display in preview pane
```

### Signal Trigger 流程

```
User clicks Button in Preview
        ↓
Qt clicked signal fires
        ↓
ButtonNode._on_button_clicked()
        ↓
_trigger_connected_nodes()
        ↓
Find all nodes connected to 'clicked' output
        ↓
Execute each connected node immediately (push-based)
        ↓
Preview updates with results
```

---

## UI 節點系統

### 節點類型層級

```
BaseNode (nodegraph/nodes/base/base_node.py)
    │
    ├── Widget Nodes (nodegraph/nodes/ui/)
    │   ├── LabelNode        - QLabel 文字顯示
    │   ├── ButtonNode       - QPushButton 帶 trigger
    │   ├── LineEditNode     - QLineEdit 單行輸入
    │   └── ComboBoxNode     - QComboBox 下拉選擇
    │
    ├── Layout Nodes
    │   ├── VBoxLayoutNode   - 垂直佈局
    │   └── HBoxLayoutNode   - 水平佈局
    │
    ├── Container Nodes
    │   ├── QWidgetContainerNode  - 通用容器
    │   └── QMainWindowNode       - 主視窗
    │
    └── UIRootNode - 預覽系統入口點
```

### 核心節點詳解

#### 1. UIRootNode

**作用：** Live Preview 系統的入口點

**接口：**
- Input: `widget` (widget) - 根 widget
- Output: `widget` (widget) - 傳遞根 widget

**實現：**
```python
class UIRootNode(BaseNode):
    def compute(self, **inputs):
        widget = inputs.get("widget")
        return {"widget": widget}
```

**使用：**
LivePreviewPane 會尋找 network 中的 UIRootNode 並執行它來獲取完整的 UI 樹。

#### 2. LabelNode

**作用：** 創建可點擊的文字標籤

**參數：**
- `text` (str): 顯示的文字
- `alignment` (str): 對齊方式 (left/center/right)
- `on_click_message` (str): 點擊時顯示的訊息

**輸出：**
- `widget` (widget): ClickableLabel 實例
- `clicked` (any): Click trigger output

**Signal Trigger 實現：**
```python
class ClickableLabel(QLabel):
    """QLabel subclass that emits a clicked signal when clicked."""
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

def _on_label_clicked(self):
    # 1. 輸出訊息
    print(f"[Preview] {self.name}: {message}")

    # 2. 觸發連接的節點
    self._trigger_connected_nodes(True)
```

#### 3. ButtonNode

**作用：** 創建按鈕，支援 click trigger

**參數：**
- `text` (str): 按鈕文字
- `width` (int): 最小寬度
- `height` (int): 最小高度
- `on_click_message` (str): 點擊時顯示的訊息

**輸出：**
- `widget` (widget): QPushButton 實例
- `clicked` (any): Click trigger output

**Signal Trigger 實現：**
```python
def _on_button_clicked(self, checked=False):
    # 1. 輸出訊息
    print(f"[Preview] {self.name}: {message}")

    # 2. 觸發連接的節點
    self._trigger_connected_nodes(checked)

def _trigger_connected_nodes(self, signal_value):
    clicked_output = self.output("clicked")
    connections = clicked_output.connections()

    # 存儲 signal 值
    self._output_values["clicked"] = signal_value

    # 立即執行所有連接的節點
    for conn in connections:
        conn.node.execute()
```

#### 4. LineEditNode

**作用：** 單行文字輸入框，支援 text change trigger

**參數：**
- `text` (str): 預設文字
- `placeholder` (str): 佔位符文字
- `width` (int): 最小寬度
- `read_only` (bool): 是否唯讀

**輸出：**
- `widget` (widget): QLineEdit 實例
- `current_text` (str): 當前文字內容（數據輸出）
- `text_changed` (any): Text change trigger output

**Push-based Trigger 實現：**
```python
def __init__(self):
    self._current_text = ""

def compute(self, **inputs):
    line_edit = QLineEdit()
    line_edit.setText(self.parameter("text").value())
    line_edit.textChanged.connect(self._on_text_changed)

    return {
        "widget": line_edit,
        "current_text": self._current_text,
        "text_changed": None
    }

def _on_text_changed(self, text: str):
    self._current_text = text  # 記錄當前值
    self._trigger_connected_nodes(text)  # 觸發連接的節點

def _trigger_connected_nodes(self, signal_value):
    text_changed_output = self.output("text_changed")
    connections = text_changed_output.connections()
    self._output_values["text_changed"] = signal_value
    for conn in connections:
        conn.node.execute()
```

#### 5. ComboBoxNode

**作用：** 下拉選擇框，支援 selection change trigger

**參數：**
- `items` (str): 選項列表（逗號分隔）
- `current_index` (int): 預設選擇的索引
- `width` (int): 最小寬度

**輸出：**
- `widget` (widget): QComboBox 實例
- `selected_index` (int): 當前選擇的索引（數據輸出）
- `selected_text` (str): 當前選擇的文字（數據輸出）
- `selection_changed` (any): Selection change trigger output

**Push-based Trigger 實現：**
```python
def __init__(self):
    self._selected_index = -1  # -1 表示未初始化
    self._selected_text = ""

def compute(self, **inputs):
    combo_box = QComboBox()

    # 只在第一次初始化時使用參數值
    if self._selected_index == -1:
        current_index = self.parameter("current_index").value()
        self._selected_index = current_index
        self._selected_text = items[current_index]

    # 設置 widget 為儲存的選擇
    combo_box.setCurrentIndex(self._selected_index)

    # 連接 signal
    combo_box.currentIndexChanged.connect(self._on_selection_changed)

    return {
        "widget": combo_box,
        "selected_index": self._selected_index,
        "selected_text": self._selected_text,
        "selection_changed": None
    }

def _on_selection_changed(self, index: int, combo_box: QComboBox):
    self._selected_index = index
    self._selected_text = combo_box.currentText()
    self._trigger_connected_nodes(index)  # 觸發連接的節點

def _trigger_connected_nodes(self, signal_value):
    selection_changed_output = self.output("selection_changed")
    connections = selection_changed_output.connections()
    self._output_values["selection_changed"] = signal_value
    for conn in connections:
        conn.node.execute()
```

---

## Signal Trigger 機制

### 概念

Node Graph 系統本質上是 **pull-based** 的：
- 執行從 output 節點開始
- 向上游 pull 數據
- 數據從 upstream 流向 downstream

Qt Signals 本質上是 **push-based** 的：
- 事件從 source 發出
- 向下游 push 通知
- 從 event source 推向 handlers

### 問題

如何在 pull-based 系統中實現 push-based 的 signal 響應？

### 解決方案：Signal Trigger Output

**核心思想：** 當 Qt signal 觸發時，主動找到並執行連接的下游節點。

**實現步驟：**

1. **添加 trigger output**
   ```python
   self.add_output("clicked", data_type="any", label="Clicked")
   ```

2. **連接 Qt signal 到 handler**
   ```python
   button.clicked.connect(self._on_button_clicked)
   ```

3. **在 handler 中觸發節點執行**
   ```python
   def _on_button_clicked(self, checked=False):
       self._trigger_connected_nodes(checked)
   ```

4. **找到並執行連接的節點**
   ```python
   def _trigger_connected_nodes(self, signal_value):
       # 獲取 output connector
       clicked_output = self.output("clicked")

       # 獲取所有連接
       connections = clicked_output.connections()

       # 存儲 signal 值供下游讀取
       self._output_values["clicked"] = signal_value

       # 執行每個連接的節點
       for conn in connections:
           conn.node.execute()
   ```

### 優勢

- ✅ 保持 Qt 原生 signal/slot 行為
- ✅ 立即響應，無需等待 refresh
- ✅ 支援多個連接的節點
- ✅ Signal 參數可傳遞給下游節點
- ✅ 與 pull-based 系統兼容

### 適用場景

**所有 UI Widgets 都使用 Trigger 模式：**
- Label clicks - 點擊標籤觸發操作
- Button clicks - 按鈕點擊觸發操作
- LineEdit text changes - 文字輸入即時觸發
- ComboBox selection - 選擇改變即時觸發
- 任何需要立即響應的 UI 交互

**Input Widgets 同時提供數據輸出：**
- LineEdit: `current_text` 可供其他節點讀取
- ComboBox: `selected_index`, `selected_text` 可供其他節點讀取
- 兼顧即時響應和數據讀取兩種需求

---

## Widget 生命週期管理

### 問題：Qt C++ Object 生命週期

Qt widgets 由 C++ 對象支撐，Python 只持有引用。當 C++ 對象被刪除後，Python 引用變成懸空指針。

**錯誤示例：**
```python
# 第一次 refresh
widget = create_widget()
preview.set_widget(widget)

# 第二次 refresh
old_widget = preview.get_current_widget()
old_widget.deleteLater()  # C++ 對象標記為刪除

new_widget = create_widget()
preview.set_widget(new_widget)

# 第三次 refresh
old_widget.setText("...")  # CRASH: C++ object already deleted
```

### 解決方案：每次重建

**策略：**
- 每次 refresh 創建全新的 widget 樹
- 不快取 widget 實例
- 讓 Qt 的父子關係自動管理生命週期

**正確的清理流程：**
```python
def _clear_preview(self):
    """安全地清理預覽區域"""
    while self._preview_layout.count():
        item = self._preview_layout.takeAt(0)
        if item.widget():
            widget = item.widget()
            widget.setParent(None)  # 解除父子關係
            widget.deleteLater()    # 標記為待刪除
```

**節點實現：**
```python
def compute(self, **inputs):
    # 總是創建新的 widget
    label = QLabel()
    label.setText(self.parameter("text").value())
    return {"widget": label}
```

### 狀態保持

對於需要保持狀態的 widget（如 LineEdit, ComboBox），在節點中儲存狀態：

```python
class LineEditNode(BaseNode):
    def __init__(self):
        self._current_text = ""  # 在節點中保存狀態

    def compute(self, **inputs):
        line_edit = QLineEdit()
        # 從節點狀態恢復 widget 狀態
        line_edit.setText(self._current_text)
        # 連接 signal 更新節點狀態
        line_edit.textChanged.connect(self._on_text_changed)
        return {"widget": line_edit, "current_text": self._current_text}

    def _on_text_changed(self, text):
        self._current_text = text  # 更新節點狀態
```

---

## 動態輸入控制

### 需求

Layout 和 Container 節點需要可變數量的子元素輸入。

### 挑戰

Node 的 inputs 在 `setup()` 方法中定義，但需要根據參數動態創建。

### 解決方案：`_setup_` 參數模式

**BaseNode 的特殊處理：**
```python
# BaseNode.__init__
def __init__(self, **kwargs):
    # 提取 _setup_ 前綴的參數
    setup_params = {}
    for key in list(kwargs.keys()):
        if key.startswith('_setup_'):
            setup_params[key] = kwargs.pop(key)

    super().__init__(**kwargs)

    # 設置為實例屬性
    for key, value in setup_params.items():
        object.__setattr__(self, key, value)

    # 調用 setup()
    self.setup()
```

**Layout Node 實現：**
```python
class VBoxLayoutNode(BaseNode):
    def __init__(self, num_children: int = 5, **kwargs):
        # 通過 kwargs 傳遞 _setup_ 參數給 BaseNode
        super().__init__(
            name="VBox Layout",
            node_type="VBoxLayoutNode",
            _setup_num_children=num_children,  # 特殊參數
            **kwargs
        )

    def setup(self):
        # 此時 self._setup_num_children 已經可用
        if not hasattr(self, '_setup_num_children'):
            self._setup_num_children = 5  # 向後兼容

        # 創建參數
        self.add_parameter("num_children",
                          default_value=self._setup_num_children)

        # 根據參數創建動態數量的 inputs
        num_children = self.parameter("num_children").value()
        for i in range(1, num_children + 1):
            self.add_input(f"child{i}", data_type="widget")
```

**使用：**
```python
# 創建有 3 個子元素輸入的 layout
layout = VBoxLayoutNode(num_children=3)
```

---

## 測試覆蓋

### 測試結構

```
tests/test_ui_nodes.py (674 lines)
├── TestBasicUINodes (3 tests)
│   ├── UIRoot node creation
│   ├── Label node creation and execution
│   └── Button node creation and execution
│
├── TestDynamicInputControl (4 tests)
│   ├── Default children count
│   ├── Custom children count
│   ├── Large children count (10)
│   └── HBox dynamic children
│
├── TestConnectionsWithDynamicInputs (3 tests)
│   ├── Connect to dynamic inputs
│   ├── Partial connections
│   └── Connections beyond num_children
│
├── TestParameterChangeScenarios (2 tests)
│   ├── num_children parameter exists
│   └── Read num_children in compute
│
├── TestLayoutNodeComputation (3 tests)
│   ├── VBox layout computation
│   ├── HBox layout computation
│   └── Layout spacing and margins
│
├── TestContainerNodes (3 tests)
│   ├── QWidget container with vbox
│   ├── QWidget container with hbox
│   └── QMainWindow node
│
├── TestComplexUIHierarchy (2 tests)
│   ├── Nested layouts
│   └── UIRoot integration
│
├── TestWidgetLifecycle (2 tests)
│   ├── Multiple executions
│   └── Layout multiple executions
│
├── TestEdgeCases (3 tests)
│   ├── Empty layout
│   ├── Zero children
│   └── Large number of children (50)
│
└── TestSignalTriggers (8 tests)
    ├── Button has clicked output
    ├── Button click triggers connected node
    ├── LineEdit has current_text output
    ├── LineEdit initial text
    ├── LineEdit text change captured
    ├── ComboBox has selection outputs
    ├── ComboBox initial selection
    ├── ComboBox selection change captured
    ├── Signal data persists across refreshes
    └── Signal data can be connected to other nodes
```

### 測試覆蓋的關鍵場景

1. **節點創建和基本執行**
2. **動態輸入控制** - 參數化輸入數量
3. **連接處理** - 完整/部分連接
4. **Widget 生命週期** - 多次執行不 crash
5. **Signal 捕獲** - 數據正確記錄
6. **狀態保持** - refresh 後狀態正確
7. **邊界條件** - 0 children, 50+ children
8. **複雜層級** - 嵌套 layouts

### QApplication Fixture

```python
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for all tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
```

所有測試共享一個 QApplication 實例，避免重複創建。

---

## 使用示例

### 示例 1：簡單的 Label + Button UI

```
┌─────────────────┐
│ [Label Node]    │
│  text: "Hello"  │
└────────┬────────┘
         │ widget
         ▼
┌─────────────────┐
│ [VBox Layout]   │
│  num_children:2 │
└────────┬────────┘
         │ child1
         │
┌────────┴────────┐
│ [Button Node]   │
│ text: "Click Me"│
└────────┬────────┘
         │ widget
         │
         ▼ child2
┌─────────────────┐
│ [UIRoot Node]   │
└─────────────────┘
```

**預覽結果：**
```
┌──────────────┐
│   Hello      │
│              │
│ [Click Me]   │
└──────────────┘
```

### 示例 2：Button Trigger 機制

```
┌─────────────────┐
│ [Button Node]   │
│ text: "Execute" │
└────────┬────────┘
         │ clicked (trigger)
         ▼
┌─────────────────┐
│ [Label Node]    │
│ text: input     │◄─── 連接到 clicked
└─────────────────┘
```

**行為：**
1. 用戶在 preview 點擊 "Execute" 按鈕
2. clicked signal 觸發
3. ButtonNode 立即執行 LabelNode
4. Label 更新為新的文字

### 示例 3：LineEdit Trigger 機制

```
┌─────────────────┐
│ [LineEdit]      │
│ placeholder:    │
│ "Enter name"    │
└────────┬────────┘
         │ text_changed (trigger)
         ▼
┌─────────────────┐
│ [Label Node]    │
│ text: input     │◄─── 連接到 text_changed
└─────────────────┘
```

**行為：**
1. 用戶在 LineEdit 輸入文字
2. textChanged signal 觸發
3. LineEditNode 立即執行 LabelNode
4. Label 即時顯示用戶輸入的文字（無需 Refresh）

### 示例 4：ComboBox Trigger 機制

```
┌─────────────────┐
│ [ComboBox]      │
│ items: A,B,C    │
└────────┬────────┘
         │ selection_changed (trigger)
         ▼
┌─────────────────┐
│ [Label Node]    │
│ text: input     │◄─── 連接到 selection_changed
└─────────────────┘
```

**行為：**
1. 用戶在 ComboBox 選擇新選項
2. currentIndexChanged signal 觸發
3. ComboBoxNode 立即執行 LabelNode
4. Label 即時顯示選擇的選項（無需 Refresh）

---

## 已知限制

### 1. 手動刷新

**限制：** UI 不會自動更新，需要手動點擊 Refresh。

**影響：** 用戶修改節點參數後需要記得刷新。

**緩解：** Signal Trigger 機制提供了部分即時響應能力。

### 2. Widget 狀態在 Refresh 時重置

**限制：** 除了特別處理的 widgets（LineEdit, ComboBox），大部分 widgets 在 refresh 後會重置狀態。

**影響：** 如 scroll positions, focus state 等不會保留。

**緩解：** 對關鍵 widgets 實現狀態保存機制。

### 3. Signal Trigger 只支援直接連接的節點

**限制：** 只執行直接連接到 trigger output 的節點。

**影響：** 不會自動追蹤整條連接鏈。

**示例：**
```
[Button] --(clicked)--> [Node A] --(out)--> [Node B]
```
只會執行 Node A，Node B 需要 Node A 主動 pull。

### 4. 測試環境限制

**限制：** 測試中無法完全模擬 live preview 環境的 widget 互動。

**影響：** Signal trigger 機制在測試中只能部分驗證。

---

## 未來改進

### 1. 更多 Widget 類型

**計劃：**
- CheckBox / RadioButton
- Slider / SpinBox
- TextEdit (多行)
- ListView / TableView
- TabWidget / StackedWidget

### 2. 更多 Layout 選項

**計劃：**
- GridLayout
- FormLayout
- Layout 參數調整（stretch factors, alignment）

### 3. Style 支援

**計劃：**
- QSS (Qt Style Sheets) 支援
- 預設樣式主題
- 動態樣式修改

### 4. Signal Trigger 增強

**計劃：**
- 追蹤完整連接鏈並執行末端節點
- Signal 參數自動類型轉換
- 條件式 trigger（只在特定條件下執行）

### 5. Widget 狀態管理

**計劃：**
- 自動保存所有 widget 狀態
- Refresh 後恢復狀態
- 狀態序列化/反序列化

### 6. 即時預覽模式

**計劃：**
- 可選的自動刷新模式
- 智能刷新（只在關鍵變更時刷新）
- 預覽性能優化

### 7. 互動增強

**計劃：**
- 預覽中直接編輯 widget 參數
- 視覺化 widget 邊界和佈局資訊
- Debug 模式顯示 widget 樹結構

---

## 技術挑戰與解決方案

### 挑戰 1：Qt C++ Object 生命週期

**問題：**
```
Error: Internal C++ object (PySide6.QtWidgets.QLabel) already deleted
```

**原因：**
- 節點快取 widget 實例
- LivePreviewPane 調用 `deleteLater()` 刪除舊 widget
- 節點仍持有已刪除的 C++ 對象的 Python 引用

**解決方案：**
1. 移除所有 widget 快取
2. 每次 `compute()` 創建新的 widget
3. 依賴 Qt 父子關係自動管理生命週期

### 挑戰 2：動態輸入數量

**問題：** `setup()` 方法在 `__init__` 中調用，如何傳遞設置時參數？

**嘗試失敗的方案：**
```python
def __init__(self, num_children=5, **kwargs):
    self._setup_num_children = num_children  # 太晚了！
    super().__init__(**kwargs)  # setup() 在這裡被調用
```

**成功的方案：**
利用 BaseNode 的 `_setup_` 參數機制：
```python
def __init__(self, num_children=5, **kwargs):
    super().__init__(
        _setup_num_children=num_children,  # 通過 kwargs 傳遞
        **kwargs
    )
```

BaseNode 會提取 `_setup_` 前綴參數並在調用 `setup()` 前設為屬性。

### 挑戰 3：Pull-based 與 Push-based 的整合

**問題：** Node graph 是 pull-based，Qt signals 是 push-based。

**解決方案：** Signal Trigger 機制
- Qt signal 觸發時，主動找到下游節點
- 存儲 signal 值到 `_output_values`
- 立即調用 `node.execute()`
- 下游節點通過正常的 pull 機制獲取數據

**關鍵代碼：**
```python
def _trigger_connected_nodes(self, signal_value):
    clicked_output = self.output("clicked")
    connections = clicked_output.connections()

    # Bridge: 存儲 push 的值供 pull 使用
    self._output_values["clicked"] = signal_value

    # Push-based trigger
    for conn in connections:
        conn.node.execute()  # Pull-based execution
```

### 挑戰 4：ComboBox 選擇狀態保持

**問題：** 每次 refresh 創建新 widget 時，如何保持用戶的選擇？

**錯誤方案：**
```python
def compute(self):
    combo_box.setCurrentIndex(self.parameter("current_index").value())
    # 問題：每次都重置為參數值，覆蓋用戶選擇
```

**正確方案：**
```python
def __init__(self):
    self._selected_index = -1  # -1 = 未初始化

def compute(self):
    # 只在第一次初始化
    if self._selected_index == -1:
        self._selected_index = self.parameter("current_index").value()

    # 使用儲存的值
    combo_box.setCurrentIndex(self._selected_index)
```

---

## 相關文件

### 核心實現文件

- `nodegraph/views/widgets/live_preview_pane.py` - 預覽面板
- `nodegraph/views/main_window.py` - 主視窗整合
- `nodegraph/views/nodes/port_graphics_item.py` - Widget 類型顏色
- `nodegraph/core/data_types.py` - Widget 數據類型定義

### UI 節點實現

- `nodegraph/nodes/ui/ui_root_node.py` - 根節點
- `nodegraph/nodes/ui/label_node.py` - Label widget
- `nodegraph/nodes/ui/button_node.py` - Button widget with trigger
- `nodegraph/nodes/ui/input_widgets.py` - LineEdit, ComboBox
- `nodegraph/nodes/ui/layout_nodes.py` - VBox, HBox, Container, MainWindow

### 測試文件

- `tests/test_ui_nodes.py` - 完整測試套件 (33 tests)

---

## 版本歷史

### v1.0.0 - Initial Implementation

**日期：** 2025-11-24

**新增功能：**
- Live Preview 面板
- 手動刷新模式
- Widget 節點（Label, Button, LineEdit, ComboBox）
- Layout 節點（VBox, HBox）
- Container 節點（QWidget, QMainWindow）
- 動態輸入控制
- Signal Trigger 機制（ButtonNode）
- Signal 數據捕獲（LineEdit, ComboBox）
- 完整測試覆蓋（33 tests）

**修復的 Bug：**
- Qt C++ object 生命週期問題
- `_setup_num_children` AttributeError
- ComboBox 選擇狀態保持
- QApplication fixture 缺失

**已知問題：**
- 手動刷新模式（設計決策）
- Widget 狀態部分保留
- Signal trigger 只支援直接連接

---

## 貢獻者

本功能由 Claude (Anthropic) 設計和實現，在用戶的需求指導和反饋下完成。

特別感謝用戶提供的清晰需求和及時反饋，使得設計能夠不斷優化和改進。

---

## 參考資料

- [Qt Documentation](https://doc.qt.io/)
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- Node Graph Execution 項目其他文檔

---

*文檔最後更新：2025-11-24*
