#!/usr/bin/env python3
"""
Spindle Tuner - Export & Profiles Feature

Handles data export, profile management, and INI file generation.

This module provides:
- Recording toggle and status display
- CSV data export for recorded telemetry
- Profile save/load with JSON storage
- INI section generation for LinuxCNC configuration
- Profile management with deletion and refresh capabilities
"""

import json
import logging
import re
from dataclasses import dataclass

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
    _HAS_TKINTER = True
except ImportError:
    tk = None
    ttk = None
    filedialog = None
    messagebox = None
    simpledialog = None
    _HAS_TKINTER = False
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, TypedDict

from config import PROFILES_DIR, BASELINE_PARAMS

# Configure module logger
logger = logging.getLogger(__name__)

# Constants
MAX_PROFILES_DISPLAYED: int = 10
INVALID_FILENAME_CHARS: re.Pattern = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class ProfileData(TypedDict, total=False):
    """Type definition for profile data structure."""
    name: str
    timestamp: str
    params: Dict[str, float]
    notes: str


@dataclass
class ParsedProfile:
    """Parsed profile information for display."""
    name: str
    timestamp: Optional[datetime]
    display_text: str
    path: Path


class ExportTab:
    """
    Export feature slice for the Spindle Tuner application.

    Provides functionality for:
    - Recording toggle and status display
    - CSV data export for recorded spindle telemetry
    - Profile save/load with JSON storage
    - INI section generation for LinuxCNC configuration
    - Profile management including deletion and refresh

    Attributes:
        parent: Parent ttk.Frame widget
        data_logger: DataLogger instance for recording management
        ini_handler: IniFileHandler for INI generation
        get_params: Callback to retrieve current tuning parameters
        set_params: Callback to apply loaded parameters
    """

    def __init__(
        self,
        parent: "ttk.Frame",
        data_logger: Any,  # DataLogger type from logger module
        ini_handler: Any,  # IniFileHandler type from hal module
        get_params_callback: Callable[[], Dict[str, float]],
        set_params_callback: Callable[[Dict[str, float]], None],
        max_profiles: int = MAX_PROFILES_DISPLAYED
    ) -> None:
        """
        Initialize the Export tab.

        Args:
            parent: Parent ttk.Frame to contain this tab's widgets
            data_logger: DataLogger instance for data recording/export
            ini_handler: IniFileHandler for INI section generation
            get_params_callback: Function that returns current parameter dict
            set_params_callback: Function that applies a parameter dict
            max_profiles: Maximum number of profiles to display in list
        """
        if not _HAS_TKINTER:
            raise ImportError(
                "tkinter is required for ExportTab but could not be imported."
            )

        self.parent = parent
        self.data_logger = data_logger
        self.ini_handler = ini_handler
        self.get_params = get_params_callback
        self.set_params = set_params_callback
        self._max_profiles = max_profiles
        self._profile_paths: List[Path] = []

        self._setup_ui()
        self._refresh_profiles_list()
    
    def _setup_ui(self) -> None:
        """Build export tab UI with all control sections."""
        ttk.Label(
            self.parent,
            text="Data Logging & Export",
            font=("Helvetica", 12, "bold")
        ).pack(pady=10)

        self._setup_recording_controls()
        self._setup_export_options()
        self._setup_profile_management()
        self._setup_profiles_list()

    def _setup_recording_controls(self) -> None:
        """Setup recording toggle, status indicator, and data controls."""
        frame = ttk.LabelFrame(self.parent, text="Recording", padding="10")
        frame.pack(fill=tk.X, padx=20, pady=10)

        row = ttk.Frame(frame)
        row.pack(fill=tk.X)

        self.rec_status = ttk.Label(row, text="● Recording", foreground="green")
        self.rec_status.pack(side=tk.LEFT, padx=10)

        self.btn_record_toggle = ttk.Button(
            row, text="Pause", command=self.toggle_recording
        )
        self.btn_record_toggle.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            row, text="Clear Data", command=self.clear_data
        ).pack(side=tk.LEFT, padx=5)

        self.points_label = ttk.Label(row, text="Points: 0")
        self.points_label.pack(side=tk.RIGHT, padx=10)

    def _setup_export_options(self) -> None:
        """Setup export buttons for CSV and INI generation."""
        frame = ttk.LabelFrame(self.parent, text="Export", padding="10")
        frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Button(
            frame, text="Export to CSV...", command=self.export_csv
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(
            frame, text="Generate INI Section...", command=self.show_ini_config
        ).pack(side=tk.LEFT, padx=10)

    def _setup_profile_management(self) -> None:
        """Setup profile save/load/delete buttons."""
        frame = ttk.LabelFrame(self.parent, text="Profiles", padding="10")
        frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Button(
            frame, text="Save Current Profile...", command=self.save_profile
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(
            frame, text="Load Profile...", command=self.load_profile
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(
            frame, text="Load Selected", command=self._load_selected_profile
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(
            frame, text="Delete Selected", command=self._delete_selected_profile
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(
            frame, text="Open Folder", command=self._open_profiles_folder
        ).pack(side=tk.RIGHT, padx=10)

    def _setup_profiles_list(self) -> None:
        """Setup recent profiles listbox with double-click to load."""
        frame = ttk.LabelFrame(self.parent, text="Recent Profiles", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.profiles_listbox = tk.Listbox(frame, height=6)
        self.profiles_listbox.pack(fill=tk.BOTH, expand=True)
        self.profiles_listbox.bind('<Double-1>', lambda e: self._load_selected_profile())
        self.profiles_listbox.bind('<Delete>', lambda e: self._delete_selected_profile())

        ttk.Button(
            frame, text="Refresh", command=self._refresh_profiles_list
        ).pack(pady=5)
    
    def toggle_recording(self) -> None:
        """Toggle data recording on/off and update UI status."""
        if self.data_logger.recording:
            self.data_logger.set_recording(False)
            self.rec_status.config(text="● Paused", foreground="orange")
            self.btn_record_toggle.config(text="Resume")
            logger.info("Recording paused")
        else:
            self.data_logger.set_recording(True)
            self.rec_status.config(text="● Recording", foreground="green")
            self.btn_record_toggle.config(text="Pause")
            logger.info("Recording resumed")

    def clear_data(self) -> None:
        """Clear all recorded data and update display."""
        self.data_logger.clear_recording()
        self.update_points_display()
        logger.info("Recording data cleared")

    def update_points_display(self) -> None:
        """Update the points count display label."""
        count = self.data_logger.get_point_count()
        self.points_label.config(text=f"Points: {count:,}")
    
    def export_csv(self) -> None:
        """
        Export recorded data to a CSV file.

        Opens a file dialog for the user to select the destination.
        Shows success/error message based on export result.
        """
        if self.data_logger.get_point_count() == 0:
            messagebox.showwarning("No Data", "No data recorded to export.")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"spindle_data_{timestamp}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=filename
        )

        if filepath:
            try:
                self.data_logger.export_csv(Path(filepath))
                messagebox.showinfo("Success", f"Data exported to:\n{filepath}")
                logger.info(f"CSV exported to {filepath}")
            except (OSError, PermissionError) as e:
                logger.error(f"CSV export failed: {e}")
                messagebox.showerror("Error", f"Export failed:\n{e}")

    def show_ini_config(self) -> None:
        """
        Display generated INI configuration in a dialog.

        Shows the INI section with options to copy to clipboard or save to file.
        """
        try:
            params = self.get_params()
            ini_text = self.ini_handler.generate_ini_section(params)
        except Exception as e:
            logger.error(f"Failed to generate INI configuration: {e}")
            messagebox.showerror("Error", f"Failed to generate INI configuration:\n{e}")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("Generated INI Configuration")
        dialog.geometry("700x500")
        dialog.transient(self.parent.winfo_toplevel())

        text = tk.Text(dialog, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, ini_text)
        text.config(state=tk.DISABLED)

        def copy_to_clipboard() -> None:
            dialog.clipboard_clear()
            dialog.clipboard_append(ini_text)
            messagebox.showinfo("Copied", "INI section copied to clipboard.", parent=dialog)

        def save_to_file() -> None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"spindle_pid_{timestamp}.ini.txt"
            save_path = filedialog.asksaveasfilename(
                parent=dialog,
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("INI files", "*.ini")],
                initialfile=default_filename
            )
            if save_path:
                try:
                    Path(save_path).write_text(ini_text, encoding="utf-8")
                    messagebox.showinfo("Saved", f"Saved to:\n{save_path}", parent=dialog)
                    logger.info(f"INI section saved to {save_path}")
                except (OSError, PermissionError) as e:
                    logger.error(f"Failed to save INI section: {e}")
                    messagebox.showerror("Save Failed", f"Could not save file:\n{e}", parent=dialog)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save to File...", command=save_to_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a profile name for use as a filename.

        Args:
            name: Raw profile name from user input

        Returns:
            Sanitized string safe for filesystem use
        """
        # Replace invalid characters with underscores
        sanitized = INVALID_FILENAME_CHARS.sub('_', name)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure not empty
        return sanitized or 'unnamed_profile'

    def _validate_profile_name(self, name: str) -> Optional[str]:
        """
        Validate a profile name.

        Args:
            name: Profile name to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not name or not name.strip():
            return "Profile name cannot be empty."
        if len(name) > 100:
            return "Profile name too long (max 100 characters)."
        return None

    def save_profile(self) -> None:
        """
        Save current parameters as a named profile.

        Prompts user for profile name, validates it, then saves
        the current tuning parameters to a JSON file.
        """
        name = simpledialog.askstring(
            "Save Profile",
            "Profile name:",
            parent=self.parent.winfo_toplevel()
        )
        if not name:
            return

        # Validate profile name
        validation_error = self._validate_profile_name(name)
        if validation_error:
            messagebox.showwarning("Invalid Name", validation_error)
            return

        name = name.strip()
        params = self.get_params()

        profile: ProfileData = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'notes': ''
        }

        # Ensure profiles directory exists
        try:
            PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create profiles directory: {e}")
            messagebox.showerror("Error", f"Cannot create profiles directory:\n{e}")
            return

        sanitized_name = self._sanitize_filename(name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{sanitized_name}_{timestamp}.json"
        filepath = PROFILES_DIR / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Profile saved:\n{filepath.name}")
            logger.info(f"Profile saved to {filepath}")
            self._refresh_profiles_list()
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to save profile: {e}")
            messagebox.showerror("Error", f"Failed to save profile:\n{e}")
    
    def _parse_profile_file(self, filepath: Path) -> Optional[ProfileData]:
        """
        Parse a profile JSON file.

        Args:
            filepath: Path to the profile JSON file

        Returns:
            ProfileData dict if successful, None if parsing fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate required structure
            if not isinstance(data, dict):
                logger.warning(f"Invalid profile format in {filepath}: not a dict")
                return None

            return data
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in profile {filepath}: {e}")
            return None
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot read profile {filepath}: {e}")
            return None

    def load_profile(self) -> None:
        """
        Load a profile from file using a file dialog.

        Opens a file selection dialog and loads the selected profile.
        """
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            initialdir=PROFILES_DIR
        )

        if filepath:
            self._load_profile_file(filepath)

    def _load_profile_file(self, filepath: str) -> None:
        """
        Load profile from specified file path.

        Args:
            filepath: Path to the profile JSON file (as string)
        """
        path = Path(filepath)
        profile = self._parse_profile_file(path)

        if profile is None:
            messagebox.showerror(
                "Error",
                "Failed to load profile:\nFile may be corrupted or invalid."
            )
            return

        name = profile.get('name', 'Unknown')
        params = profile.get('params', {})

        # Validate params is a dict
        if not isinstance(params, dict):
            logger.warning(f"Profile {filepath} has invalid params type: {type(params)}")
            messagebox.showerror(
                "Error",
                "Profile has invalid format:\n'params' is not a dictionary."
            )
            return

        # Filter to only known parameters with valid numeric values
        known_params = {}
        for k, v in params.items():
            if k in BASELINE_PARAMS:
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    known_params[k] = float(v)
                else:
                    logger.warning(f"Skipping non-numeric parameter {k}={v!r} in {filepath}")

        if not known_params:
            messagebox.showwarning(
                "No Parameters",
                "This profile contains no recognized parameters."
            )
            return

        # Format timestamp for display
        timestamp_str = profile.get('timestamp', 'Unknown')
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            display_time = dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, AttributeError):
            display_time = str(timestamp_str)[:16] if timestamp_str else 'Unknown'

        # Confirmation dialog
        msg = (
            f"Load profile '{name}'?\n\n"
            f"Parameters: {len(known_params)}\n"
            f"Created: {display_time}\n\n"
            "This will update the current tuning parameters."
        )

        if not messagebox.askyesno("Load Profile", msg):
            return

        self.set_params(known_params)
        messagebox.showinfo("Success", f"Loaded profile: {name}")
        logger.info(f"Loaded profile '{name}' from {filepath}")
    
    def _get_selected_profile_path(self) -> Optional[Path]:
        """
        Get the path of the currently selected profile.

        Returns:
            Path to selected profile, or None if nothing selected
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            return None

        idx = selection[0]
        if 0 <= idx < len(self._profile_paths):
            return self._profile_paths[idx]
        return None

    def _load_selected_profile(self) -> None:
        """Load the profile currently selected in the listbox."""
        filepath = self._get_selected_profile_path()

        if filepath is None:
            messagebox.showinfo(
                "Load Profile",
                "Select a profile from the list first."
            )
            return

        if not filepath.exists():
            messagebox.showerror(
                "Error",
                "Selected profile file no longer exists.\nRefreshing list..."
            )
            self._refresh_profiles_list()
            return

        self._load_profile_file(str(filepath))

    def _delete_selected_profile(self) -> None:
        """
        Delete the profile currently selected in the listbox.

        Prompts for confirmation before deletion.
        """
        filepath = self._get_selected_profile_path()

        if filepath is None:
            messagebox.showinfo(
                "Delete Profile",
                "Select a profile from the list first."
            )
            return

        if not filepath.exists():
            messagebox.showinfo(
                "Delete Profile",
                "Selected profile file no longer exists.\nRefreshing list..."
            )
            self._refresh_profiles_list()
            return

        # Get profile name for confirmation
        profile = self._parse_profile_file(filepath)
        if profile:
            name = profile.get('name', filepath.stem)
        else:
            name = filepath.stem

        if not messagebox.askyesno(
            "Delete Profile",
            f"Delete profile '{name}'?\n\nThis action cannot be undone."
        ):
            return

        try:
            filepath.unlink()
            messagebox.showinfo("Deleted", f"Profile '{name}' deleted.")
            logger.info(f"Deleted profile: {filepath}")
            self._refresh_profiles_list()
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to delete profile {filepath}: {e}")
            messagebox.showerror("Error", f"Failed to delete profile:\n{e}")

    def _open_profiles_folder(self) -> None:
        """Open the profiles directory in the system file manager."""
        import subprocess
        import sys

        try:
            PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Cannot create profiles directory: {e}")
            messagebox.showerror("Error", f"Cannot create profiles directory:\n{e}")
            return

        try:
            if sys.platform.startswith('win'):
                import os
                os.startfile(PROFILES_DIR)
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(PROFILES_DIR)], check=False)
            else:
                subprocess.run(['xdg-open', str(PROFILES_DIR)], check=False)
        except (OSError, FileNotFoundError) as e:
            logger.error(f"Could not open profiles folder: {e}")
            messagebox.showerror("Error", f"Could not open profiles folder:\n{e}")
    
    def _format_profile_display(self, profile_path: Path) -> str:
        """
        Format a profile path for display in the listbox.

        Args:
            profile_path: Path to the profile JSON file

        Returns:
            Formatted display string "name — date"
        """
        profile = self._parse_profile_file(profile_path)

        if profile:
            name = profile.get('name', profile_path.stem)
            timestamp = profile.get('timestamp', '')

            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except (ValueError, AttributeError):
                    date_str = str(timestamp)[:16]
                return f"{name} — {date_str}"
            return name

        # Fallback to filename + mtime for invalid/unreadable profiles
        try:
            mtime = datetime.fromtimestamp(profile_path.stat().st_mtime)
            return f"{profile_path.stem} — {mtime.strftime('%Y-%m-%d %H:%M')}"
        except OSError:
            return profile_path.stem

    def _get_file_mtime(self, path: Path) -> float:
        """
        Safely get file modification time.

        Args:
            path: Path to the file

        Returns:
            Modification time as float, or 0.0 if file is inaccessible
        """
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    def _refresh_profiles_list(self) -> None:
        """
        Refresh the profiles listbox with recent profiles.

        Displays up to max_profiles most recently modified profiles,
        sorted by modification time (newest first).
        """
        self.profiles_listbox.delete(0, tk.END)
        self._profile_paths = []

        if not PROFILES_DIR.exists():
            return

        try:
            # Collect profile paths, filtering out inaccessible files
            profile_files = []
            for p in PROFILES_DIR.glob("*.json"):
                mtime = self._get_file_mtime(p)
                if mtime > 0:
                    profile_files.append((p, mtime))
                else:
                    logger.warning(f"Skipping inaccessible profile: {p}")

            # Sort by modification time (newest first)
            profile_files.sort(key=lambda x: x[1], reverse=True)
            profiles = [p for p, _ in profile_files]
        except OSError as e:
            logger.warning(f"Error scanning profiles directory: {e}")
            return

        for profile_path in profiles[:self._max_profiles]:
            self._profile_paths.append(profile_path)
            display = self._format_profile_display(profile_path)
            self.profiles_listbox.insert(tk.END, display)
