import tkinter as tk
from tkinter import ttk
import pyperclip
import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps
import shutil, os
from calculate_query import calculate_input
from executed_records import register_executed_records

frame_background = '#242424'
main_background = '#242424'


root = ctk.CTk(fg_color=main_background)
root.attributes('-topmost', True)
root.geometry("650x500") #WxH
root.title("Global swap tool")

drop_var = ctk.StringVar()
drop_var.set("DBKEY")
format_strings = {
    'DBKEY': "DBKey IN ({})",
}

query_attribute = drop_var.get()


def get_user_input():
    user_input = input_box.get("1.0", "end-1c")
    executed_values = progress_box.get("1.0", "end-1c")
    progress_box.configure(state="normal", bg='gray')
    progress_box.insert("1.0", user_input + "\n")

    progress_box.configure(state="disabled")
    progress_box.insert("1.0", calculate_input(attribute=query_attribute, new_data=user_input, old_data=executed_values))

frame_dims = (650, 170)

first_frame = ctk.CTkFrame(root, fg_color=frame_background, width=frame_dims[1], height=frame_dims[0])
first_frame.grid(row=0, column=1, padx=(20,5), pady=30)

second_frame = ctk.CTkFrame(root, fg_color=frame_background, width=frame_dims[1], height=frame_dims[0])
second_frame.grid(row=0, column=2, padx=10, pady=30)

third_frame = ctk.CTkFrame(root, fg_color=frame_background, width=frame_dims[1], height=frame_dims[0])
third_frame.grid(row=0, column=3, padx=10, pady=10)

#First frame // Input area
input_label = ctk.CTkLabel(first_frame, text="Paste as column")
input_label.grid(row=0, column=1)
input_box = tk.Text(first_frame, width=17)
input_box.grid(row=1, column=1)

#Second frame // Progress reflect
progress_label = ctk.CTkLabel(second_frame, text="Progress status")
progress_label.grid(row=0, column=1)
progress_box = tk.Text(second_frame, width=17)
progress_box.configure(state="disabled", bg='gray')
progress_box.grid(row=1, column=1)

#Third frame // menu frame
clear_img = Image.open(os.path.normpath('images/clear.png')) #Locating and storing original image
clear_img_new_size = (int(clear_img.size[0] / 1.5), int(clear_img.size[1] / 1.5)) #Storing new image size in a tuple
clear_img_resized = ImageTk.PhotoImage(clear_img.resize(clear_img_new_size)) #used in GUI

get_query_img = Image.open(os.path.normpath('images/get_query.png')) #Locating and storing original image
get_query_img_new_size = (int(get_query_img.size[0] / 1.5), int(get_query_img.size[1] / 1.5)) #Storing new image size in a tuple
get_query_img_resized = ImageTk.PhotoImage(get_query_img.resize(get_query_img_new_size)) #used in GUI

clear_button = ctk.CTkButton(third_frame, text="", image=clear_img_resized, command=get_user_input, width=5, fg_color=frame_background, hover_color=frame_background)
get_query_button = ctk.CTkButton(third_frame, text="", image=get_query_img_resized, width=5, fg_color=frame_background, hover_color=frame_background)
attribute_dropdown = ttk.Combobox(third_frame, textvariable=drop_var, width=10)


clear_button.grid(row=1, column=0, pady=5, padx=5)
get_query_button.grid(row=2, column=0, pady=5, padx=5)
attribute_dropdown.grid(row=3, column=0, pady=5, padx=5)



root.mainloop()