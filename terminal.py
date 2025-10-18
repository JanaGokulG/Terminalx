import tkinter as tk

root = tk.Tk()
root.state("zoomed")
root.title("terminal window")
root.configure(bg='black')

# Create the menu first
menu = tk.Menu(root)
root.config(menu=menu)

# Create the appearance submenu
appearancemenu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Appearance", menu=appearancemenu)
appearancemenu.add_command(label='font size')
appearancemenu.add_command(label='font color')
appearancemenu.add_command(label='background color')  # Fixed typo

newterminalmenu=tk.Menu(menu,tearoff=0)
menu.add_cascade(label="New Terminal", menu=newterminalmenu)
newterminalmenu.add_command(label='New Terminal')  
root.mainloop()