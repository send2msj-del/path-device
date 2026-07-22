# PATH Command Manager (`pd`)

A lightweight, zero-dependency Windows utility for managing custom terminal aliases and system scripts with automatic `PATH` registry integration.

---

## ⚡ Key Features

* **GUI Script Editor:** Built-in editor to create, rename, and manage custom command scripts (`.cmd`).
* **CLI Quick Aliasing:** Instantly map commands or scripts to short aliases from any terminal.
* **Auto PATH Configuration:** Seamlessly updates User Environment `PATH` (no admin rights needed).
* **Zero External Dependencies:** Built entirely with Python's standard library (`tkinter`, `winreg`, `ctypes`).
* **Clean Installer & Uninstaller:** Built-in setup wizard, repair tool, and complete `--uninstall` purge.

---

## 🚀 Quick Start

1. Run `path.exe`.
2. Follow the prompt to complete the one-click setup.
3. Open a **new terminal** and run `pd` to open the manager.

---

## 💻 CLI Usage

| Action | Command | Description |
| :--- | :--- | :--- |
| **Open GUI** | `pd` | Opens the interactive visual editor |
| **Map Command** | `pd -a "echo Hello!" hello` | Creates a fast alias `hello` |
| **Map File** | `pd -f "C:\script.py" runscript python` | Maps script to `runscript` using Python |
| **Help** | `pd -h` | Shows command options |
| **Uninstall** | `pd --uninstall` | Fully removes app & updates `PATH` |

---

## 📁 File Structure

```text
%LOCALAPPDATA%\path-manager\
├── path.exe           # Core binary
├── .installed         # Installation marker
└── cmd\               # Added to User PATH
    ├── pd.cmd         # Terminal wrapper
    └── <your-scripts>.cmd