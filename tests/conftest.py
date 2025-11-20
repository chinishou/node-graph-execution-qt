"""
Pytest configuration for node-graph-execution-qt tests.
"""
import os
import sys

# Set Qt platform to offscreen for headless testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"
