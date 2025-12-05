"""
Spindle Tuner - Checklists Tab

Provides pre-flight and commissioning checklists from the tuning guide:
- Hardware Checklist (§5 Pre-Flight Verification)
- Commissioning Checklist (final verification before production use)
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple

from config import HARDWARE_CHECKLIST, COMMISSIONING_CHECKLIST


class ChecklistWidget(ttk.Frame):
    """Reusable checklist widget with completion tracking."""

    def __init__(self, parent, title: str, items: List[str], **kwargs):
        super().__init__(parent, **kwargs)

        self.items = items
        self.vars = []

        if title:
            ttk.Label(self, text=title, font=("Arial", 10, "bold")).pack(anchor="w")

        for item in items:
            var = tk.BooleanVar()
            self.vars.append(var)
            cb = ttk.Checkbutton(self, text=item, variable=var)
            cb.pack(anchor="w", padx=10)

    def get_completion(self) -> Tuple[int, int]:
        """Get (completed, total) counts."""
        completed = sum(1 for v in self.vars if v.get())
        return completed, len(self.vars)

    def is_complete(self) -> bool:
        """Check if all items are checked."""
        return all(v.get() for v in self.vars)

    def reset(self):
        """Uncheck all items."""
        for v in self.vars:
            v.set(False)


class ChecklistsTab:
    """
    Checklists feature slice.

    Provides pre-flight and commissioning checklists from the tuning guide:
    - Hardware Checklist (§5 Pre-Flight Verification)
    - Commissioning Checklist (final verification before production use)
    """

    def __init__(self, parent: ttk.Frame):
        """
        Initialize checklists tab.

        Args:
            parent: Parent frame to build UI in
        """
        self.parent = parent
        self.hw_checklist = None
        self.comm_checklist = None

        self._setup_ui()

    def _setup_ui(self):
        """Build the checklists UI."""
        # Header
        header = ttk.Frame(self.parent)
        header.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header, text="Pre-Flight & Commissioning Checklists",
                  font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        # Progress display
        self.progress_label = ttk.Label(header, text="Progress: 0/0",
                                        font=("Arial", 10))
        self.progress_label.pack(side=tk.RIGHT)

        # Create scrollable frame
        canvas = tk.Canvas(self.parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollable area
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Hardware Checklist (§5 Pre-Flight)
        hw_frame = ttk.LabelFrame(scrollable, text="Hardware Checklist (Pre-Flight §5)",
                                  padding="10")
        hw_frame.pack(fill=tk.X, pady=10, padx=5)

        # Add description
        ttk.Label(hw_frame, text="Complete before each tuning session:",
                  font=("Arial", 9, "italic"), foreground="gray").pack(anchor="w", pady=(0, 5))

        # Extract descriptions from tuple list
        hw_items = [desc for _, desc in HARDWARE_CHECKLIST]
        self.hw_checklist = ChecklistWidget(hw_frame, "", hw_items)
        self.hw_checklist.pack(fill=tk.X)

        # Bind checkbuttons to update progress
        for var in self.hw_checklist.vars:
            var.trace_add("write", lambda *args: self._update_progress())

        # Hardware checklist buttons
        hw_btn_frame = ttk.Frame(hw_frame)
        hw_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(hw_btn_frame, text="Reset Hardware Checklist",
                   command=self._reset_hardware).pack(side=tk.LEFT, padx=5)

        ttk.Separator(scrollable, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Commissioning Checklist
        comm_frame = ttk.LabelFrame(scrollable,
                                    text="Commissioning Checklist (Final Verification)",
                                    padding="10")
        comm_frame.pack(fill=tk.X, pady=10, padx=5)

        # Add description
        ttk.Label(comm_frame, text="Complete before production use (Guide §13):",
                  font=("Arial", 9, "italic"), foreground="gray").pack(anchor="w", pady=(0, 5))

        # Extract descriptions from tuple list
        comm_items = [desc for _, desc in COMMISSIONING_CHECKLIST]
        self.comm_checklist = ChecklistWidget(comm_frame, "", comm_items)
        self.comm_checklist.pack(fill=tk.X)

        # Bind checkbuttons to update progress
        for var in self.comm_checklist.vars:
            var.trace_add("write", lambda *args: self._update_progress())

        # Commissioning checklist buttons
        comm_btn_frame = ttk.Frame(comm_frame)
        comm_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(comm_btn_frame, text="Reset Commissioning Checklist",
                   command=self._reset_commissioning).pack(side=tk.LEFT, padx=5)

        ttk.Separator(scrollable, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Overall controls
        ctrl_frame = ttk.Frame(scrollable)
        ctrl_frame.pack(fill=tk.X, pady=10, padx=5)

        ttk.Button(ctrl_frame, text="Reset All Checklists",
                   command=self._reset_all).pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(ctrl_frame, text="", foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Tips section
        tips_frame = ttk.LabelFrame(scrollable, text="Tips", padding="10")
        tips_frame.pack(fill=tk.X, pady=10, padx=5)

        tips = [
            "Complete hardware checklist before each tuning session",
            "Commissioning checklist is for final production readiness",
            "See Guide §5 for hardware verification details",
            "See Guide §13 for commissioning cleanup procedures",
        ]
        for tip in tips:
            ttk.Label(tips_frame, text=f"  {tip}",
                      foreground="gray").pack(anchor="w")

        # Initial progress update
        self._update_progress()

    def _update_progress(self):
        """Update progress display."""
        hw_done, hw_total = self.hw_checklist.get_completion()
        comm_done, comm_total = self.comm_checklist.get_completion()

        total_done = hw_done + comm_done
        total_items = hw_total + comm_total

        self.progress_label.config(text=f"Progress: {total_done}/{total_items}")

        # Update status
        if total_done == total_items:
            self.status_label.config(text="All checklists complete!",
                                     foreground="green")
        elif hw_done == hw_total:
            self.status_label.config(text="Hardware complete, commissioning pending",
                                     foreground="blue")
        else:
            self.status_label.config(text="", foreground="blue")

    def _reset_hardware(self):
        """Reset hardware checklist."""
        self.hw_checklist.reset()
        self._update_progress()

    def _reset_commissioning(self):
        """Reset commissioning checklist."""
        self.comm_checklist.reset()
        self._update_progress()

    def _reset_all(self):
        """Reset all checklists."""
        self.hw_checklist.reset()
        self.comm_checklist.reset()
        self._update_progress()

    def is_hardware_complete(self) -> bool:
        """Check if hardware checklist is complete."""
        return self.hw_checklist.is_complete()

    def is_commissioning_complete(self) -> bool:
        """Check if commissioning checklist is complete."""
        return self.comm_checklist.is_complete()

    def is_all_complete(self) -> bool:
        """Check if all checklists are complete."""
        return self.is_hardware_complete() and self.is_commissioning_complete()
