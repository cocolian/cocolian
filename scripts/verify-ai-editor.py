"""Compatibility entry point for the current comment-driven AI editor acceptance test."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('verify-ai-revise.py')),run_name='__main__')
