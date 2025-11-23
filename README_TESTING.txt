快速測試指南
============

這個項目需要先安裝依賴才能運行測試。

1. 安裝依賴：
   pip install -e ".[all]"

2. 運行測試：
   
   # 所有測試
   pytest tests/
   
   # 只運行 UI 測試
   pytest tests/ui/ -v
   
   # 運行特定測試
   pytest tests/ui/test_debug_signals.py -v

3. 如果遇到 "No module named 'nodegraph'" 錯誤：
   - 確保已經運行: pip install -e .
   - 或者: pip install -e ".[qt]"

4. 如果遇到 Qt 相關錯誤：
   - 安裝 Qt: pip install PySide6
   - 或者: pip install -e ".[qt]"

更多詳情請查看 RUNNING_TESTS.md
