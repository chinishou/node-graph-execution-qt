# Running UI Tests with Visible Windows

This guide explains how to run UI tests with actual visible Qt windows for debugging and demonstration purposes.

## Quick Start

### Using the Visual Test Runner Script

The easiest way to run tests with visible UI:

```bash
# Run all UI tests with visible windows
python run_ui_test_visual.py

# Run specific test file
python run_ui_test_visual.py tests/ui/test_recursion_bug.py

# Run specific test with verbose output
python run_ui_test_visual.py tests/ui/test_parameters_pane.py -v -s

# Run with custom delay (in milliseconds)
python run_ui_test_visual.py --delay 1000

# Run tests matching a keyword
python run_ui_test_visual.py -k "recursion"
```

### Using pytest Directly

You can also use pytest with the `--show-ui` flag:

```bash
# Show UI with default 500ms delay
pytest tests/ui/ --show-ui -s

# Show UI with custom delay
pytest tests/ui/ --show-ui --ui-delay=1000 -s

# Run specific test
pytest tests/ui/test_recursion_bug.py::test_recursion_bug_simple --show-ui -s -v
```

### Using Environment Variable

Set the `SHOW_UI` environment variable:

**Windows (PowerShell):**
```powershell
$env:SHOW_UI=1
pytest tests/ui/test_recursion_bug.py -s -v
```

**Windows (CMD):**
```cmd
set SHOW_UI=1
pytest tests/ui/test_recursion_bug.py -s -v
```

**Linux/Mac:**
```bash
SHOW_UI=1 pytest tests/ui/test_recursion_bug.py -s -v
```

## Command Line Options

### `--show-ui`
Shows the actual Qt windows during tests instead of running headless.

### `--ui-delay=<milliseconds>`
Sets the delay between UI operations when `--show-ui` is enabled.
- Default: 500ms
- Recommended for debugging: 1000-2000ms
- Faster runs: 100-300ms

### `-s` (--no-capture)
Don't capture stdout, allowing print statements to show in real-time.
**Highly recommended** when using `--show-ui` to see progress messages.

### `-v` (--verbose)
Verbose output showing each test name as it runs.

### `-k <keyword>`
Only run tests matching the keyword expression.

## Example Test Run Output

```bash
$ python run_ui_test_visual.py tests/ui/test_recursion_bug.py -s

Running: pytest tests/ui/test_recursion_bug.py --show-ui --ui-delay=500
UI delay: 500ms
------------------------------------------------------------

STEP 1: int->add
  Connected int->add
STEP 1: add->add_1
  Connected add->add_1

STEP 2: add->add_2
  Connected add->add_2 (add now has 2 outputs)
  Verified: add has 2 output connections

STEP 3: int->add_1 (potential recursion trigger)
  This should disconnect add->add_1 and create int->add_1
  Connected int->add_1 (old add->add_1 should be removed)
✓ SUCCESS: No recursion error!

Verifying final state:
✓ add_1 connected to int only
✓ add connected to add_2 only

Test completed! Keeping window open for inspection...
```

## Tips for Debugging

1. **Use `-s` flag** to see print statements in real-time
2. **Increase delay** for complex operations: `--delay 1000` or `--delay 2000`
3. **Run single tests** to focus on specific issues
4. **Add print statements** in your tests to track progress
5. **Window stays open** at the end of each test when using show_ui

## Headless Testing (Default)

By default, all tests run in headless mode using Qt's offscreen platform:

```bash
# Normal headless testing
pytest tests/ui/

# Headless with coverage
pytest tests/ui/ --cov=nodegraph --cov-report=html
```

This is faster and doesn't require a display, making it suitable for:
- CI/CD pipelines
- Automated testing
- Quick test runs

## Writing Tests with Visual Support

To add visual debugging support to your tests, use the `show_ui` and `ui_delay` fixtures:

```python
def test_my_ui_feature(qtbot, show_ui, ui_delay):
    """Test with optional visual debugging."""
    # Create UI components
    view = MyView()
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)

    # Helper function for conditional delays
    def maybe_wait(msg=""):
        if show_ui:
            if msg:
                print(f"  {msg}")
            qtbot.wait(ui_delay)
        else:
            qtbot.wait(10)
        QApplication.processEvents()

    # Perform operations with delays
    print("Step 1: Creating node")
    create_node()
    maybe_wait("Node created")

    print("Step 2: Connecting nodes")
    connect_nodes()
    maybe_wait("Nodes connected")

    # Final wait to inspect result
    if show_ui:
        print("\nTest completed! Window stays open...")
        qtbot.wait(ui_delay * 2)
```

## Troubleshooting

### Qt Platform Plugin Error
If you see `could not find the Qt platform plugin`, make sure:
1. PySide6 is properly installed
2. You're not in a headless environment (or use default headless mode)

### Tests Run Too Fast
Increase the delay: `--ui-delay=2000`

### Can't See Windows
Make sure you're using `-s` flag and `--show-ui` flag together

### Windows Don't Close
This is by design when using `--show-ui`. Each test keeps the window open briefly for inspection.
