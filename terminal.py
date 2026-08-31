import tkinter as tk
from tkinter import font, colorchooser
import subprocess
import os
import getpass
import socket
import datetime as dt
import threading
import platform
import queue

# Predefined terminal theme profiles
THEMES = {
    "Classic Dark": {
        "bg": "#0c0c0c",
        "fg": "#ffffff",
        "insert": "#ffffff",
        "username": "#22c55e",  # Green
        "hostname": "#06b6d4",  # Cyan
        "symbol": "#eab308",  # Yellow
        "directory": "#3b82f6",  # Blue
    },
    "Matrix": {
        "bg": "#000000",
        "fg": "#00ff00",
        "insert": "#00ff00",
        "username": "#00ff00",
        "hostname": "#00ff00",
        "symbol": "#00cc00",
        "directory": "#00ee00",
    },
    "Cyberpunk": {
        "bg": "#120422",  # Dark purple
        "fg": "#00ffff",  # Cyan
        "insert": "#ff007f",  # Hot pink
        "username": "#ff007f",
        "hostname": "#00ffff",
        "symbol": "#f39c12",
        "directory": "#9b59b6",
    },
    "One Dark": {
        "bg": "#282c34",
        "fg": "#abb2bf",
        "insert": "#528bff",
        "username": "#98c379",  # Soft green
        "hostname": "#56b6c2",  # Soft cyan
        "symbol": "#d19a66",  # Soft orange
        "directory": "#61afef",  # Soft blue
    },
    "Solarized Dark": {
        "bg": "#002b36",
        "fg": "#839496",
        "insert": "#839496",
        "username": "#859900",  # Olive green
        "hostname": "#2aa198",  # Cyan/Teal
        "symbol": "#b58900",  # Yellow/Gold
        "directory": "#268bd2",  # Blue
    },
    "Light Theme": {
        "bg": "#f3f4f6",
        "fg": "#111827",
        "insert": "#111827",
        "username": "#16a34a",
        "hostname": "#0891b2",
        "symbol": "#ca8a04",
        "directory": "#2563eb",
    }
}

# Main application window
root = tk.Tk()
root.deiconify()  # Show main window after splash
try:
    logo = tk.PhotoImage(file='logo.png')
    root.iconphoto(False, logo)
except Exception:
    pass
root.state("zoomed")
root.title("Terminal X")
root.configure(bg='black')

# Terminal font and colors
terminal_font = font.Font(family='Consolas', size=12)
font_color = 'white'
bg_color = 'black'

# Create a frame to hold terminal text and its scrollbar
terminal_frame = tk.Frame(root, bg=bg_color)
terminal_frame.pack(fill=tk.BOTH, expand=True)

# Terminal Text widget
terminal = tk.Text(terminal_frame, bg=bg_color, fg=font_color, insertbackground="white", font=terminal_font, undo=True)
terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Scrollbar
scrollbar = tk.Scrollbar(terminal_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
terminal.configure(yscrollcommand=scrollbar.set)
scrollbar.configure(command=terminal.yview)

# Username, hostname, IP
username = getpass.getuser()
hostname = socket.gethostname()
try:
    ip_address = socket.gethostbyname(hostname)
except Exception:
    ip_address = "127.0.0.1"

# Tags for colored prompt and search highlights
terminal.tag_config("username", foreground="green", font=("Consolas", 12, "bold"))
terminal.tag_config("hostname", foreground="cyan", font=("Consolas", 12, "bold"))
terminal.tag_config("symbol", foreground="yellow", font=("Consolas", 12, "bold"))
terminal.tag_config("directory", foreground="#3b82f6", font=("Consolas", 12, "bold"))
terminal.tag_config("search_highlight", background="#ca8a04", foreground="black")
terminal.tag_config("search_active_match", background="#22c55e", foreground="black")

# State tracking variables
history = []
history_index = -1
current_dir = os.getcwd()
previous_dir = os.getcwd()

is_running_command = False
current_process = None
output_queue = queue.Queue()

# Function to insert prompt
def insert_prompt():
    if not terminal.winfo_exists():
        return
    terminal.insert(tk.END, username, "username")
    terminal.insert(tk.END, "@", "symbol")
    terminal.insert(tk.END, hostname, "hostname")
    terminal.insert(tk.END, ":", "symbol")
    
    # Format path, replace home with ~
    home = os.path.expanduser("~")
    display_dir = current_dir
    if display_dir.startswith(home):
        display_dir = display_dir.replace(home, "~", 1)
        
    terminal.insert(tk.END, display_dir, "directory")
    terminal.insert(tk.END, "$ ", "symbol")
    
    terminal.mark_set("prompt_start", "insert") 
    terminal.mark_gravity("prompt_start", tk.LEFT)
    terminal.mark_set("insert", tk.END)
    terminal.see(tk.END)

# Custom commands dictionary
custom_commands = {
    'whoami': username,
    'hostname-I': ip_address,
    'about': 'Terminal developed by Jana Gokul G',
    'date': str(dt.datetime.now().date()),
    'time': str(dt.datetime.now().time().strftime("%H:%M:%S")),
    'machine': hostname
}

# Insert initial prompt
insert_prompt()

# Directory management function
def change_directory(target_dir):
    global current_dir, previous_dir
    if not target_dir:
        target_dir = os.path.expanduser("~")
    elif target_dir == "-":
        target_dir = previous_dir
        
    target_dir = os.path.expandvars(target_dir)
    target_dir = os.path.expanduser(target_dir)
    
    try:
        new_dir = os.path.abspath(target_dir)
        if os.path.exists(new_dir) and os.path.isdir(new_dir):
            os.chdir(new_dir)
            previous_dir = current_dir
            current_dir = new_dir
        else:
            terminal.insert(tk.END, f"cd: no such file or directory: {target_dir}\n")
    except Exception as e:
        terminal.insert(tk.END, f"cd: error: {e}\n")

# Interrupt process using Ctrl+C
def interrupt_process():
    global current_process
    if current_process and current_process.poll() is None:
        try:
            current_process.terminate()
        except Exception:
            pass
        terminal.insert(tk.END, "^C\n")
        terminal.see(tk.END)

# Restrict keys and lock historical prompt
def check_readonly(event):
    global is_running_command
    
    # 1. Allow modifier keys and navigation
    if event.keysym in ("Up", "Down", "Left", "Right", "Prior", "Next", "Home", "End",
                        "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
                        "Caps_Lock", "Num_Lock"):
        return None
        
    # 2. Handle Ctrl bindings
    ctrl_pressed = (event.state & 0x4) != 0
    shift_pressed = (event.state & 0x1) != 0
    
    if ctrl_pressed:
        key = event.keysym.lower()
        if key == 'c':
            if is_running_command:
                interrupt_process()
                return "break"
            else:
                try:
                    selected = terminal.get(tk.SEL_FIRST, tk.SEL_LAST)
                    return None  # Let standard copy run
                except tk.TclError:
                    terminal.insert(tk.END, "^C\n")
                    insert_prompt()
                    return "break"
        elif key == 'v' and shift_pressed:
            if not is_running_command:
                paste_text()
            return "break"
            
    # 3. Block keyboard modifications when command is running
    if is_running_command:
        return "break"
        
    # 4. Handle Backspace at/before prompt start
    if event.keysym == "BackSpace":
        if terminal.compare(tk.INSERT, "<=", "prompt_start"):
            return "break"
        try:
            if terminal.compare(tk.SEL_FIRST, "<", "prompt_start"):
                return "break"
        except tk.TclError:
            pass
        return None
        
    # 5. Prevent modification if cursor is before prompt
    if terminal.compare(tk.INSERT, "<", "prompt_start"):
        return "break"
    try:
        if terminal.compare(tk.SEL_FIRST, "<", "prompt_start"):
            return "break"
    except tk.TclError:
        pass
        
    return None

# Bind keypress validation
terminal.bind('<KeyPress>', check_readonly)

# Execute command
def execute_command(event):
    global history_index, is_running_command, current_process
    
    if is_running_command:
        return 'break'
        
    command = terminal.get("prompt_start", "insert lineend").strip()
    
    if command:
        if not history or history[-1] != command:
            history.append(command)
    history_index = -1
    
    terminal.insert(tk.END, '\n')
    
    # Built-in terminal commands
    if command == 'clear':
        reset_terminal()
        return 'break'
    elif command == 'exit':
        close_terminal()
        return 'break'
        
    # Directory navigation cd
    if command.startswith('cd ') or command == 'cd':
        parts = command.split(' ', 1)
        target = parts[1].strip() if len(parts) > 1 else ""
        change_directory(target)
        insert_prompt()
        return 'break'
        
    # Theme selection
    if command.startswith('theme '):
        parts = command.split(' ', 1)
        theme_name = parts[1].strip()
        matched_theme = None
        for k in THEMES:
            if k.lower() == theme_name.lower():
                matched_theme = k
                break
        if matched_theme:
            apply_theme(matched_theme)
            terminal.insert(tk.END, f"Theme changed to {matched_theme}\n")
        else:
            terminal.insert(tk.END, f"Unknown theme. Available: {', '.join(THEMES.keys())}\n")
        insert_prompt()
        return 'break'
        
    # Custom commands
    if command in custom_commands:
        terminal.insert(tk.END, custom_commands[command] + '\n')
        insert_prompt()
        return 'break'
        
    # Help message
    if command == 'help':
        help_text = (
            "whoami      - Display the current username\n"
            "hostname-I  - Display the IP address of the machine\n"
            "about       - Information about the terminal\n"
            "date        - Display the current date\n"
            "time        - Display the current time\n"
            "machine     - Display the hostname of the machine\n"
            "cd [dir]    - Change working directory\n"
            "theme [name]- Change color theme\n"
            "help        - Show this help message\n"
            "clear       - Clear the terminal screen\n"
            "exit        - Close the terminal application"
        )
        terminal.insert(tk.END, help_text + '\n')
        insert_prompt()
        return 'break'
        
    # Asynchronous command execution
    is_running_command = True
    
    def run_thread():
        global current_process
        try:
            current_process = subprocess.Popen(
                command,
                shell=True,
                cwd=current_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            # Read output in real-time
            for line in iter(current_process.stdout.readline, ''):
                output_queue.put(('output', line))
                
            current_process.stdout.close()
            return_code = current_process.wait()
            output_queue.put(('finished', return_code))
        except Exception as e:
            output_queue.put(('error', str(e)))
            
    threading.Thread(target=run_thread, daemon=True).start()
    return 'break'

# Copy / paste utility
def copy_text(event=None):
    try:
        selected = terminal.get(tk.SEL_FIRST, tk.SEL_LAST)
        root.clipboard_clear()
        root.clipboard_append(selected)
    except tk.TclError:
        pass
    return "break"

def paste_text(event=None):
    global is_running_command
    if is_running_command:
        return "break"
    try:
        pasted = root.clipboard_get()
        if terminal.compare(tk.INSERT, "<", "prompt_start"):
            terminal.mark_set("insert", tk.END)
        terminal.insert(tk.INSERT, pasted)
        terminal.see(tk.END)
    except tk.TclError:
        pass
    return "break"

# Bind Copy/Paste shortcuts
terminal.bind('<Control-Shift-c>', copy_text)
terminal.bind('<Control-Shift-C>', copy_text)
terminal.bind('<Control-Shift-v>', paste_text)
terminal.bind('<Control-Shift-V>', paste_text)

# Queue Polling Loop
def poll_queue():
    global is_running_command
    while not output_queue.empty():
        msg_type, val = output_queue.get()
        if msg_type == 'output':
            if terminal.winfo_exists():
                terminal.insert(tk.END, val)
                terminal.see(tk.END)
        elif msg_type == 'finished' or msg_type == 'error':
            if msg_type == 'error':
                if terminal.winfo_exists():
                    terminal.insert(tk.END, f"Error: {val}\n")
            is_running_command = False
            if terminal.winfo_exists():
                insert_prompt()
    root.after(50, poll_queue)

# Start polling
root.after(50, poll_queue)

# Autocomplete (Tab key)
autocomplete_matches = []
autocomplete_index = 0
autocomplete_last_word = ""

def autocomplete(event):
    global autocomplete_matches, autocomplete_index, autocomplete_last_word
    
    if is_running_command:
        return "break"
        
    command_typed = terminal.get("prompt_start", "insert")
    if not command_typed:
        return "break"
        
    # Check if we are cycling through existing matches
    if autocomplete_matches:
        last_match = autocomplete_matches[autocomplete_index]
        if os.path.isdir(os.path.join(current_dir, last_match)) and not last_match.endswith("/"):
            last_match_disp = last_match + "/"
        else:
            last_match_disp = last_match
            
        if command_typed.endswith(last_match_disp):
            # Delete old completed text and insert next match
            insert_pos = terminal.index("insert")
            start_pos = f"{insert_pos} - {len(last_match_disp)} chars"
            terminal.delete(start_pos, "insert")
            
            autocomplete_index = (autocomplete_index + 1) % len(autocomplete_matches)
            new_match = autocomplete_matches[autocomplete_index]
            
            if os.path.isdir(os.path.join(current_dir, new_match)):
                new_match += "/"
                
            terminal.insert("insert", new_match)
            terminal.see(tk.END)
            return "break"
            
    # Calculate last typed word
    parts = command_typed.split()
    if not parts:
        return "break"
    last_word = parts[-1]
    
    matches = []
    
    # Check built-in names
    all_cmds = list(custom_commands.keys()) + ['clear', 'exit', 'help', 'cd', 'theme']
    for cmd in all_cmds:
        if cmd.startswith(last_word):
            matches.append(cmd)
            
    # Check directory items
    try:
        head, tail = os.path.split(last_word)
        search_dir = os.path.join(current_dir, head) if head else current_dir
        if os.path.exists(search_dir) and os.path.isdir(search_dir):
            for item in os.listdir(search_dir):
                if item.startswith(tail):
                    full_path = os.path.join(head, item) if head else item
                    matches.append(full_path.replace("\\", "/"))
    except Exception:
        pass
        
    if not matches:
        return "break"
        
    autocomplete_matches = sorted(list(set(matches)))
    autocomplete_index = 0
    autocomplete_last_word = last_word
    
    insert_pos = terminal.index("insert")
    start_pos = f"{insert_pos} - {len(last_word)} chars"
    terminal.delete(start_pos, "insert")
    
    first_match = autocomplete_matches[0]
    if os.path.isdir(os.path.join(current_dir, first_match)):
        first_match += "/"
        
    terminal.insert("insert", first_match)
    terminal.see(tk.END)
    return "break"

# Bind Tab key
terminal.bind('<Tab>', autocomplete)

# Navigate history
def navigate_history(event):
    global history_index
    if not history:
        return 'break'

    if event.keysym == "Up":
        if history_index == -1:
            history_index = len(history) - 1
        elif history_index > 0:
            history_index -= 1
    elif event.keysym == "Down":
        if history_index != -1:
            history_index += 1
            if history_index >= len(history):
                history_index = -1
                terminal.delete('prompt_start', 'insert lineend')
                return 'break'
    else:
        return

    # Delete current input and replace with history command
    terminal.delete('prompt_start', 'insert lineend')
    if history_index != -1:
        terminal.insert(tk.END, history[history_index])
    return 'break'

# Bind navigation keys
terminal.bind('<Return>', execute_command)
terminal.bind('<Up>', navigate_history)
terminal.bind('<Down>', navigate_history)

# Find/Search UI Overlay
search_active = False
current_search_match_idx = 0
search_matches = []

search_frame = tk.Frame(root, bg="#1e1e1e", bd=1, relief=tk.RIDGE)

tk.Label(search_frame, text="Find:", bg="#1e1e1e", fg="white", font=("Consolas", 10)).pack(side=tk.LEFT, padx=5)

search_entry = tk.Entry(search_frame, bg="#2d2d2d", fg="white", insertbackground="white", font=("Consolas", 10), width=30)
search_entry.pack(side=tk.LEFT, padx=5, pady=5)

search_status = tk.Label(search_frame, text="", bg="#1e1e1e", fg="gray", font=("Consolas", 9))
search_status.pack(side=tk.LEFT, padx=10)

def search_text_change(event=None):
    global current_search_match_idx, search_matches
    query = search_entry.get()
    terminal.tag_remove("search_highlight", "1.0", tk.END)
    terminal.tag_remove("search_active_match", "1.0", tk.END)
    
    if not query:
        search_status.config(text="", fg="gray")
        search_matches = []
        current_search_match_idx = 0
        return
        
    start = "1.0"
    search_matches = []
    while True:
        pos = terminal.search(query, start, stopindex=tk.END, nocase=True)
        if not pos:
            break
        search_matches.append(pos)
        start = f"{pos} + {len(query)} chars"
        
    if not search_matches:
        search_status.config(text="0 matches", fg="#ef4444")
        return
        
    for pos in search_matches:
        end_pos = f"{pos} + {len(query)} chars"
        terminal.tag_add("search_highlight", pos, end_pos)
        
    current_search_match_idx = 0
    show_active_search_match()

def show_active_search_match():
    global current_search_match_idx, search_matches
    if not search_matches:
        return
        
    query = search_entry.get()
    terminal.tag_remove("search_active_match", "1.0", tk.END)
    
    pos = search_matches[current_search_match_idx]
    end_pos = f"{pos} + {len(query)} chars"
    terminal.tag_add("search_active_match", pos, end_pos)
    
    terminal.see(pos)
    search_status.config(text=f"{current_search_match_idx + 1}/{len(search_matches)} matches", fg="#22c55e")

def search_next(event=None):
    global current_search_match_idx, search_matches
    if not search_matches:
        return
    current_search_match_idx = (current_search_match_idx + 1) % len(search_matches)
    show_active_search_match()

def search_prev(event=None):
    global current_search_match_idx, search_matches
    if not search_matches:
        return
    current_search_match_idx = (current_search_match_idx - 1) % len(search_matches)
    show_active_search_match()

search_entry.bind("<KeyRelease>", search_text_change)
search_entry.bind("<Return>", search_next)

btn_prev = tk.Button(search_frame, text="▲", command=search_prev, bg="#333333", fg="white", relief=tk.FLAT, bd=0, padx=5, activebackground="#444444", activeforeground="white")
btn_prev.pack(side=tk.LEFT, padx=2)

btn_next = tk.Button(search_frame, text="▼", command=search_next, bg="#333333", fg="white", relief=tk.FLAT, bd=0, padx=5, activebackground="#444444", activeforeground="white")
btn_next.pack(side=tk.LEFT, padx=2)

def toggle_search(event=None):
    global search_active
    if not search_active:
        search_frame.pack(side=tk.BOTTOM, fill=tk.X)
        search_entry.focus_set()
        search_entry.select_range(0, tk.END)
        search_active = True
        search_text_change()
    else:
        search_frame.pack_forget()
        terminal.tag_remove("search_highlight", "1.0", tk.END)
        terminal.tag_remove("search_active_match", "1.0", tk.END)
        terminal.focus_set()
        search_active = False
    return "break"

btn_close = tk.Button(search_frame, text="✕", command=toggle_search, bg="#1e1e1e", fg="gray", relief=tk.FLAT, bd=0, activebackground="#1e1e1e", activeforeground="white")
btn_close.pack(side=tk.RIGHT, padx=5)

terminal.bind("<Control-f>", toggle_search)
terminal.bind("<Control-F>", toggle_search)
search_entry.bind("<Escape>", toggle_search)

# Appearance functions
def font_size():
    sizes = [8,10,12,14,16,18,20,24,28,32,36,40,44,48]
    size_window = tk.Toplevel(root)
    size_window.title("Select Font Size")
    size_window.geometry("200x150")
    size_window.configure(bg='lightgrey')
    
    tk.Label(size_window, text="Select Font Size", bg='lightgrey', fg='black').pack(pady=10)
    selected_size = tk.IntVar(value=terminal_font['size'])
    tk.OptionMenu(size_window, selected_size, *sizes).pack(pady=10)
    
    def apply_size():
        terminal_font.configure(size=selected_size.get())
        size_window.destroy()
    tk.Button(size_window, text="Apply", command=apply_size, bg='white').pack(pady=10)

def font_color_change():
    global font_color
    colour = colorchooser.askcolor(title="Choose font color")
    if colour[1]:
        font_color = colour[1]
        terminal.configure(fg=font_color)

def bg_color_change():
    global bg_color
    colour = colorchooser.askcolor(title="Choose background color")
    if colour[1]:
        bg_color = colour[1]
        terminal.configure(bg=bg_color)
        terminal.configure(insertbackground=font_color)

def apply_theme(theme_name):
    theme = THEMES[theme_name]
    terminal.configure(bg=theme["bg"], fg=theme["fg"], insertbackground=theme["insert"])
    terminal.tag_config("username", foreground=theme["username"])
    terminal.tag_config("hostname", foreground=theme["hostname"])
    terminal.tag_config("symbol", foreground=theme["symbol"])
    terminal.tag_config("directory", foreground=theme["directory"])
    terminal_frame.configure(bg=theme["bg"])

def new_terminal():
    terminal.delete(1.0, tk.END)
    insert_prompt()

def close_terminal():
    global current_process
    if current_process and current_process.poll() is None:
        try:
            current_process.terminate()
        except Exception:
            pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_terminal)

def reset_terminal():
    global current_dir, previous_dir, is_running_command
    if terminal.winfo_exists():
        terminal.delete(1.0, tk.END)
        is_running_command = False
        current_dir = os.getcwd()
        previous_dir = os.getcwd()
        apply_theme("Classic Dark")
        terminal_font.configure(size=12)
        terminal.tag_remove("search_highlight", "1.0", tk.END)
        terminal.tag_remove("search_active_match", "1.0", tk.END)
        if search_active:
            toggle_search()
    insert_prompt()

# Menus creation
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

appearancemenu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Appearance", menu=appearancemenu)
appearancemenu.add_command(label='Font size', command=font_size)
appearancemenu.add_command(label='Font color', command=font_color_change)
appearancemenu.add_command(label='Background color', command=bg_color_change)

# Themes cascade
themesmenu = tk.Menu(appearancemenu, tearoff=0)
appearancemenu.add_cascade(label="Themes", menu=themesmenu)
for t_name in THEMES:
    themesmenu.add_command(label=t_name, command=lambda name=t_name: apply_theme(name))

newterminalmenu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Terminal", menu=newterminalmenu)
newterminalmenu.add_command(label='New Terminal', command=new_terminal)
newterminalmenu.add_command(label='Close Terminal', command=close_terminal)
newterminalmenu.add_command(label='Reset Terminal', command=reset_terminal)

if __name__ == '__main__':
    root.mainloop()
