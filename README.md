# SnapBack - Explorer Session Manager

A Windows application to save and restore File Explorer sessions with window positions and sizes.

## Features

- 💾 **Save Explorer Sessions**: Capture all open Explorer windows with their exact positions and sizes
- 🔄 **Restore Sessions**: Restore previously saved sessions with one click
- 📋 **Session Management**: View, manage, and delete saved sessions
- 🎨 **Modern UI**: Clean, intuitive interface built with CustomTkinter
- 📁 **Multiple Sessions**: Save and organize multiple workspace snapshots

## Requirements

- Python 3.7+
- Windows OS
- Required packages:
  - customtkinter
  - pywin32

## Installation

1. Clone or download this repository

2. Install required packages:

```bash
pip install customtkinter pywin32
```

## Usage

Run the application:

```bash
python app.py
```

### Main Features:

1. **Save Current Session**: Click the "+" button or "Restore Explorer Windows" button to save all currently open Explorer windows

2. **View Sessions**: Click on any session card in the left panel to see its details in the right panel

3. **Restore Session**: Click the "Restore" button on a session card to reopen all windows from that session

4. **Delete Session**: Click the "Delete" button to remove a saved session

## How It Works

- The app uses Windows COM automation (`Shell.Application`) to interact with Explorer windows
- Sessions are saved as JSON files in the `sessions/` directory
- Each session stores:
  - Window paths (folder locations)
  - Window geometry (position and size)
  - Window state (normal, maximized, minimized)
  - Timestamp and metadata



## Notes

- Some special or virtual folders may not restore correctly
- Elevated windows (run as admin) may not be accessible from a non-elevated process
- The app automatically creates the `sessions/` directory if it doesn't exist

## License

Free to use and modify.

## Credits

Built with Python, CustomTkinter, and pywin32.
