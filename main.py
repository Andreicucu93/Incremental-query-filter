import tkinter as tk
from tkinter import ttk
import pyperclip
import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps
import shutil, os

root = ctk.CTk()
root.attributes('-topmost', True)
root.geometry("650x750")
root.title("Global swap tool")
drop_var = ctk.StringVar()
drop_var.set("DBKEY")
format_strings = {
    'DBKEY': "DBKey IN ({})",
}

frame_height = 650
frame_width = 170


first_frame = ctk.CTkFrame(root, fg_color="green", width=frame_width, height=frame_height)
first_frame.grid(row=0, column=1, padx=10, pady=10)

second_frame = ctk.CTkFrame(root, fg_color="green", width=frame_width, height=frame_height)
second_frame.grid(row=0, column=2, padx=10, pady=10)

third_frame = ctk.CTkFrame(root, fg_color="green", width=frame_width, height=frame_height)
third_frame.grid(row=0, column=3, padx=10, pady=10)

#Third frame // menu frame

clear_img = os.path.normpath('clear.png')
clear_img_size = Image.open(clear_img).size
clear_img_new_size = ((clear_img_size[0] / 3), (clear_img_size[1] / 3))
clear_img_button = Image.open(clear_img).resize(clear_img_new_size)

get_query_size = (Image.open(os.path.normpath('get_query.png'))).size
get_query_new_size = ((get_query_size[0] / 3), (get_query_size[1] / 3))
get_query_img_button = ImageTk.PhotoImage(get_query_img)

clear_button = ctk.CTkButton(third_frame,text="", image=clear_img_button)
get_query_button = ctk.CTkButton(third_frame, text="", image=get_query_img_button)
attribute_dropdown = ttk.Combobox(third_frame, textvariable=drop_var, width=10)

clear_button.grid(row=1, column=1, pady=5, padx=5)
get_query_button.grid(row=2, column=1, pady=5, padx=5)
attribute_dropdown.grid(row=3, column=1, pady=5, padx=5)


root.mainloop()