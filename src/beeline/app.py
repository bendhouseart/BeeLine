"""
Creates a GUI (BeeWare based) application from a Python argparse.NameSpace object.
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from argparse import ArgumentParser
import pathlib
import asyncio
from datetime import datetime


import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--choices", choices=["a", "b", "c"])
parser.add_argument("--input_dir", type=pathlib.Path)
parser.add_argument("--input_file", type=pathlib.Path)

# Optional: restrict to specific types, e.g. ["json", "csv"]
FILE_TYPES = None  # None = all files

# Ipsum lines for terminal stress test (every 0.5s for 30s)
IPSUM_LINES = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa.",
]


class BeeLine(toga.App):
    def __init__(self, parser: ArgumentParser):
        # Store parser actions before calling super().__init__()
        self.parser_actions = parser._actions
        # (dest, widget) for each argument - widget.value gives current value
        self.arg_widgets = []
        # Terminal output widget (set in startup)
        self.terminal_output = None
        # Initialize the parent Toga App class with required parameters
        super().__init__(
            formal_name="BeeLine",
            app_id="org.openneuropet.beeline",
            startup=self.startup,
        )

    def create_browse_handler(self, path_input, path_type_selection):
        """Create a browse handler that captures the specific widgets."""

        def on_browse(widget, **kwargs):
            # Create a task to handle the async dialog
            async def show_dialog():
                is_folder = path_type_selection.value == "Folder"
                if is_folder:
                    dialog = toga.SelectFolderDialog(
                        title="Choose a folder",
                        multiple_select=False,
                    )
                else:
                    dialog = toga.OpenFileDialog(
                        title="Choose a file",
                        file_types=FILE_TYPES,
                        multiple_select=False,
                    )
                path = await self.main_window.dialog(dialog)
                if path is not None:
                    path_input.value = str(path)

            # Schedule the async task
            asyncio.create_task(show_dialog())

        return on_browse

    def collect_arguments(self):
        """Collect current values from all argument widgets into a dictionary."""
        return {dest: widget.value for dest, widget in self.arg_widgets}

    def log_to_terminal(self, text):
        """Append text to the terminal output area and scroll to bottom."""
        if not self.terminal_output:
            return
        current = self.terminal_output.value or ""
        self.terminal_output.value = current + text + "\n"
        try:
            self.terminal_output.scroll_to_bottom()
        except (AttributeError, TypeError):
            pass

    def on_run(self, widget, **kwargs):
        """Collect arguments, log to terminal, stream ipsum for 30s, then show popup."""
        args_dict = self.collect_arguments()

        # Log to terminal
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_to_terminal(f"[{timestamp}] Run pressed. Arguments:")
        for k, v in args_dict.items():
            self.log_to_terminal(f"  {k}: {v!r}")
        self.log_to_terminal("")
        self.log_to_terminal("Streaming ipsum every 0.5s for 30s…")
        self.log_to_terminal("")

        async def ipsum_stream():
            """Log a line of ipsum every 0.5s for 30 seconds."""
            for i in range(60):  # 60 * 0.5s = 30s
                await asyncio.sleep(0.5)
                line = IPSUM_LINES[i % len(IPSUM_LINES)]
                ts = datetime.now().strftime("%H:%M:%S")
                self.log_to_terminal(f"  [{ts}] {line}")
            self.log_to_terminal("")
            self.log_to_terminal("Ipsum stream finished.")

        asyncio.create_task(ipsum_stream())

    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        children = []
        for action in self.parser_actions:
            # Skip the help action that argparse adds by default
            if action.dest == "help":
                continue

            # Format the label from action.dest (replace underscores with spaces, capitalize)
            label_text = action.dest.replace("_", " ").title()
            label = toga.Label(label_text, style=Pack(margin_right=10))

            # determine type of input from the arg parser and map it to the corresponding toga instance
            if action.choices:
                widget = toga.Selection(items=action.choices)
                self.arg_widgets.append((action.dest, widget))
                children.append(
                    toga.Box(
                        children=[label, widget],
                        style=Pack(direction=ROW, margin=10),
                    )
                )
            elif action.type is pathlib.Path:
                path_input = toga.TextInput(
                    placeholder="No file or folder selected",
                    style=Pack(flex=1),
                )
                path_type_selection = toga.Selection(
                    items=["File", "Folder"],
                    style=Pack(margin_left=8, width=100),
                )
                browse_btn = toga.Button(
                    "Browse…",
                    on_press=self.create_browse_handler(
                        path_input, path_type_selection
                    ),
                    style=Pack(margin_left=8),
                )
                self.arg_widgets.append((action.dest, path_input))
                path_row = toga.Box(
                    children=[label, path_input, path_type_selection, browse_btn],
                    style=Pack(direction=ROW, margin=10),
                )
                children.append(path_row)

        run_btn = toga.Button("Run", on_press=self.on_run, style=Pack(margin=10))
        children.append(run_btn)

        # Form on top: column, no flex so it sizes to content
        form_box = toga.Box(children=children, style=Pack(direction=COLUMN))

        # Terminal at bottom: column with flex=1 so it fills remaining space
        self.terminal_output = toga.MultilineTextInput(
            readonly=True,
            placeholder="Output will appear here when you run…",
            style=Pack(flex=1),
        )
        terminal_label = toga.Label("Output", style=Pack(margin=(10, 5)))
        terminal_box = toga.Box(
            children=[terminal_label, self.terminal_output],
            style=Pack(direction=COLUMN, flex=1, margin=5),
        )

        # Single column: form on top, terminal below (flexbox-like; terminal stays at bottom when resizing)
        main_content = toga.Box(
            children=[form_box, terminal_box],
            style=Pack(direction=COLUMN, flex=1),
        )

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_content
        self.main_window.show()


def main():
    return BeeLine(parser=parser)
