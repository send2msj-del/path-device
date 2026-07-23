import os
import sys
import shutil
import winreg
import ctypes
import argparse
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

# Unified paths under Local AppData
LOCAL_APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), "path-manager")
CMD_DIR = os.path.join(LOCAL_APP_DIR, "cmd")
MARKER_FILE = os.path.join(LOCAL_APP_DIR, ".installed")

def clean_path_string(p):
    """Normalizes path strings for strict comparison by stripping extra spacing and slashes."""
    return os.path.normpath(p.strip().rstrip('\\')).lower()

def update_user_path(remove_mode=False):
    """Safely manages the User Environment PATH registry block."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            current_path_raw, data_type = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path_raw = ""
            data_type = winreg.REG_EXPAND_SZ

        path_segments = [seg for seg in current_path_raw.split(";") if seg.strip()]
        target_cleaned = clean_path_string(CMD_DIR)
        
        new_segments = [seg for seg in path_segments if clean_path_string(seg) != target_cleaned]
        
        if not remove_mode:
            new_segments.append(CMD_DIR)
            
        new_path_str = ";".join(new_segments)
        
        if new_path_str:
            winreg.SetValueEx(key, "Path", 0, data_type, new_path_str)
        else:
            try:
                winreg.DeleteValue(key, "Path")
            except FileNotFoundError:
                pass
                
        winreg.CloseKey(key)
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 2, 5000, None)
    except Exception as e:
        print(f"[-] Failed to update environment Registry layout: {e}")
        raise e

def run_passive_setup(target_dir):
    """Architects or repairs the internal storage routing infrastructure cleanly."""
    os.makedirs(CMD_DIR, exist_ok=True)
    
    target_exe_path = os.path.join(target_dir, "path.exe")
    pd_cmd_path = os.path.join(CMD_DIR, "pd.cmd")
    
    source_candidates = [sys.argv[0], sys.executable]
    source_exe = None
    for candidate in source_candidates:
        if candidate and os.path.exists(candidate):
            if os.path.getsize(candidate) > 1024 * 1024:
                source_exe = os.path.abspath(candidate)
                break
    if not source_exe:
        source_exe = os.path.abspath(sys.argv[0] if sys.argv[0] else sys.executable)

    if os.path.exists(target_exe_path):
        try:
            os.remove(target_exe_path)
        except OSError:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Process Lock", "The installation target 'path.exe' is currently locked. Close all apps and try again.")
            root.destroy()
            return

    shutil.copyfile(source_exe, target_exe_path)

    # REENGINEERED: pd.cmd handles help strings natively in the shell, bypassing executable booting
    pd_cmd_content = (
        "@echo off\n"
        'if "%~1"=="-h" goto :print_help\n'
        'if "%~1"=="--help" goto :print_help\n'
        'if "%~1"=="" (\n'
        '    :: No arguments provided -> Spin up GUI silently in background and exit batch\n'
        '    start "" /b "{target_exe_path}" %*\n'
        '    goto :eof\n'
        ") else (\n"
        '    :: Other CLI arguments provided -> Run directly in foreground to catch stdout\n'
        '    "{target_exe_path}" %*\n'
        '    goto :eof\n'
        ")\n\n"
        ":print_help\n"
        "echo.\n"
        "echo PATH Command Manager CLI\n"
        "echo.\n"
        "echo options:\n"
        "echo   -h, --help                        show this help message and exit\n"
        "echo   --uninstall                       completely delete itself and its assets\n"
        "echo   -f [file] [alias] [executioner]   map a file to an alias\n"
        "echo   -a [alias] [string]               map a raw inline string to an alias\n"
        "echo.\n"
        ":eof\n"
    ).format(target_exe_path=target_exe_path)

    with open(pd_cmd_path, "w") as f:
        f.write(pd_cmd_content)

    with open(MARKER_FILE, "w") as f:
        f.write("installation_lock=true\n")

    update_user_path(remove_mode=False)

def run_uninstall():
    """Removes environment paths, configuration bindings, and local application code storage maps."""
    try:
        update_user_path(remove_mode=True)
        if os.path.exists(LOCAL_APP_DIR):
            shutil.rmtree(LOCAL_APP_DIR, ignore_errors=True)
            
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Uninstall Successful", "PATH Command Manager has been completely removed from this system.")
        root.destroy()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Uninstall Failure", f"An error occurred while cleaning components:\n{e}")
        root.destroy()


class SetupWizardApp:
    def __init__(self, root, is_repair=False):
        self.root = root
        self.is_repair = is_repair
        self.root.title("PATH Command Manager Setup" if not is_repair else "PATH Command Manager - Repair")
        self.root.geometry("520x250")
        self.root.resizable(False, False)
        
        title_text = "PATH Command Manager Installation" if not is_repair else "Repair PATH Command Manager"
        tk.Label(root, text=title_text, font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        desc_text = (
            "Select the directory to install the core application binaries:" 
            if not is_repair else 
            "An existing or corrupted installation was detected. Click Repair to restore all components:"
        )
        tk.Label(root, text=desc_text, wraplength=470, justify="left").pack(anchor="w", padx=25)
        
        self.path_frame = tk.Frame(root)
        self.path_frame.pack(fill=tk.X, padx=25, pady=10)
        
        self.path_var = tk.StringVar(value=LOCAL_APP_DIR)
        
        self.entry = tk.Entry(self.path_frame, textvariable=self.path_var, font=("Segoe UI", 10))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.browse_btn = tk.Button(self.path_frame, text="Browse...", command=self.browse_folder)
        self.browse_btn.pack(side=tk.RIGHT)
        
        if self.is_repair:
            self.entry.config(state=tk.DISABLED)
            self.browse_btn.config(state=tk.DISABLED)

        btn_text = "Install & Finish" if not is_repair else "Repair Installation"
        btn_color = "#2ecc71" if not is_repair else "#f39c12"
        
        self.install_btn = tk.Button(root, text=btn_text, bg=btn_color, fg="white", font=("Segoe UI", 11, "bold"), padx=15, pady=5, command=self.execute_installation)
        self.install_btn.pack(side=tk.BOTTOM, pady=20)
        
    def browse_folder(self):
        selected = filedialog.askdirectory(initialdir=self.path_var.get())
        if selected:
            self.path_var.set(os.path.abspath(selected))
            
    def execute_installation(self):
        target_dir = self.path_var.get().strip()
        if not target_dir:
            return
        try:
            os.makedirs(target_dir, exist_ok=True)
            run_passive_setup(target_dir)
            
            success_title = "Installation Complete" if not self.is_repair else "Repair Complete"
            success_msg = "Installation completed successfully.\n\n" if not self.is_repair else "All application components have been successfully restored.\n\n"
            success_msg += "You can now use:\n    pd\nfrom Command Prompt or PowerShell.\n\nIf you already had a terminal open, open a new one to refresh your PATH."
            
            messagebox.showinfo(success_title, success_msg)
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Setup Error", f"Operation failed:\n{e}")


class PathManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PATH Command Manager")
        self.root.geometry("850x550")
        self.current_file = None
        self.known_files = set()
        self.root.configure(bg="#f4f7f6")
        
        self.sidebar = tk.Frame(root, width=220, bg="#2c3e50", padx=10, pady=10)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        sidebar_title = tk.Label(self.sidebar, text="Custom Commands", font=("Segoe UI", 11, "bold"), fg="white", bg="#2c3e50")
        sidebar_title.pack(anchor="w", pady=5)

        self.add_btn = tk.Button(self.sidebar, text="+ New Command", font=("Segoe UI", 9, "bold"), bg="#2ecc71", fg="white", command=self.create_new_command, bd=0, padx=5, pady=5)
        self.add_btn.pack(fill=tk.X, pady=10)

        self.canvas = tk.Canvas(self.sidebar, bg="#2c3e50", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.sidebar, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#2c3e50")

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=200)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_btn = tk.Button(self.sidebar, text="🔄 Refresh List", font=("Segoe UI", 9), bg="#34495e", fg="white", command=lambda: self.refresh_command_sidebar(force=True), bd=0, pady=5)
        self.refresh_btn.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        self.main_content = tk.Frame(root, bg="#f4f7f6", padx=15, pady=15)
        self.main_content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.header_frame = tk.Frame(self.main_content, bg="#f4f7f6")
        self.header_frame.pack(fill=tk.X, anchor="w", pady=5)
        
        self.file_label = tk.Label(self.header_frame, text="Select or Create a Command script to edit", font=("Segoe UI", 12, "bold"), fg="#333", bg="#f4f7f6")
        self.file_label.pack(side=tk.LEFT)
        
        self.rename_btn = tk.Button(self.header_frame, text="Rename", bg="#f39c12", fg="white", font=("Segoe UI", 9, "bold"), padx=5, pady=2, bd=0, command=self.rename_current_file, state=tk.DISABLED)
        self.rename_btn.pack(side=tk.RIGHT, padx=5)

        self.editor = tk.Text(self.main_content, font=("Consolas", 11), wrap="none", bd=1, relief="solid")
        self.editor.pack(fill=tk.BOTH, expand=True, pady=10)

        self.btn_frame = tk.Frame(self.main_content, bg="#f4f7f6")
        self.btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.save_btn = tk.Button(self.btn_frame, text="Save Command", bg="#0056b3", fg="white", font=("Segoe UI", 10, "bold"), padx=6, pady=6, command=self.save_current_file, state=tk.DISABLED)
        self.save_btn.pack(side=tk.RIGHT, padx=5)

        self.delete_btn = tk.Button(self.btn_frame, text="Delete Command", bg="#c0392b", fg="white", font=("Segoe UI", 10, "bold"), padx=6, pady=6, command=self.delete_current_file, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.RIGHT, padx=5)

        self.refresh_command_sidebar(force=True)
        self.start_auto_refresh_loop()

    def refresh_command_sidebar(self, force=False):
        if not os.path.exists(CMD_DIR): 
            return
        current_files_on_disk = {f for f in os.listdir(CMD_DIR) if f.endswith(".cmd") and f != "pd.cmd"}
        if not force and current_files_on_disk == self.known_files:
            return
        self.known_files = current_files_on_disk
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        for filename in sorted(list(self.known_files)):
            btn = tk.Button(
                self.scroll_frame, text=f" {filename.replace('.cmd', '')}", anchor="w", font=("Segoe UI", 10),
                bg="#34495e", fg="white", activebackground="#4e6e8e", activeforeground="white", bd=0, pady=6,
                command=lambda f=filename: self.load_file_into_editor(f)
            )
            btn.pack(fill=tk.X, pady=2)

    def start_auto_refresh_loop(self):
        self.refresh_command_sidebar(force=False)
        self.root.after(4000, self.start_auto_refresh_loop)

    def load_file_into_editor(self, filename):
        self.current_file = os.path.join(CMD_DIR, filename)
        self.file_label.config(text=f"Editing: {filename}")
        self.save_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        self.rename_btn.config(state=tk.NORMAL)
        self.editor.delete("1.0", tk.END)
        with open(self.current_file, "r") as f:
            self.editor.insert("1.0", f.read())

    def create_new_command(self):
        popup = tk.Toplevel(self.root)
        popup.title("New Target Command")
        popup.geometry("300x120")
        popup.resizable(False, False)
        tk.Label(popup, text="Enter Command Name:", font=("Segoe UI", 9)).pack(pady=10)
        entry = tk.Entry(popup, width=30)
        entry.pack()

        def submit():
            name = entry.get().strip().lower().replace(" ", "-")
            if name:
                target_filename = f"{name}.cmd"
                target_path = os.path.join(CMD_DIR, target_filename)
                if os.path.exists(target_path):
                    messagebox.showerror("Error", "Command conflict already exists.")
                else:
                    with open(target_path, "w") as f:
                        f.write("@echo off\necho Custom system macro initiated...\n")
                    popup.destroy()
                    self.refresh_command_sidebar(force=True)
                    self.load_file_into_editor(target_filename)
            else:
                popup.destroy()
        tk.Button(popup, text="Create", command=submit, bg="#2ecc71", fg="white").pack(pady=10)

    def save_current_file(self):
        if self.current_file and os.path.exists(self.current_file):
            try:
                with open(self.current_file, "w") as f:
                    f.write(self.editor.get("1.0", tk.END).strip() + "\n")
                messagebox.showinfo("Success", "Changes saved successfully.")
            except Exception as e:
                messagebox.showerror("Save Failure", str(e))

    def delete_current_file(self):
        if not self.current_file or not os.path.exists(self.current_file): return
        filename = os.path.basename(self.current_file)
        if messagebox.askyesno("Confirm Deletion", f"Completely drop '{filename}'?"):
            try:
                os.remove(self.current_file)
                self.current_file = None
                self.editor.delete("1.0", tk.END)
                self.file_label.config(text="Select or Create a Command script to edit")
                self.save_btn.config(state=tk.DISABLED)
                self.delete_btn.config(state=tk.DISABLED)
                self.rename_btn.config(state=tk.DISABLED)
                self.refresh_command_sidebar(force=True)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def rename_current_file(self):
        if not self.current_file or not os.path.exists(self.current_file): return
        old_filename = os.path.basename(self.current_file)
        old_name = old_filename.replace(".cmd", "")
        popup = tk.Toplevel(self.root)
        popup.title("Rename Command")
        popup.geometry("300x120")
        popup.resizable(False, False)
        tk.Label(popup, text=f"Rename '{old_name}' to:", font=("Segoe UI", 9)).pack(pady=10)
        entry = tk.Entry(popup, width=30)
        entry.insert(0, old_name)
        entry.pack()

        def submit():
            new_name = entry.get().strip().lower().replace(" ", "-")
            if new_name and new_name != old_name:
                new_filename = f"{new_name}.cmd"
                new_path = os.path.join(CMD_DIR, new_filename)
                if os.path.exists(new_path):
                    messagebox.showerror("Error", "Command name already exists.")
                else:
                    try:
                        os.rename(self.current_file, new_path)
                        popup.destroy()
                        self.refresh_command_sidebar(force=True)
                        self.load_file_into_editor(new_filename)
                    except Exception as e:
                        messagebox.showerror("Error", str(e))
            else:
                popup.destroy()
        tk.Button(popup, text="Rename", command=submit, bg="#f39c12", fg="white").pack(pady=10)


def create_cli_alias(macro_value, name, executor=None):
    os.makedirs(CMD_DIR, exist_ok=True)
    target_path = os.path.join(CMD_DIR, f"{name.lower().strip()}.cmd")
    script_content = f"@echo off\n{executor} \"{macro_value}\" %*\n" if executor else f"@echo off\n{macro_value} %*\n"
    with open(target_path, "w") as f:
        f.write(script_content)


def main():
    parser = argparse.ArgumentParser(description="PATH Command Manager CLI", add_help=False)
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-f", "--file", nargs='+', metavar="ARGS")
    parser.add_argument("-a", "--alias", nargs='+', metavar="ARGS")

    args, unknown = parser.parse_known_args()
    
    has_cli_flags = any([args.help, args.uninstall, args.file, args.alias])

    if has_cli_flags:
        # ATTACH ENHANCEMENT: Try attaching to parent process window (-1).
        # If that fails, manually look up the current active foreground console engine handle.
        attached = ctypes.windll.kernel32.AttachConsole(-1)
        if not attached:
            attached = ctypes.windll.kernel32.AllocConsole()

        if attached:
            stdout_handle = ctypes.windll.kernel32.GetStdHandle(-11)
            
            if args.uninstall:
                msg = "\n[*] Purging system tracking signatures...\n"
                ctypes.windll.kernel32.WriteConsoleW(stdout_handle, msg, len(msg), None, None)
                run_uninstall()
                sys.exit(0)

            if args.help:
                help_text = "\n" + parser.format_help() + "\n"
                ctypes.windll.kernel32.WriteConsoleW(stdout_handle, help_text, len(help_text), None, None)
                ctypes.windll.kernel32.WriteConsoleW(stdout_handle, "\r\n", 2, None, None)
                sys.exit(0)
                
            if args.file:
                if len(args.file) < 2: sys.exit(1)
                create_cli_alias(args.file[0], args.file[1], args.file[2] if len(args.file) > 2 else None)
                msg = f"[+] Alias mapped successfully: '{args.file[1]}'\n"
                ctypes.windll.kernel32.WriteConsoleW(stdout_handle, msg, len(msg), None, None)
                sys.exit(0)

            if args.alias:
                if len(args.alias) < 2: sys.exit(1)
                create_cli_alias(args.alias[0], args.alias[1])
                msg = f"[+] Alias mapped successfully: '{args.alias[1]}'\n"
                ctypes.windll.kernel32.WriteConsoleW(stdout_handle, msg, len(msg), None, None)
                sys.exit(0)

    has_exe = os.path.exists(os.path.join(LOCAL_APP_DIR, "path.exe"))
    has_marker = os.path.exists(MARKER_FILE)
    has_cmd = os.path.exists(os.path.join(CMD_DIR, "pd.cmd"))
    
    is_healthy_install = has_exe and has_marker and has_cmd
    is_corrupted = (has_exe or has_marker or has_cmd) and not is_healthy_install

    if getattr(sys, 'frozen', False):
        if not is_healthy_install:
            root = tk.Tk()
            app = SetupWizardApp(root, is_repair=is_corrupted)
            root.mainloop()
            sys.exit(0)

    root = tk.Tk()
    app = PathManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
