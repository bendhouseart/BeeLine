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
from .inputs import DirPath, FilePath

import argparse
import sys
import io
from typing import Callable, Optional

# Optional: restrict to specific types, e.g. ["json", "csv"]
FILE_TYPES = None  # None = all files


class _StdoutToTerminal(io.TextIOBase):
    """Wraps stdout so writes are also sent to the BeeLine terminal widget."""

    def __init__(self, log_to_terminal, original_stdout):
        self._log = log_to_terminal
        self._original = original_stdout
        self._buffer = ""

    def write(self, s):
        self._original.write(s)
        if not s:
            return 0
        self._buffer += s
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._log(line)
        return len(s)

    def flush(self):
        if self._buffer:
            self._log(self._buffer)
            self._buffer = ""
        self._original.flush()


class BeeLine(toga.App):
    def __init__(
        self,
        parser: ArgumentParser,
        *,
        formal_name: str = "BeeLine",
        app_id: str = "org.openneuropet.beeline",
        on_run: Optional[Callable[["BeeLine", argparse.Namespace], None]] = None,
    ):
        self.parser = parser
        # Store parser actions before calling super().__init__()
        self.parser_actions = parser._actions
        # (dest, widget) for each argument - widget.value gives current value
        self.arg_widgets = []
        # Terminal output widget (set in startup)
        self.terminal_output = None
        self._on_run = on_run
        # Initialize the parent Toga App class with required parameters
        super().__init__(
            formal_name=formal_name,
            app_id=app_id,
            startup=self.startup,
        )

    def create_browse_handler(self, path_input, path_type_selection):
        """Create a browse handler that captures the specific widgets."""

        def on_browse(widget, **kwargs):
            # Create a task to handle the async dialog
            async def show_dialog():
                if path_type_selection is DirPath:
                    dialog = toga.SelectFolderDialog(
                        title="Choose a folder",
                        multiple_select=False,
                    )
                elif path_type_selection is FilePath:
                    dialog = toga.OpenFileDialog(
                        title="Choose a file",
                        file_types=FILE_TYPES,
                        multiple_select=False,
                    )
                else:
                    pass
                path = await self.main_window.dialog(dialog)
                if path is not None:
                    path_input.value = str(path)

            # Schedule the async task
            asyncio.create_task(show_dialog())

        return on_browse

    def collect_arguments(self):
        """Collect current values from all argument widgets into a dictionary."""
        return {dest: widget.value for dest, widget in self.arg_widgets}

    def parse_arguments(self) -> argparse.Namespace:
        """Build argv from current widget values and parse with the app's parser.

        Returns an argparse.Namespace with types applied (e.g. DirPath, FilePath).
        Raises if required args are missing or validation fails.
        """
        dest_to_action = {
            a.dest: a for a in self.parser_actions if a.dest != "help"
        }
        argv = []
        for dest, widget in self.arg_widgets:
            action = dest_to_action[dest]
            value = widget.value
            if value is None or (
                isinstance(value, str) and value.strip() == ""
            ):
                if not action.required:
                    continue
            option_strings = getattr(action, "option_strings", [])
            if option_strings:
                argv.append(option_strings[0])
            argv.append(str(value) if value is not None else "")
        return self.parser.parse_args(argv)

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
        """Parse args from the form, log to terminal, then call on_run callback if set."""
        try:
            args = self.parse_arguments()
        except (SystemExit, ValueError) as e:
            self.log_to_terminal(
                f"Validation error: {e}\n"
            )
            return

        # Log to terminal
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_to_terminal(f"[{timestamp}] Run pressed. Parsed arguments:")
        for k, v in vars(args).items():
            self.log_to_terminal(f"  {k}: {v!r}")
        self.log_to_terminal("")

        if self._on_run is not None:
            try:
                self._on_run(self, args)
            except Exception as e:
                self.log_to_terminal(f"Error in on_run callback: {e}\n")
                import traceback
                self.log_to_terminal(traceback.format_exc())
            return

        # No callback set - nothing to do
        self.log_to_terminal("No on_run callback set. Nothing to execute.\n")

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
            elif action.type is DirPath or action.type is FilePath:
                path_input = toga.TextInput(
                    placeholder="No file or folder selected",
                    style=Pack(flex=1),
                )
                browse_btn = toga.Button(
                    "Browse…",
                    on_press=self.create_browse_handler(
                        path_input, action.type
                    ),
                    style=Pack(margin_left=8),
                )
                self.arg_widgets.append((action.dest, path_input))
                path_row = toga.Box(
                    children=[label, path_input, browse_btn],
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

        # Route stdout to the terminal widget so any print() (e.g. from on_run callbacks)
        # appears in the GUI without callbacks needing to know about BeeLine.
        self._original_stdout = sys.stdout
        sys.stdout = _StdoutToTerminal(self.log_to_terminal, self._original_stdout)


def main(parser: Optional[ArgumentParser] = None):
    if parser is None:
        parser = ArgumentParser()
    return BeeLine(parser=parser)
