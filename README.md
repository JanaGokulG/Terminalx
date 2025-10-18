# Terminal X

A **custom terminal emulator** built in **Python** using **Tkinter**, inspired by Linux terminals. It allows you to execute shell commands, navigate command history, and customize appearance, all in a GUI window on your own machine.

---

## Features

- Fully functional terminal interface in **Tkinter**.
- Supports **custom commands**.
- Execute any **system shell commands**.
- **Command history** navigation with `Up` and `Down` arrow keys.
- **Restrict prompt deletion** – prevents accidental deletion of terminal prompt.
- Customizable **font size**, **font color**, and **background color**.
- Menu options for terminal appearance and management (New, Reset, Close).

---

## Custom Commands

| Command      | Description                         |
|-------------|-------------------------------------|
| `whoami`    | Display the current username        |
| `hostname-I`| Display the IP address of the machine |
| `about`     | Information about the terminal      |
| `date`      | Display the current date            |
| `time`      | Display the current time            |
| `machine`   | Display the hostname of the machine |
| `help`      | Show this help message              |
| `clear`     | Clear the terminal screen           |
| `exit`      | Close the terminal application      |

---

## steps to be followed

```bash
git clone https://github.com/your-username/terminal-x.git
cd terminal-x
pip install pillow
python terminal.py
