"""Demo ArgumentParser for BeeLine (choices, paths). Packaged with the app for demo builds."""

import argparse
import asyncio
from datetime import datetime

from beeline.inputs import DirPath, FilePath

# Ipsum lines for terminal stress test (every 0.5s for 30s)
IPSUM_LINES = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa.",
]


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("positional", type=str, default="defaultpositionalvalue")
    parser.add_argument("--choices", choices=["a", "b", "c"])
    parser.add_argument("--input_dir", type=DirPath)
    parser.add_argument("--input_file", type=FilePath)
    parser.add_argument("--storetrue", action="store_true")
    parser.add_argument("--boolean", type=bool)
    parser.add_argument("--string", type=str)
    parser.add_argument("--int", type=int)
    parser.add_argument('--float', type=float)
    return parser


def demo_on_run(app, args):
    """Demo on_run callback that prints ipsum text to stdout (console).
    BeeLine captures stdout and shows it in the terminal widget when run from the GUI.
    """
    print("Streaming ipsum every 0.5s for 30s…")
    print()

    async def ipsum_stream():
        for i in range(60):  # 60 * 0.5s = 30s
            await asyncio.sleep(0.5)
            line = IPSUM_LINES[i % len(IPSUM_LINES)]
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"  [{ts}] {line}")
        print()
        print("Ipsum stream finished.")

    asyncio.create_task(ipsum_stream())
