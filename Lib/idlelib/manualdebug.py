# Lib/idlelib/manualdebug.py

"""
Currently: Simple Window for Manual Debug Feature - adapted from configdialog.py 

Note there is a Vertical Scrolling Window class in configdialog.py that may be useful.
Some of the current imports are not used but would be used with a Vertical Scrolling Window,
so they've been left in for convenience (we may use a scrolling window for a list of print statements).
"""

from tkinter import (Toplevel, TRUE, FALSE,
                     TOP, BOTTOM, RIGHT, LEFT,
                     BOTH, Y, NW, VERTICAL, X)
from tkinter.ttk import (Frame, Scrollbar, Button)
from idlelib import macosx
from tkinter import Text, END
from tkinter import StringVar, Entry, Label
from idlelib import manualdebug_helpers


class ManualDebug(Toplevel):
    """Opens the Print Statement Debugger window.

    This dialog lets users “apply” or “unapply” specific line numbers so that
    only print statements on those lines will actually appear in the Manual Debugger.
    All other prints in the user’s code become “invisible.”

    Args:
        editor_window  – the EditorWindow (or PyShellEditorWindow) instance that
                         owns .rpcclt (the RPC client) and .top (the real Tk Toplevel).
        title          – string for this window’s title (defaults to 'Print Statement Debugger').
        _htest         – bool (internal): if True, adjust geometry for IDLE’s htest harness.
        _utest         – bool (internal): if True, do not withdraw/deiconify (unittest mode).
    """

    def __init__(self, editor_window, title='', *, _htest=False, _utest=False):
        # Store the unittest flag (used by test suite to disable withdraw/deiconify)
        self._utest = _utest

        # Keep a reference to the EditorWindow so we can call self.editor.rpcclt
        self.editor = editor_window

        # Parent this Toplevel to editor_window.top (the real Tk window)
        Toplevel.__init__(self, self.editor.top)

        # If running under htest, IDLE’s test harness populates instance_dict
        if _htest:
            self.editor.instance_dict = {}

        # If not in unittest mode, start withdrawn to avoid flicker
        if not _utest:
            self.withdraw()

        # Title and position the window relative to the editor’s Toplevel
        self.title(title or 'Print Statement Debugger')
        x = self.editor.top.winfo_rootx() + 20
        y = self.editor.top.winfo_rooty() + (30 if not _htest else 150)
        self.geometry(f'+{x}+{y}')

        # Create all widgets (text area, scrollbar, entry, buttons, etc.)
        self.create_widgets()

        # Kick off the recurring poll that pulls messages out of manualdebug_helpers
        self._poll_messages()

        # Prevent user from resizing the Debugger window
        self.resizable(height=FALSE, width=FALSE)

        # When the user clicks the window’s [X], call self.destroy()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # If not in unittest mode, show the window now
        if not _utest:
            self.wm_deiconify()

    def create_widgets(self):
        """Create and place widgets for the dialog and the large output for prints."""
        self.frame = frame = Frame(self, padding=5)
        self.frame.grid(sticky="nwes")

        # The large, read-only Text area where intercepted prints appear in blue:
        self.output_text = Text(frame,
                                height=15,
                                width=60,
                                wrap="word",
                                state="disabled")
        self.output_text.grid(row=0, column=0, columnspan=2,
                              sticky="nwes", padx=4, pady=4)
        self.output_text.tag_configure("debug_blue", foreground="blue")

        # Vertical scrollbar for that text area:
        scrollbar = Scrollbar(frame, command=self.output_text.yview)
        scrollbar.grid(row=0, column=2, sticky="ns")
        self.output_text['yscrollcommand'] = scrollbar.set

        # The entry + Apply/Unapply buttons row:
        self.create_action_buttons().grid(row=1, column=0,
                                          columnspan=3, sticky="ew", pady=(8, 0))

        # Make the text area expand if user grows the window (though resizing is disabled):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def create_action_buttons(self):
        """Return a frame containing the entry plus Apply/Unapply buttons."""
        if macosx.isAquaTk():
            padding_args = {}
        else:
            padding_args = {'padding': (6, 3)}

        outer = Frame(self.frame, padding=2)

        # Entry field for comma-separated line numbers:
        self.line_var = getattr(self, "line_var", StringVar(self))
        line_frame = Frame(outer)
        Label(line_frame, text="Comma-separated debug lines:").pack(side=LEFT)
        self.line_entry = Entry(line_frame,
                                textvariable=self.line_var,
                                width=20)
        self.line_entry.pack(side=LEFT)
        line_frame.pack(side=TOP, pady=4)

        # “Apply” and “Unapply” buttons:
        buttons_frame = Frame(outer, padding=2)
        self.buttons = {}
        for txt, cmd in (
            ('Apply', self.apply),
            ('Unapply', self.cancel)
        ):
            self.buttons[txt] = Button(buttons_frame,
                                      text=txt,
                                      command=cmd,
                                      takefocus=FALSE,
                                      **padding_args)
            self.buttons[txt].pack(side=LEFT, padx=5)
        # Spacer above the buttons:
        Frame(outer, height=2, borderwidth=0).pack(side=TOP)
        buttons_frame.pack(side=BOTTOM)

        return outer

    def output_message(self, message):
        """Insert a message into the output text area (in blue)."""
        self.output_text.config(state="normal")
        self.output_text.insert(END, message + "\n", "debug_blue")
        self.output_text.see(END)
        self.output_text.config(state="disabled")

    def _poll_messages(self):
        """
        Every 100 ms, ask manualdebug_helpers.poll_messages() for any new debug messages.
        If there are messages, insert them (tagged “debug_blue”) into self.output_text,
        then reschedule another check in 100 ms.
        """
        messages = manualdebug_helpers.poll_messages()
        if messages:
            self.output_text.config(state="normal")
            for msg in messages:
                self.output_text.insert(END, msg, "debug_blue")
            self.output_text.see(END)
            self.output_text.config(state="disabled")
        # Schedule next poll in 100 ms:
        self.after(100, self._poll_messages)

    def check_line(self, lineno):
        """Check whether `lineno` (string) is a valid line number in the editor."""
        # Get the actual Text widget from the editor:
        text_widget = self.editor.text
        max_lines = int(text_widget.index('end-1c').split('.')[0])
        if lineno.isdigit() and 1 <= int(lineno) <= max_lines:
            return True
        return False

    def apply(self):
        """Apply the chosen print‐lines in the subprocess via RPC."""
        raw = self.line_var.get().strip()
        parts = [p.strip() for p in raw.split(",") if p.strip().isdigit()]
        lines = [int(p) for p in parts]

        try:
            # Ask the subprocess to set this debug‐line set
            result = self.editor.rpcclt.call(
                'idlelib.manualdebug_helpers.rpc_set_debug_lines',
                lines
            )
            self.output_message(f"Lines {lines}: applied! (rpc says: {result})")
        except Exception as e:
            self.output_message(f"RPC error: {e}")

    def cancel(self):
        """Unapply the chosen lines (remove them from the subprocess’s debug‐line set)."""
        raw = self.line_var.get().strip()
        parts = [p.strip() for p in raw.split(",") if p.strip().isdigit()]
        to_remove = [int(p) for p in parts]

        try:
            #  Fetch the current set from the subprocess
            current_set = self.editor.rpcclt.call(
                'idlelib.manualdebug_helpers.get_debug_lines'
            )
            #  Remove each requested line from it
            for ln in to_remove:
                current_set.discard(ln)
            # Write the updated set back to the subprocess
            result = self.editor.rpcclt.call(
                'idlelib.manualdebug_helpers.rpc_set_debug_lines',
                list(current_set)
            )
            self.output_message(f"Lines {to_remove}: unapplied! (rpc says: {result})")
        except Exception as e:
            self.output_message(f"RPC error: {e}")

    def destroy(self):
        """Override destroy so we can release any grabs (if used)."""
        try:
            self.grab_release()
        except Exception:
            pass
        super().destroy()


if __name__ == '__main__':
    from unittest import main
    main('idlelib.idle_test.test_configdialog', verbosity=2, exit=False)

    from idlelib.idle_test.htest import run
    run(ManualDebug)
