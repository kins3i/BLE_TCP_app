# -*- coding: utf-8 -*-
""" Class for creating waiting window. """

import customtkinter

from app_frontend.window_shared_utils import set_geometry


class ToplevelWindow(customtkinter.CTkToplevel):
    """ Class for creating window when main window is busy. """

    def __init__(self):
        super().__init__()
        w = 400
        h = 200

        set_geometry(self, w, h)

        self.title("Waiter")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.label = customtkinter.CTkLabel(self, text="",
                                            justify="center",
                                            font=("Arial", 16, "bold"),
                                            anchor="center", )
        self.label.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
