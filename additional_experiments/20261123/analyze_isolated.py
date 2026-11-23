"""Run the frozen analysis with a local import path under Python -I."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / 'analyze.py'), run_name='__main__')
