import tkinter as tk
from tkinter import font, colorchooser
import subprocess
import os
import getpass
import socket
import datetime as dt
import threading
import platform
import subprocess

# Main application window
root = tk.Tk()
root.deiconify()  # Show main window after splash
root.iconphoto(False, tk.PhotoImage(file="logo.png"))  # Set logo
root.state("zoomed")
root.title("Terminal X")
root.configure(bg='black')
logo=tk.PhotoImage(file='logo.png')
root.iconphoto(False,logo)

# Terminal font and colors
terminal_font = font.Font(family='Consolas', size=12)
font_color = 'white'
bg_color = 'black'

# Terminal Text widget
terminal = tk.Text(root, bg=bg_color, fg=font_color, insertbackground="white", font=terminal_font)
terminal.pack(fill=tk.BOTH, expand=True)

# Scrollbar
scrollbar = tk.Scrollbar(terminal)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
terminal.configure(yscrollcommand=scrollbar.set)
scrollbar.configure(command=terminal.yview)

# Username, hostname, IP
username = getpass.getuser()
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Tags for colored prompt
terminal.tag_config("username", foreground="green", font=("Consolas", 12, "bold"))
terminal.tag_config("hostname", foreground="cyan", font=("Consolas", 12, "bold"))
terminal.tag_config("symbol", foreground="yellow", font=("Consolas", 12, "bold"))

# Command history
history = []
history_index = -1

# Function to insert prompt
def insert_prompt():
    if not terminal.winfo_exists():
        return
    terminal.insert(tk.END, username, "username")
    terminal.insert(tk.END, "@", "symbol")
    terminal.insert(tk.END, hostname, "hostname")
    terminal.insert(tk.END, f":{ip_address}$ ", "symbol")
    terminal.mark_set("prompt_start", "insert") 
    terminal.mark_gravity("prompt_start", tk.LEFT)
    terminal.mark_set("insert", tk.END)
    terminal.see(tk.END)

# Custom commands
custom_commands = {
    'whoami': username,
    'hostname-I': ip_address,
    'about': 'Terminal developed by Jana Gokul G',
    'date': str(dt.datetime.now().date()),
    'time': str(dt.datetime.now().time().strftime("%H:%M:%S")),
    'machine':hostname
}

# Insert initial prompt
insert_prompt()

def restrict_backspace(event):
    cursor_index = terminal.index(tk.INSERT)
    prompt_index = terminal.index("prompt_start")
    if terminal.compare(cursor_index, "<=", prompt_index):
        return "break"
    
terminal.bind('<BackSpace>', restrict_backspace)
# Execute commands
def execute_command(event):
    global history_index
    linestart = 'insert linestart'
    lineend = 'insert lineend'
    full_line = terminal.get(linestart, lineend).strip()
    
    # Remove prompt from command
    prompt_len = len(f"{username}@{hostname}:{ip_address}$ ")
    command = full_line[prompt_len:]

    if command:
        history.append(command)
    history_index = -1  # Reset history index

    # Handle clear/reset separately
    if command == 'clear':
        reset_terminal()  # This already inserts a prompt
        return 'break'
    elif command == 'exit':
        close_terminal()
        return 'break'

    # Handle custom commands
    if command in custom_commands:
        terminal.insert(tk.END, '\n' + custom_commands[command] + '\n')
        insert_prompt()
        return 'break'
    
    # Handle help
    elif command == 'help':
        help_text = (
            "whoami - Display the current username\n"
            "hostname-I - Display the IP address of the machine\n"
            "about - Information about the terminal\n"
            "date - Display the current date\n"
            "time - Display the current time\n"
            "help - Show this help message\n"
            "clear - Clear the terminal screen\n"
            "exit - Close the terminal application\n"
            "machine - Display the hostname of the machine"
        )
        terminal.insert(tk.END, '\n' + (help_text) + '\n')
        insert_prompt()
        return 'break'

    # Execute other shell commands
    else:
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output
        except Exception as e:
            output = str(e)
        terminal.insert(tk.END, '\n' + output + '\n')
        insert_prompt()
        return 'break'

# Navigate command history
def navigate_history(event):
    global history_index
    if not history:
        return 'break'  # Nothing to do

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
                terminal.delete('insert linestart', 'insert lineend')
                insert_prompt()
                return 'break'
    else:
        return

    # Replace line with prompt + history command
    terminal.delete('insert linestart', 'insert lineend')
    insert_prompt()
    if history_index != -1:
        terminal.insert(tk.END, history[history_index])
    return 'break'

# Bind keys
terminal.bind('<Return>', execute_command)
terminal.bind('<Up>', navigate_history)
terminal.bind('<Down>', navigate_history)
# Terminal menu functions
def font_size():
    sizes = [8,10,12,14,16,18,20,24,28,32,36,40,44,48]
    size_window = tk.Toplevel(root)
    size_window.title("Select Font Size")
    size_window.geometry("200x150")
    size_window.configure(bg='lightgrey')
    
    tk.Label(size_window, text="Select Font Size", bg='lightgrey', fg='white').pack(pady=10)
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

def new_terminal():
    terminal.delete(1.0, tk.END)
    insert_prompt()

def close_terminal():
    root.destroy()

def reset_terminal():
    if terminal.winfo_exists():
        terminal.delete(1.0, tk.END)
        terminal.configure(bg='black', fg='white')
        terminal_font.configure(size=12)
    insert_prompt()

# Create menu
menu = tk.Menu(root)
root.config(menu=menu)

appearancemenu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Appearance", menu=appearancemenu)
appearancemenu.add_command(label='Font size', command=font_size)
appearancemenu.add_command(label='Font color', command=font_color_change)
appearancemenu.add_command(label='Background color', command=bg_color_change)

newterminalmenu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Terminal", menu=newterminalmenu)
newterminalmenu.add_command(label='New Terminal', command=new_terminal)
newterminalmenu.add_command(label='Close Terminal', command=close_terminal)
newterminalmenu.add_command(label='Reset Terminal', command=reset_terminal)

if __name__ == '__main__':
    root.mainloop()
