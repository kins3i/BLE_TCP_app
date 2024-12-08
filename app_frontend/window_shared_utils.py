# -*- coding: utf-8 -*-
""" Set shared parameters of window. """

def set_geometry(obj, w, h):
    """ Set customtkinter window geometry. """

    ws = obj.winfo_screenwidth()
    hs = obj.winfo_screenheight()

    x = int((ws / 2) - (w / 2))
    y = int((hs / 2) - (h / 2))

    obj.geometry(f"{w}x{h}+{x}+{y}")
    obj.minsize(w, h)

def set_style(obj, size: int):
    """ Sets style to customtkinter object. """

    desired_font = ("Arial", size, "normal")

    obj.configure(height=1,
                  corner_radius=0,
                  wrap='word',
                  spacing1=5,
                  spacing3=5,
                  font=desired_font)


def redirector(obj, input_str):
    """ Sets text to textbox. """

    obj.insert('end', input_str)
