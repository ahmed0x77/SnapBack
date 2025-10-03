# session_manager.py
"""
Backend module for managing Explorer sessions.
Handles saving, restoring, and managing session files.
"""
import os
import json
import time
import subprocess
from datetime import datetime
from typing import List, Dict, Optional

try:
    import win32com.client
    import win32gui
    import win32con
except Exception as e:
    raise SystemExit("pywin32 is required. Install with: pip install pywin32\nError: " + str(e))


class SessionManager:
    """Manages Explorer window sessions."""
    
    def __init__(self, sessions_dir: str = None):
        """Initialize the session manager.
        
        Args:
            sessions_dir: Directory to store session files. Defaults to ./sessions
        """
        if sessions_dir is None:
            sessions_dir = os.path.join(os.path.dirname(__file__), "sessions")
        self.sessions_dir = sessions_dir
        self._ensure_sessions_dir()
    
    def _ensure_sessions_dir(self):
        """Create sessions directory if it doesn't exist."""
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
    
    def get_all_explorer_windows(self) -> List[Dict]:
        """Get all open Explorer windows with their geometry.
        
        Returns:
            List of dicts with keys: path, hwnd, rect, show_cmd
        """
        shell = win32com.client.Dispatch("Shell.Application")
        windows = []
        
        for w in shell.Windows():
            try:
                doc = w.Document
                folder = getattr(doc, "Folder", None)
                if folder is None:
                    continue
                
                path = folder.Self.Path
                hwnd = int(w.HWND)
                
                # Get window placement
                try:
                    placement = win32gui.GetWindowPlacement(hwnd)
                    show_cmd = placement[1]
                    normal_rect = placement[4]  # (left, top, right, bottom)
                    left, top, right, bottom = normal_rect
                    width = right - left
                    height = bottom - top
                    rect = [left, top, width, height]
                except Exception:
                    # Fallback to GetWindowRect
                    try:
                        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                        width = right - left
                        height = bottom - top
                        rect = [left, top, width, height]
                        show_cmd = win32con.SW_SHOWNORMAL
                    except Exception:
                        continue
                
                windows.append({
                    "path": path,
                    "hwnd": hwnd,
                    "rect": rect,
                    "show_cmd": show_cmd
                })
            except Exception:
                continue
        
        return windows
    
    def save_session(self, name: str = None) -> str:
        """Save current Explorer session.
        
        Args:
            name: Optional custom name for the session. If None, uses timestamp.
        
        Returns:
            Path to the saved session file.
        """
        windows = self.get_all_explorer_windows()
        
        # Deduplicate by path (keep first seen)
        seen = set()
        session_entries = []
        for w in windows:
            p = w["path"]
            if p in seen:
                continue
            seen.add(p)
            session_entries.append({
                "path": p,
                "rect": w["rect"],
                "show_cmd": w["show_cmd"]
            })
        
        timestamp = datetime.now()
        payload = {
            "name": name or f"Session {timestamp.strftime('%b %d, %Y at %I:%M:%S %p')}",
            "saved_at": timestamp.isoformat(),
            "windows": session_entries
        }
        
        # Generate filename
        if name:
            # Use custom name, sanitize it
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_name}.json"
        else:
            # Use timestamp
            filename = f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.sessions_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_session(self, filepath: str) -> Dict:
        """Load a session from file.
        
        Args:
            filepath: Path to the session file.
        
        Returns:
            Dictionary with session data.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def list_sessions(self) -> List[Dict]:
        """List all saved sessions.
        
        Returns:
            List of dicts with keys: filepath, name, saved_at, window_count, tab_count
        """
        sessions = []
        
        if not os.path.exists(self.sessions_dir):
            return sessions
        
        for filename in os.listdir(self.sessions_dir):
            if not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(self.sessions_dir, filename)
            try:
                data = self.load_session(filepath)
                windows = data.get("windows", [])
                
                sessions.append({
                    "filepath": filepath,
                    "name": data.get("name", filename),
                    "saved_at": data.get("saved_at", ""),
                    "window_count": len(set(w["path"] for w in windows)),
                    "tab_count": len(windows)
                })
            except Exception as e:
                print(f"Error loading session {filename}: {e}")
                continue
        
        # Sort by saved_at descending (newest first)
        sessions.sort(key=lambda x: x["saved_at"], reverse=True)
        
        return sessions
    
    def delete_session(self, filepath: str):
        """Delete a session file.
        
        Args:
            filepath: Path to the session file to delete.
        """
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def restore_session(self, filepath: str, open_timeout: float = 2.0, poll_interval: float = 0.1):
        """Restore a saved session.
        
        Args:
            filepath: Path to the session file.
            open_timeout: Timeout in seconds to wait for new windows to open.
            poll_interval: Polling interval in seconds.
        
        Returns:
            Tuple of (restored_count, skipped_count)
        """
        data = self.load_session(filepath)
        windows = data.get("windows", [])
        
        used_hwnds = set()
        restored = 0
        skipped = 0
        
        # Separate windows into already-open and needs-opening
        to_open = []
        to_restore = []
        
        for w in windows:
            path = w.get("path")
            rect = w.get("rect")
            show_cmd = w.get("show_cmd", win32con.SW_SHOWNORMAL)
            
            if not path:
                skipped += 1
                continue
            
            # Try to find an already-open window for this path
            hwnd = self._find_window_by_path(path, used_hwnds)
            
            if hwnd is not None:
                # Already open, just needs geometry applied
                to_restore.append((hwnd, rect, show_cmd))
                used_hwnds.add(hwnd)
            else:
                # Need to open this window
                to_open.append((path, rect, show_cmd))
        
        # Launch ALL new windows in parallel (don't wait)
        for path, rect, show_cmd in to_open:
            try:
                subprocess.Popen(["explorer", path], shell=False)
            except Exception as e:
                print(f"Failed to start explorer for {path!r}: {e}")
                skipped += 1
        
        # Now wait for all windows to appear and match them
        if to_open:
            deadline = time.time() + open_timeout
            remaining = list(to_open)  # Copy the list
            
            while remaining and time.time() < deadline:
                # Check all remaining windows at once
                for i in range(len(remaining) - 1, -1, -1):
                    path, rect, show_cmd = remaining[i]
                    hwnd = self._find_window_by_path(path, used_hwnds)
                    
                    if hwnd is not None:
                        # Found it!
                        to_restore.append((hwnd, rect, show_cmd))
                        used_hwnds.add(hwnd)
                        remaining.pop(i)
                
                if remaining:
                    time.sleep(poll_interval)
            
            # Count any that didn't open in time as skipped
            for path, _, _ in remaining:
                print(f"Timed out waiting for Explorer window for: {path}")
                skipped += 1
        
        # Apply geometry to all windows (both already-open and newly-opened)
        for hwnd, rect, show_cmd in to_restore:
            success = self._apply_geometry(hwnd, rect, show_cmd)
            if success:
                restored += 1
            else:
                skipped += 1
        
        return restored, skipped
    
    def _find_window_by_path(self, path: str, used_hwnds: set = None) -> Optional[int]:
        """Find an existing shell window with matching path which is not used yet.
        
        Args:
            path: Path to search for.
            used_hwnds: Set of already-used window handles.
        
        Returns:
            Window handle if found, None otherwise.
        """
        if used_hwnds is None:
            used_hwnds = set()
        
        shell = win32com.client.Dispatch("Shell.Application")
        for w in shell.Windows():
            try:
                doc = w.Document
                folder = getattr(doc, "Folder", None)
                if folder is None:
                    continue
                
                window_path = folder.Self.Path
                hwnd = int(w.HWND)
                
                if window_path == path and hwnd not in used_hwnds:
                    return hwnd
            except Exception:
                continue
        
        return None
    
    def _apply_geometry(self, hwnd: int, rect: List[int], show_cmd: int) -> bool:
        """Apply geometry and show state to window.
        
        Args:
            hwnd: Window handle.
            rect: [left, top, width, height]
            show_cmd: Windows show command constant.
        
        Returns:
            True if successful, False otherwise.
        """
        left, top, width, height = rect
        
        try:
            if show_cmd == win32con.SW_SHOWMAXIMIZED:
                win32gui.MoveWindow(hwnd, left, top, width, height, True)
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            elif show_cmd == win32con.SW_SHOWMINIMIZED or show_cmd == win32con.SW_MINIMIZE:
                win32gui.MoveWindow(hwnd, left, top, width, height, True)
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            else:
                win32gui.MoveWindow(hwnd, left, top, width, height, True)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return True
        except Exception as e:
            print(f"Failed to move/show hwnd {hwnd}: {e}")
            return False
    
    def remove_path_from_session(self, filepath: str, path_to_remove: str) -> bool:
        """Remove a specific path from a session.
        
        Args:
            filepath: Path to the session file.
            path_to_remove: The folder path to remove from the session.
        
        Returns:
            True if session still has paths, False if session is now empty.
        """
        # Load session data
        session_data = self.load_session(filepath)
        windows = session_data.get("windows", [])
        
        # Filter out the path to remove
        updated_windows = [w for w in windows if w.get("path") != path_to_remove]
        
        # If all paths removed, delete the entire session file
        if not updated_windows:
            self.delete_session(filepath)
            return False
        
        # Update session with remaining windows
        session_data["windows"] = updated_windows
        
        # Save updated session
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def add_path_to_session(self, filepath: str, new_path: str, rect: List[int] = None, 
                           show_cmd: int = None) -> bool:
        """Add a new path to an existing session.
        
        Args:
            filepath: Path to the session file.
            new_path: The folder path to add to the session.
            rect: Window geometry [left, top, width, height]. If None, uses default.
            show_cmd: Windows show command. If None, uses SW_SHOWNORMAL.
        
        Returns:
            True if path was added, False if it already exists.
        """
        # Load session data
        session_data = self.load_session(filepath)
        windows = session_data.get("windows", [])
        
        # Check if path already exists
        for window in windows:
            if window.get("path") == new_path:
                return False  # Path already exists
        
        # Set defaults if not provided
        if rect is None:
            # Default window position and size
            rect = [100, 100, 1000, 600]
        
        if show_cmd is None:
            show_cmd = 1  # SW_SHOWNORMAL
        
        # Add new window entry
        new_window = {
            "path": new_path,
            "rect": rect,
            "show_cmd": show_cmd
        }
        windows.append(new_window)
        
        # Update session
        session_data["windows"] = windows
        
        # Save updated session
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return True
