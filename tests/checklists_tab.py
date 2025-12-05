"""
Spindle Tuner - Checklists Tab

Provides pre-flight and commissioning checklists from the tuning guide:
- Hardware Checklist (§5 Pre-Flight Verification)
- Commissioning Checklist (final verification before production use)
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple

try:
    from config import HARDWARE_CHECKLIST, COMMISSIONING_CHECKLIST
except ImportError:
    HARDWARE_CHECKLIST = [
        ("id1", "Check power supply voltage"),
        ("id2", "Verify ground connections"),
        ("id3", "Check emergency stop"),
    ]
    COMMISSIONING_CHECKLIST = [
        ("id4", "Run warm-up cycle"),
        ("id5", "Verify RPM accuracy"),
        ("id6", "Check bearing temperature"),
    ]

STATE_FILE = "checklist_state.json"


class ScrollableFrame(ttk.Frame):
    """Reusable scrollable frame container."""

    def __init__(self, container: tk.Misc, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event: tk.Event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event):
        if self.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ChecklistGroup(ttk.LabelFrame):
    """Unified group of checkboxes with a title and controls."""

    def __init__(
        self, parent: tk.Misc, title: str, description: str, items: List[str], callback=None, key_id: str = ""
    ):
        super().__init__(parent, text=title, padding="10")

        self.key_id = key_id
        self.items = items
        self.vars: List[tk.BooleanVar] = []
        self.callback = callback

        if description:
            ttk.Label(self, text=description, font=("Arial", 9, "italic"), foreground="#555").pack(
                anchor="w", pady=(0, 10)
            )

        for item in items:
            var = tk.BooleanVar()
            var.trace_add("write", self._on_change)
            self.vars.append(var)

            row = ttk.Frame(self)
            row.pack(fill=tk.X, pady=2)
            ttk.Checkbutton(row, text=item, variable=var).pack(anchor="w")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Reset", command=self.reset).pack(side=tk.LEFT)

    def _on_change(self, *args):
        if self.callback:
            self.callback()

    def get_completion(self) -> Tuple[int, int]:
        completed = sum(1 for var in self.vars if var.get())
        return completed, len(self.vars)

    def is_complete(self) -> bool:
        return all(var.get() for var in self.vars)

    def reset(self):
        for var in self.vars:
            var.set(False)

    def select_all(self):
        for var in self.vars:
            var.set(True)

    def get_state(self) -> List[bool]:
        return [var.get() for var in self.vars]

    def set_state(self, states: List[bool]):
        if len(states) != len(self.vars):
            return
        for var, state in zip(self.vars, states):
            var.set(state)


class ChecklistsTab:
    """Checklists feature slice with state persistence."""

    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self.groups: Dict[str, ChecklistGroup] = {}

        self._setup_ui()
        self._load_state()

    def _setup_ui(self):
        header = ttk.Frame(self.parent)
        header.pack(fill=tk.X, padx=10, pady=10)

        title_frame = ttk.Frame(header)
        title_frame.pack(side=tk.LEFT)
        ttk.Label(title_frame, text="Pre-Flight & Commissioning", font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(title_frame, text="Track verification progress", font=("Arial", 9), foreground="gray").pack(
            anchor="w"
        )

        stats_frame = ttk.Frame(header)
        stats_frame.pack(side=tk.RIGHT)
        self.progress_bar = ttk.Progressbar(stats_frame, orient="horizontal", length=150, mode="determinate")
        self.progress_bar.pack(side=tk.TOP, pady=(0, 2))
        self.progress_label = ttk.Label(stats_frame, text="0/0 Checks", font=("Arial", 10, "bold"))
        self.progress_label.pack(side=tk.TOP, anchor="e")

        ttk.Separator(self.parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 5))

        self.scroller = ScrollableFrame(self.parent)
        self.scroller.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        content_area = self.scroller.scrollable_frame

        checklist_defs: List[Tuple[str, str, str, List[str]]] = [
            (
                "Hardware Checklist (Pre-Flight §5)",
                "Complete before each tuning session to ensure physical machine safety.",
                "hw",
                [desc for _, desc in HARDWARE_CHECKLIST],
            ),
            (
                "Commissioning Checklist (Final Verification)",
                "Complete before production use (Guide §13). Ensures final tuning stability.",
                "comm",
                [desc for _, desc in COMMISSIONING_CHECKLIST],
            ),
        ]

        for title, description, key_id, items in checklist_defs:
            group = ChecklistGroup(
                content_area, title=title, description=description, items=items, callback=self._on_update, key_id=key_id
            )
            group.pack(fill=tk.X, pady=10, padx=5)
            self.groups[key_id] = group

        footer = ttk.Frame(content_area)
        footer.pack(fill=tk.X, pady=20, padx=5)
        ttk.Button(footer, text="Reset All Checklists", command=self._reset_all).pack(side=tk.LEFT)
        self.status_label = ttk.Label(footer, text="", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=20)

        tips_frame = ttk.LabelFrame(content_area, text="Quick Tips", padding="10")
        tips_frame.pack(fill=tk.X, pady=10, padx=5)
        tips = [
            "• Progress is saved automatically when you close the application.",
            "• Use the Hardware checklist every time you power on the spindle.",
            "• The Commissioning checklist is required only once after final tuning.",
        ]
        for tip in tips:
            ttk.Label(tips_frame, text=tip, foreground="#444").pack(anchor="w", pady=1)

    def _on_update(self):
        total_checked = 0
        total_items = 0

        for group in self.groups.values():
            done, total = group.get_completion()
            total_checked += done
            total_items += total

        self.progress_label.config(text=f"{total_checked}/{total_items} Checks")
        if total_items > 0:
            self.progress_bar["value"] = (total_checked / total_items) * 100

        if total_checked == total_items and total_items > 0:
            self.status_label.config(text="✓ READY FOR PRODUCTION", foreground="green")
        elif self.groups.get("hw") and self.groups["hw"].is_complete():
            self.status_label.config(text="✓ Hardware Verified", foreground="blue")
        else:
            self.status_label.config(text="")

        self._save_state()

    def _reset_all(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to uncheck all items?"):
            for group in self.groups.values():
                group.reset()
            self._save_state()

    def _save_state(self):
        data: Dict[str, List[bool]] = {key: group.get_state() for key, group in self.groups.items()}
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file)
        except Exception as exc:  # pragma: no cover - logging helpful in app but not critical in tests
            print(f"Error saving checklist state: {exc}")

    def _load_state(self):
        if not os.path.exists(STATE_FILE):
            return
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as file:
                data: Dict[str, List[bool]] = json.load(file)
            for key, states in data.items():
                if key in self.groups:
                    self.groups[key].set_state(states)
            self._on_update()
        except Exception as exc:  # pragma: no cover - logging helpful in app but not critical in tests
            print(f"Error loading checklist state: {exc}")

    def is_hardware_complete(self) -> bool:
        group = self.groups.get("hw")
        return bool(group and group.is_complete())

    def is_commissioning_complete(self) -> bool:
        group = self.groups.get("comm")
        return bool(group and group.is_complete())

    def is_all_complete(self) -> bool:
        return self.is_hardware_complete() and self.is_commissioning_complete()


if __name__ == "__main__":  # pragma: no cover - manual UI smoke test
    root = tk.Tk()
    root.geometry("500x700")
    root.title("Checklist Test")

    app = ChecklistsTab(root)

    root.mainloop()
