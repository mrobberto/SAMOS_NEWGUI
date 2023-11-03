from tkinter import *
from tkinter import messagebox

""" called by samos_new_xxx.py
> help_menu.add_command(label="About", command=U.about)
"""

def about():
    messagebox.showinfo('About', "This is a sample Application")