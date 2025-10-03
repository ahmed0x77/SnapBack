# app.py
"""
SnapBack - Explorer Session Manager
A GUI application to save and restore Windows Explorer sessions with window geometry.
"""
import os
import sys
from datetime import datetime
from tkinter import messagebox, filedialog
import customtkinter as ctk
from session_manager import SessionManager


# Set appearance mode and color theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class SessionCard(ctk.CTkFrame):
    """A card widget displaying a saved session."""
    
    def __init__(self, parent, session_data, on_select, on_restore, on_delete, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.session_data = session_data
        self.on_select = on_select
        self.on_restore = on_restore
        self.on_delete = on_delete
        
        # Configure card appearance
        self.configure(fg_color="white", corner_radius=8, border_width=1, border_color="#E0E0E0")
        self.grid_columnconfigure(0, weight=1)
        
        # Session name/title
        name = session_data.get("name", "Restore Explorer Windows")
        self.title_label = ctk.CTkLabel(
            self,
            text=name,
            font=ctk.CTkFont(size=14, weight="normal"),
            text_color="#2B2B2B",
            anchor="w"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 5))
        
        # Session info
        window_count = session_data.get("window_count", 0)
        tab_count = session_data.get("tab_count", 0)
        info_text = f"{window_count} Window{'s' if window_count != 1 else ''} - {tab_count} Tab{'s' if tab_count != 1 else ''}"
        self.info_label = ctk.CTkLabel(
            self,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color="#757575",
            anchor="w"
        )
        self.info_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 5))
        
        # Timestamp
        saved_at = session_data.get("saved_at", "")
        if saved_at:
            try:
                dt = datetime.fromisoformat(saved_at)
                timestamp_text = dt.strftime("%b %d, %Y at %I:%M:%S %p")
            except:
                timestamp_text = saved_at
        else:
            timestamp_text = ""
        
        self.timestamp_label = ctk.CTkLabel(
            self,
            text=timestamp_text,
            font=ctk.CTkFont(size=11),
            text_color="#9E9E9E",
            anchor="w"
        )
        self.timestamp_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 10))
        
        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=0)
        
        # Restore button
        self.restore_btn = ctk.CTkButton(
            button_frame,
            text="Restore",
            width=100,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="#FF8C00",
            hover_color="#FF7700",
            command=self._on_restore_clicked
        )
        self.restore_btn.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Delete button
        self.delete_btn = ctk.CTkButton(
            button_frame,
            text="Delete",
            width=100,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="#E0E0E0",
            hover_color="#D0D0D0",
            text_color="#2B2B2B",
            command=self._on_delete_clicked
        )
        self.delete_btn.grid(row=0, column=1, sticky="e")
        
        # Make card clickable
        self.bind("<Button-1>", self._on_card_clicked)
        self.title_label.bind("<Button-1>", self._on_card_clicked)
        self.info_label.bind("<Button-1>", self._on_card_clicked)
        self.timestamp_label.bind("<Button-1>", self._on_card_clicked)
    
    def _on_card_clicked(self, event=None):
        """Handle card click."""
        if self.on_select:
            self.on_select(self.session_data)
    
    def _on_restore_clicked(self):
        """Handle restore button click."""
        if self.on_restore:
            self.on_restore(self.session_data)
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self.on_delete:
            self.on_delete(self.session_data)
    
    def set_selected(self, selected: bool):
        """Update appearance to show selection state."""
        if selected:
            self.configure(border_color="#FF8C00", border_width=2)
        else:
            self.configure(border_color="#E0E0E0", border_width=1)


class PathItem(ctk.CTkFrame):
    """A widget displaying a single folder path."""
    
    def __init__(self, parent, path, on_delete=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.path = path
        self.on_delete = on_delete
        
        # Configure appearance
        self.configure(fg_color="#F5F5F5", corner_radius=6, height=50)
        self.grid_columnconfigure(1, weight=1)
        
        # Folder icon (using emoji)
        self.icon_label = ctk.CTkLabel(
            self,
            text="📁",
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.icon_label.grid(row=0, column=0, padx=(15, 10), pady=10, sticky="w")
        
        # Extract folder name and full path
        folder_name = os.path.basename(path) if path else "Unknown"
        if not folder_name:  # If path ends with backslash
            folder_name = os.path.basename(os.path.dirname(path))
        
        # Text container frame
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ew")
        text_frame.grid_columnconfigure(0, weight=0)
        text_frame.grid_columnconfigure(1, weight=1)
        
        # Folder name in black (bold)
        self.name_label = ctk.CTkLabel(
            text_frame,
            text=folder_name + ":",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2B2B2B",
            anchor="w"
        )
        self.name_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        
        # Full path in gray
        self.path_label = ctk.CTkLabel(
            text_frame,
            text=path,
            font=ctk.CTkFont(size=12),
            text_color="#757575",
            anchor="w"
        )
        self.path_label.grid(row=0, column=1, sticky="w")
        
        # Delete button (if callback provided) - always visible but styled differently
        self.delete_btn = None
        if on_delete:
            # Create button that's always there but styled to be subtle
            self.delete_btn = ctk.CTkButton(
                self,
                text="🗑",
                width=32,
                height=32,
                font=ctk.CTkFont(size=14),
                fg_color="transparent",
                hover_color="#FFCDD2",
                text_color="#BDBDBD",  # Light gray when not hovering on row
                command=self._on_delete_clicked,
                border_width=0
            )
            self.delete_btn.grid(row=0, column=2, padx=(0, 15), pady=10, sticky="e")
            
            # Bind hover events to change delete button appearance
            self.bind("<Enter>", self._on_hover_enter)
            self.bind("<Leave>", self._on_hover_leave)
            self.icon_label.bind("<Enter>", self._on_hover_enter)
            self.icon_label.bind("<Leave>", self._on_hover_leave)
            text_frame.bind("<Enter>", self._on_hover_enter)
            text_frame.bind("<Leave>", self._on_hover_leave)
            self.name_label.bind("<Enter>", self._on_hover_enter)
            self.name_label.bind("<Leave>", self._on_hover_leave)
            self.path_label.bind("<Enter>", self._on_hover_enter)
            self.path_label.bind("<Leave>", self._on_hover_leave)
    
    def _on_hover_enter(self, event=None):
        """Highlight delete button on hover."""
        if self.delete_btn:
            self.delete_btn.configure(
                fg_color="#FFEBEE",
                text_color="#C62828"
            )
    
    def _on_hover_leave(self, event=None):
        """Dim delete button when not hovering."""
        if self.delete_btn:
            self.delete_btn.configure(
                fg_color="transparent",
                text_color="#BDBDBD"
            )
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self.on_delete:
            self.on_delete(self.path)


class SnapBackApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize session manager
        self.session_manager = SessionManager()
        self.selected_session = None
        self.session_cards = []
        
        # Configure window
        self.title("SnapBack - Explorer Session Manager")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=0, minsize=400)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create UI
        self.create_left_panel()
        self.create_right_panel()
        
        # Load sessions
        self.load_sessions()
    
    def create_left_panel(self):
        """Create the left panel with session list."""
        # Main left panel
        self.left_panel = ctk.CTkFrame(self, fg_color="#E5E5E5", corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        self.left_panel.grid_rowconfigure(2, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        # Header frame
        header_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Logo and title
        title_label = ctk.CTkLabel(
            header_frame,
            text="📁 SnapBack",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FF8C00",
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Search icon (placeholder)
        search_label = ctk.CTkLabel(
            header_frame,
            text="🔍",
            font=ctk.CTkFont(size=18),
            text_color="#757575"
        )
        search_label.grid(row=0, column=1, sticky="e")
        
        # Action buttons frame
        action_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        action_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        action_frame.grid_columnconfigure(0, weight=1)
        
        # Session name input field
        self.session_name_entry = ctk.CTkEntry(
            action_frame,
            placeholder_text="Enter session name...",
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="white",
            border_width=1,
            border_color="#E0E0E0",
            corner_radius=8
        )
        self.session_name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # Add/Save button
        add_btn = ctk.CTkButton(
            action_frame,
            text="+",
            width=45,
            height=45,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#FF8C00",
            hover_color="#FF7700",
            text_color="white",
            border_width=0,
            corner_radius=8,
            command=self.save_current_session
        )
        add_btn.grid(row=0, column=1)
        
        # Scrollable frame for session cards
        self.sessions_frame = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color="transparent",
            corner_radius=0
        )
        self.sessions_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.sessions_frame.grid_columnconfigure(0, weight=1)
    
    def create_right_panel(self):
        """Create the right panel with session details."""
        # Main right panel
        self.right_panel = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        # Header frame
        self.detail_header = ctk.CTkFrame(self.right_panel, fg_color="#F8F8F8", corner_radius=0, height=120)
        self.detail_header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 1))
        self.detail_header.grid_columnconfigure(0, weight=1)
        self.detail_header.grid_propagate(False)
        
        # Session title
        self.detail_title = ctk.CTkLabel(
            self.detail_header,
            text="Select a session to view details",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2B2B2B",
            anchor="w"
        )
        self.detail_title.grid(row=0, column=0, sticky="w", padx=30, pady=(20, 5))
        
        # Session info
        self.detail_info = ctk.CTkLabel(
            self.detail_header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#757575",
            anchor="w"
        )
        self.detail_info.grid(row=1, column=0, sticky="w", padx=30, pady=(0, 5))
        
        # Session timestamp
        self.detail_timestamp = ctk.CTkLabel(
            self.detail_header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#9E9E9E",
            anchor="w"
        )
        self.detail_timestamp.grid(row=2, column=0, sticky="w", padx=30, pady=(0, 20))
        
        # Add Folder button (initially hidden)
        self.add_folder_btn = ctk.CTkButton(
            self.right_panel,
            text="+ Add Folder",
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="#FF8C00",
            hover_color="#FF7700",
            text_color="white",
            corner_radius=6,
            command=self.add_folder_to_session
        )
        # Will be shown when a session is selected
        
        # Scrollable frame for paths
        self.paths_frame = ctk.CTkScrollableFrame(
            self.right_panel,
            fg_color="white",
            corner_radius=0
        )
        self.paths_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(10, 30))
        self.paths_frame.grid_columnconfigure(0, weight=1)
    
    def load_sessions(self):
        """Load all sessions and display them."""
        # Clear existing cards
        for card in self.session_cards:
            card.destroy()
        self.session_cards.clear()
        
        # Load sessions from manager
        sessions = self.session_manager.list_sessions()
        
        # Create cards
        for i, session in enumerate(sessions):
            card = SessionCard(
                self.sessions_frame,
                session,
                on_select=self.select_session,
                on_restore=self.restore_session,
                on_delete=self.delete_session
            )
            card.grid(row=i, column=0, sticky="ew", pady=(0, 10))
            self.session_cards.append(card)
        
        # If no sessions, show a message
        if not sessions:
            no_sessions_label = ctk.CTkLabel(
                self.sessions_frame,
                text="No saved sessions yet.\nClick '+' to save current Explorer windows.",
                font=ctk.CTkFont(size=13),
                text_color="#9E9E9E",
                justify="center"
            )
            no_sessions_label.grid(row=0, column=0, pady=50)
    
    def select_session(self, session_data):
        """Display session details in right panel."""
        self.selected_session = session_data
        
        # Update card selection states
        for card in self.session_cards:
            card.set_selected(card.session_data == session_data)
        
        # Update header
        name = session_data.get("name", "Restore Explorer Windows")
        self.detail_title.configure(text=name)
        
        window_count = session_data.get("window_count", 0)
        tab_count = session_data.get("tab_count", 0)
        info_text = f"{window_count} Window{'s' if window_count != 1 else ''} - {tab_count} Tab{'s' if tab_count != 1 else ''}"
        self.detail_info.configure(text=info_text)
        
        saved_at = session_data.get("saved_at", "")
        if saved_at:
            try:
                dt = datetime.fromisoformat(saved_at)
                timestamp_text = dt.strftime("%b %d, %Y at %I:%M:%S %p")
            except:
                timestamp_text = saved_at
        else:
            timestamp_text = ""
        self.detail_timestamp.configure(text=timestamp_text)
        
        # Show Add Folder button
        self.add_folder_btn.grid(row=1, column=0, sticky="w", padx=30, pady=(10, 10))
        
        # Clear existing path items
        for widget in self.paths_frame.winfo_children():
            widget.destroy()
        
        # Load session data and display paths
        try:
            filepath = session_data.get("filepath")
            session_full_data = self.session_manager.load_session(filepath)
            windows = session_full_data.get("windows", [])
            
            for i, window in enumerate(windows):
                path = window.get("path", "")
                if path:
                    path_item = PathItem(
                        self.paths_frame, 
                        path,
                        on_delete=lambda p=path: self.delete_path_from_session(p, filepath)
                    )
                    path_item.grid(row=i, column=0, sticky="ew", pady=(0, 8))
        except Exception as e:
            error_label = ctk.CTkLabel(
                self.paths_frame,
                text=f"Error loading session details:\n{str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="#C62828"
            )
            error_label.grid(row=0, column=0, pady=20)
    
    def save_current_session(self):
        """Save current Explorer session."""
        try:
            # Get session name from input field
            session_name = self.session_name_entry.get().strip()
            
            # If name is empty, use None to get auto-generated name
            if not session_name:
                session_name = None
            
            # Save session
            filepath = self.session_manager.save_session(session_name)
            
            # Clear the input field
            self.session_name_entry.delete(0, 'end')
            
            # Reload sessions
            self.load_sessions()
            
            # Show success message
            messagebox.showinfo(
                "Success",
                "Explorer session saved successfully!"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to save session:\n{str(e)}"
            )
    
    def restore_session(self, session_data):
        """Restore a saved session."""
        try:
            filepath = session_data.get("filepath")
            
            # Confirm action
            if not messagebox.askyesno(
                "Restore Session",
                "This will open Explorer windows for all saved paths.\nContinue?"
            ):
                return
            
            # Restore session
            restored, skipped = self.session_manager.restore_session(filepath)
            
            # Show result
            messagebox.showinfo(
                "Restore Complete",
                f"Restored: {restored} window(s)\nSkipped: {skipped} window(s)"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to restore session:\n{str(e)}"
            )
    
    def delete_session(self, session_data):
        """Delete a saved session."""
        try:
            # Confirm deletion
            if not messagebox.askyesno(
                "Delete Session",
                f"Are you sure you want to delete this session?\n\n{session_data.get('name', 'Session')}"
            ):
                return
            
            # Delete session file
            filepath = session_data.get("filepath")
            self.session_manager.delete_session(filepath)
            
            # Clear right panel if this was the selected session
            if self.selected_session == session_data:
                self.selected_session = None
                self.detail_title.configure(text="Select a session to view details")
                self.detail_info.configure(text="")
                self.detail_timestamp.configure(text="")
                for widget in self.paths_frame.winfo_children():
                    widget.destroy()
            
            # Reload sessions
            self.load_sessions()
            
            messagebox.showinfo("Success", "Session deleted successfully!")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to delete session:\n{str(e)}"
            )
    
    def delete_path_from_session(self, path_to_delete, session_filepath):
        """Delete a specific path from a session (UI wrapper)."""
        try:
            # Confirm deletion
            folder_name = os.path.basename(path_to_delete) if path_to_delete else "this folder"
            if not folder_name:
                folder_name = os.path.basename(os.path.dirname(path_to_delete))
            
            if not messagebox.askyesno(
                "Remove Folder",
                f"Remove '{folder_name}' from this session?"
            ):
                return
            
            # Use SessionManager to remove the path
            session_has_paths = self.session_manager.remove_path_from_session(
                session_filepath, 
                path_to_delete
            )
            
            # If session is now empty (returns False)
            if not session_has_paths:
                messagebox.showinfo(
                    "Session Empty",
                    "This was the last folder in the session. The session has been deleted."
                )
                
                # Clear right panel
                self.selected_session = None
                self.detail_title.configure(text="Select a session to view details")
                self.detail_info.configure(text="")
                self.detail_timestamp.configure(text="")
                for widget in self.paths_frame.winfo_children():
                    widget.destroy()
                
                # Reload sessions list
                self.load_sessions()
            else:
                # Session still has paths - reload the display
                if self.selected_session:
                    # Reload session data to get updated counts
                    session_data = self.session_manager.load_session(session_filepath)
                    windows = session_data.get("windows", [])
                    
                    updated_session_data = self.selected_session.copy()
                    updated_session_data["window_count"] = len(set(w["path"] for w in windows))
                    updated_session_data["tab_count"] = len(windows)
                    self.select_session(updated_session_data)
                
                # Reload sessions list to update counts
                self.load_sessions()
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to remove folder from session:\n{str(e)}"
            )


def main():
    """Run the application."""
    app = SnapBackApp()
    app.mainloop()


if __name__ == "__main__":
    main()
