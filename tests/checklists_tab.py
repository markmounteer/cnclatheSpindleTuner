"""
Spindle Tuner - Checklists Tab

Provides pre-flight and commissioning checklists from the tuning guide:
- Hardware Checklist (§5 Pre-Flight Verification)
- Commissioning Checklist (final verification before production use)
"""

from __future__ import annotations

import json
import logging
import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Dict, Iterable, List, Mapping, MutableMapping, Tuple, Union

log = logging.getLogger(__name__)

try:
    from config import COMMISSIONING_CHECKLIST, HARDWARE_CHECKLIST
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

# NOTE: Default stays "local file", but you can redirect via env var.
_STATE_DIR = Path(os.getenv("SPINDLE_TUNER_STATE_DIR", "."))
STATE_FILE = _STATE_DIR / "checklist_state.json"


ItemDef = Union[str, Tuple[str, str]]  # "text" OR ("stable_id", "text")


class ScrollableFrame(ttk.Frame):
    """Reusable scrollable frame container (mouse-wheel safe across platforms)."""

    def __init__(self, container: tk.Misc, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self._canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind wheel scrolling only when cursor is over this widget (prevents global interference).
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _on_canvas_configure(self, event: tk.Event):
        self.canvas.itemconfig(self._canvas_window, width=event.width)

    def _bind_wheel(self, *_):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows/macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)  # Linux up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)  # Linux down

    def _unbind_wheel(self, *_):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event):
        # event.delta: Windows typically ±120 per notch; macOS can be smaller.
        delta = int(-1 * (event.delta / 120)) if getattr(event, "delta", 0) else 0
        if delta == 0 and getattr(event, "delta", 0):
            delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")

    def _on_mousewheel_linux(self, event: tk.Event):
        if getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(1, "units")


class ChecklistGroup(ttk.LabelFrame):
    """Unified group of checkboxes with a title and controls."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        description: str,
        items: Iterable[ItemDef],
        callback=None,
        key_id: str = "",
    ):
        super().__init__(parent, text=title, padding="10")

        self.key_id = key_id
        self.callback = callback
        self._suppress_callback = False

        self.item_ids: List[str] = []
        self.item_texts: List[str] = []
        self.vars: List[tk.BooleanVar] = []

        if description:
            ttk.Label(self, text=description, font=("Arial", 9, "italic"), foreground="#555").pack(
                anchor="w", pady=(0, 10)
            )

        for it in items:
            if isinstance(it, tuple):
                item_id, text = it
            else:
                # Back-compat: if only a string is supplied, derive an ID from the text.
                text = it
                item_id = text

            self.item_ids.append(str(item_id))
            self.item_texts.append(str(text))

            var = tk.BooleanVar()
            var.trace_add("write", self._on_change)
            self.vars.append(var)

            row = ttk.Frame(self)
            row.pack(fill=tk.X, pady=2)
            ttk.Checkbutton(row, text=text, variable=var).pack(anchor="w")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Reset", command=self.reset).pack(side=tk.LEFT)

    def _on_change(self, *_):
        if self._suppress_callback:
            return
        if self.callback:
            self.callback()

    def get_completion(self) -> Tuple[int, int]:
        completed = sum(1 for var in self.vars if var.get())
        return completed, len(self.vars)

    def is_complete(self) -> bool:
        return all(var.get() for var in self.vars)

    def reset(self):
        self._suppress_callback = True
        try:
            for var in self.vars:
                var.set(False)
        finally:
            self._suppress_callback = False
        if self.callback:
            self.callback()

    def select_all(self):
        self._suppress_callback = True
        try:
            for var in self.vars:
                var.set(True)
        finally:
            self._suppress_callback = False
        if self.callback:
            self.callback()

    def get_state(self) -> Dict[str, bool]:
        # New format: stable ID -> bool (survives reordering)
        return {item_id: bool(var.get()) for item_id, var in zip(self.item_ids, self.vars)}

    def set_state(self, states: Union[List[bool], Mapping[str, bool]]):
        self._suppress_callback = True
        try:
            if isinstance(states, list):
                # Back-compat: old format was list[bool] aligned with item order.
                if len(states) != len(self.vars):
                    return
                for var, state in zip(self.vars, states):
                    var.set(bool(state))
                return

            # New format: dict of id -> bool
            for idx, item_id in enumerate(self.item_ids):
                if item_id in states:
                    self.vars[idx].set(bool(states[item_id]))
        finally:
            self._suppress_callback = False


class ChecklistsTab:
    """Checklists feature slice with state persistence."""

    def __init__(self, parent: tk.Misc):
        self.parent = parent
        self.groups: Dict[str, ChecklistGroup] = {}
        self._suspend_save = False

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

        checklist_defs: List[Tuple[str, str, str, List[Tuple[str, str]]]] = [
            (
                "Hardware Checklist (Pre-Flight §5)",
                "Complete before each tuning session to ensure physical machine safety.",
                "hw",
                [(item_id, desc) for item_id, desc in HARDWARE_CHECKLIST],
            ),
            (
                "Commissioning Checklist (Final Verification)",
                "Complete before production use (Guide §13). Ensures final tuning stability.",
                "comm",
                [(item_id, desc) for item_id, desc in COMMISSIONING_CHECKLIST],
            ),
        ]

        for title, description, key_id, items in checklist_defs:
            group = ChecklistGroup(
                content_area,
                title=title,
                description=description,
                items=items,
                callback=self._on_update,
                key_id=key_id,
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

        self._on_update()

    def _on_update(self):
        total_checked = 0
        total_items = 0

        for group in self.groups.values():
            done, total = group.get_completion()
            total_checked += done
            total_items += total

        self.progress_label.config(text=f"{total_checked}/{total_items} Checks")
        self.progress_bar["value"] = (total_checked / total_items) * 100 if total_items else 0

        if total_items > 0 and total_checked == total_items:
            self.status_label.config(text="✓ READY FOR PRODUCTION", foreground="green")
        elif self.groups.get("hw") and self.groups["hw"].is_complete():
            self.status_label.config(text="✓ Hardware Verified", foreground="blue")
        else:
            self.status_label.config(text="")

        if not self._suspend_save:
            self._save_state()

    def _reset_all(self):
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to uncheck all items?"):
            return

        self._suspend_save = True
        try:
            for group in self.groups.values():
                group.set_state({item_id: False for item_id in group.item_ids})
        finally:
            self._suspend_save = False

        self._on_update()

    def _save_state(self):
        data: Dict[str, Union[List[bool], Dict[str, bool]]] = {key: group.get_state() for key, group in self.groups.items()}
        try:
            _STATE_DIR.mkdir(parents=True, exist_ok=True)
            tmp_path = STATE_FILE.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
            tmp_path.replace(STATE_FILE)
        except Exception as exc:  # pragma: no cover
            log.warning("Error saving checklist state: %s", exc)

    def _load_state(self):
        if not STATE_FILE.exists():
            return
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data: MutableMapping[str, Union[List[bool], Mapping[str, bool]]] = json.load(f)

            self._suspend_save = True
            try:
                for key, states in data.items():
                    if key in self.groups:
                        self.groups[key].set_state(states)
            finally:
                self._suspend_save = False

            self._on_update()
        except Exception as exc:  # pragma: no cover
            log.warning("Error loading checklist state: %s", exc)

    def is_hardware_complete(self) -> bool:
        group = self.groups.get("hw")
        return bool(group and group.is_complete())

    def is_commissioning_complete(self) -> bool:
        group = self.groups.get("comm")
        return bool(group and group.is_complete())

    def is_all_complete(self) -> bool:
        return self.is_hardware_complete() and self.is_commissioning_complete()


if __name__ == "__main__":  # pragma: no cover
    root = tk.Tk()
    root.geometry("500x700")
    root.title("Checklist Test")
    ChecklistsTab(root)
    root.mainloop()
