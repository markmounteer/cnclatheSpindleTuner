#!/usr/bin/env python3
"""
Spindle Tuner - Export & Profiles Feature

Handles data export, profile management, and INI file generation.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable

from config import PROFILES_DIR, BASELINE_PARAMS


class ExportTab:
    """
    Export feature slice.
    
    Provides:
    - Recording toggle and status
    - CSV data export
    - Profile save/load
    - INI section generation
    """
    
    def __init__(self, parent: ttk.Frame, data_logger, ini_handler,
                 get_params_callback: Callable[[], Dict[str, float]],
                 set_params_callback: Callable[[Dict[str, float]], None]):
        self.parent = parent
        self.logger = data_logger
        self.ini_handler = ini_handler
        self.get_params = get_params_callback
        self.set_params = set_params_callback
        self._profile_paths = []  # Track paths for Load Selected
        
        self._setup_ui()
        self._refresh_profiles_list()
    
    def _setup_ui(self):
        """Build export tab UI."""
        ttk.Label(self.parent, text="Data Logging & Export",
                 font=("Helvetica", 12, "bold")).pack(pady=10)
        
        # Recording controls
        self._setup_recording_controls()
        
        # Export options
        self._setup_export_options()
        
        # Profile management
        self._setup_profile_management()
        
        # Recent profiles list
        self._setup_profiles_list()
    
    def _setup_recording_controls(self):
        """Setup recording toggle and status."""
        frame = ttk.LabelFrame(self.parent, text="Recording", padding="10")
        frame.pack(fill=tk.X, padx=20, pady=10)
        
        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        
        self.rec_status = ttk.Label(row, text="● Recording", foreground="green")
        self.rec_status.pack(side=tk.LEFT, padx=10)
        
        self.btn_record_toggle = ttk.Button(row, text="Pause",
                  command=self.toggle_recording)
        self.btn_record_toggle.pack(side=tk.LEFT, padx=5)
        ttk.Button(row, text="Clear Data",
                  command=self.clear_data).pack(side=tk.LEFT, padx=5)
        
        self.points_label = ttk.Label(row, text="Points: 0")
        self.points_label.pack(side=tk.RIGHT, padx=10)
    
    def _setup_export_options(self):
        """Setup export buttons."""
        frame = ttk.LabelFrame(self.parent, text="Export", padding="10")
        frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(frame, text="Export to CSV...",
                  command=self.export_csv).pack(side=tk.LEFT, padx=10)
        ttk.Button(frame, text="Generate INI Section...",
                  command=self.show_ini_config).pack(side=tk.LEFT, padx=10)
    
    def _setup_profile_management(self):
        """Setup profile save/load buttons."""
        frame = ttk.LabelFrame(self.parent, text="Profiles", padding="10")
        frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(frame, text="Save Current Profile...",
                  command=self.save_profile).pack(side=tk.LEFT, padx=10)
        ttk.Button(frame, text="Load Profile...",
                  command=self.load_profile).pack(side=tk.LEFT, padx=10)
        ttk.Button(frame, text="Load Selected",
                  command=self._load_selected_profile).pack(side=tk.LEFT, padx=10)
        ttk.Button(frame, text="Open Folder",
                  command=self._open_profiles_folder).pack(side=tk.RIGHT, padx=10)
    
    def _setup_profiles_list(self):
        """Setup recent profiles listbox."""
        frame = ttk.LabelFrame(self.parent, text="Recent Profiles", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.profiles_listbox = tk.Listbox(frame, height=6)
        self.profiles_listbox.pack(fill=tk.BOTH, expand=True)
        self.profiles_listbox.bind('<Double-1>', lambda e: self._load_selected_profile())
        
        ttk.Button(frame, text="Refresh",
                  command=self._refresh_profiles_list).pack(pady=5)
    
    def toggle_recording(self):
        """Toggle data recording on/off."""
        if self.logger.recording:
            self.logger.set_recording(False)
            self.rec_status.config(text="● Paused", foreground="orange")
            self.btn_record_toggle.config(text="Resume")
        else:
            self.logger.set_recording(True)
            self.rec_status.config(text="● Recording", foreground="green")
            self.btn_record_toggle.config(text="Pause")
    
    def clear_data(self):
        """Clear recorded data."""
        self.logger.clear_recording()
        self.update_points_display()
    
    def update_points_display(self):
        """Update the points count display."""
        count = self.logger.get_point_count()
        self.points_label.config(text=f"Points: {count}")
    
    def export_csv(self):
        """Export data to CSV file."""
        if self.logger.get_point_count() == 0:
            messagebox.showwarning("No Data", "No data recorded to export.")
            return
        
        filename = f"spindle_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=filename
        )
        
        if filepath:
            if self.logger.export_csv(Path(filepath)):
                messagebox.showinfo("Success", f"Data exported to {filepath}")
            else:
                messagebox.showerror("Error", "Export failed.")
    
    def show_ini_config(self):
        """Show generated INI configuration."""
        params = self.get_params()
        ini_text = self.ini_handler.generate_ini_section(params)
        
        # Show in dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Generated INI Configuration")
        dialog.geometry("700x500")
        dialog.transient(self.parent.winfo_toplevel())
        
        text = tk.Text(dialog, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, ini_text)
        text.config(state=tk.DISABLED)
        
        def copy_to_clipboard():
            dialog.clipboard_clear()
            dialog.clipboard_append(ini_text)
            messagebox.showinfo("Copied", "INI section copied to clipboard.")
        
        def save_to_file():
            filename = f"spindle_pid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ini.txt"
            filepath = filedialog.asksaveasfilename(
                parent=dialog,
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("INI files", "*.ini")],
                initialfile=filename
            )
            if filepath:
                try:
                    Path(filepath).write_text(ini_text, encoding="utf-8")
                    messagebox.showinfo("Saved", f"Saved to:\n{filepath}", parent=dialog)
                except Exception as e:
                    messagebox.showerror("Save Failed", f"Could not save file:\n{e}", parent=dialog)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Copy to Clipboard",
                  command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save to File...",
                  command=save_to_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close",
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_profile(self):
        """Save current parameters as a profile."""
        name = simpledialog.askstring("Save Profile", "Profile name:")
        if not name:
            return
        
        params = self.get_params()
        
        profile = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'notes': ''
        }
        
        # Ensure profiles directory exists
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        
        filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = PROFILES_DIR / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(profile, f, indent=2)
            messagebox.showinfo("Success", f"Profile saved to {filepath}")
            self._refresh_profiles_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}")
    
    def load_profile(self):
        """Load a profile from file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            initialdir=PROFILES_DIR
        )
        
        if filepath:
            self._load_profile_file(filepath)
    
    def _load_profile_file(self, filepath: str):
        """Load profile from specified file."""
        try:
            with open(filepath, 'r') as f:
                profile = json.load(f)
            
            name = profile.get('name', 'Unknown')
            params = profile.get('params', {})
            
            # Filter to only known parameters
            known_params = {k: v for k, v in params.items() if k in BASELINE_PARAMS}
            
            if not known_params:
                messagebox.showwarning("No Parameters", 
                    "This profile contains no recognized parameters.")
                return
            
            # Confirmation dialog
            msg = f"Load profile '{name}'?\n\n"
            msg += f"Parameters: {len(known_params)}\n"
            msg += f"Created: {profile.get('timestamp', 'Unknown')}\n\n"
            msg += "This will update the current tuning parameters."
            
            if not messagebox.askyesno("Load Profile", msg):
                return
            
            self.set_params(known_params)
            messagebox.showinfo("Success", f"Loaded profile: {name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile: {e}")
    
    def _load_selected_profile(self):
        """Load the selected profile from listbox."""
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showinfo("Load Profile", "Select a profile from the list first.")
            return
        
        idx = selection[0]
        if 0 <= idx < len(self._profile_paths):
            filepath = self._profile_paths[idx]
            if filepath.exists():
                self._load_profile_file(str(filepath))
    
    def _open_profiles_folder(self):
        """Open the profiles directory in file manager."""
        import subprocess
        import sys
        
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            if sys.platform.startswith('win'):
                import os
                os.startfile(PROFILES_DIR)
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(PROFILES_DIR)], check=False)
            else:
                subprocess.run(['xdg-open', str(PROFILES_DIR)], check=False)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open profiles folder:\n{e}")
    
    def _refresh_profiles_list(self):
        """Refresh the profiles listbox with name and date."""
        self.profiles_listbox.delete(0, tk.END)
        self._profile_paths = []  # Track paths for Load Selected
        
        if not PROFILES_DIR.exists():
            return
        
        profiles = sorted(PROFILES_DIR.glob("*.json"), 
                         key=lambda p: p.stat().st_mtime, reverse=True)
        
        for profile_path in profiles[:10]:  # Show 10 most recent
            self._profile_paths.append(profile_path)
            
            # Try to show "name — date" format
            try:
                with open(profile_path, 'r') as f:
                    data = json.load(f)
                name = data.get('name', profile_path.stem)
                timestamp = data.get('timestamp', '')
                if timestamp:
                    # Parse ISO timestamp and format nicely
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        date_str = timestamp[:16]
                    display = f"{name} — {date_str}"
                else:
                    display = name
            except:
                # Fallback to filename + mtime
                mtime = datetime.fromtimestamp(profile_path.stat().st_mtime)
                display = f"{profile_path.stem} — {mtime.strftime('%Y-%m-%d %H:%M')}"
            
            self.profiles_listbox.insert(tk.END, display)
