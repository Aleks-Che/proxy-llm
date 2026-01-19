#!/usr/bin/env python3

import tkinter as tk
from gui import ProxyGUI
from server import app

if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyGUI(root)
    root.mainloop()