"""Run BeeLine with the demo parser (choices, input_dir, input_file).

From project root: python -m tests.run_demo
"""

import sys
from pathlib import Path

# Add src to path so beeline package can be imported
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from beeline import BeeLine

from tests.demo_parser import get_parser, demo_on_run

if __name__ == "__main__":
    demo = BeeLine(
        parser=get_parser(),
        formal_name="beeline_demo",
        on_run=demo_on_run,
    )
    demo.main_loop()
