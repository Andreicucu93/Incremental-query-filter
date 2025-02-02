#Progress auto saved
#Dinamic limit and attribute


import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import os
import pyperclip

# GUI Config
frame_background = '#242424'
main_background = '#242424'

root = ctk.CTk(fg_color=main_background)
root.attributes('-topmost', False, '-alpha', 1)
root.geometry("650x500")
root.title("Incremental query filter")


# Create GUI Frames
first_frame = ctk.CTkFrame(root, fg_color=frame_background)
first_frame.grid(row=0, column=1, padx=20, pady=30)

second_frame = ctk.CTkFrame(root, fg_color=frame_background)
second_frame.grid(row=0, column=2, padx=10, pady=30)

third_frame = ctk.CTkFrame(root, fg_color=frame_background)
third_frame.grid(row=0, column=3, padx=10, pady=10)

# Input Text Box (All Records)
input_label = ctk.CTkLabel(first_frame, text="Paste as column")
input_label.grid(row=0, column=1)
input_box = tk.Text(first_frame, width=17, height=25)
input_box.grid(row=1, column=1)

# Progress Text Box (Executed Records)
progress_label = ctk.CTkLabel(second_frame, text="Progress status")
progress_label.grid(row=0, column=1)
progress_box = tk.Text(second_frame, width=17, height=25)
progress_box.config(state='disabled', bg='gray')
progress_box.grid(row=1, column=1)


# 🟢 Load WIP & Completed Records from Files
def load_records():
    if not os.path.exists("all_records.txt"):
        open("all_records.txt", "w").close()
    if not os.path.exists("executed_records.txt"):
        open("executed_records.txt", "w").close()

    with open("all_records.txt", "r") as file:
        wip = {line.strip() for line in file if line.strip()}

    with open("executed_records.txt", "r") as file:
        completed = {line.strip() for line in file if line.strip()}

    return wip, completed


# 🟢 Generate Query & Update Completed Records
def generate_query():
    if character_limit.get() and attribute_char.get():
        attribute_selected = attribute_char.get()
        limit = int(character_limit.get())
    else:
        messagebox.showinfo(title="Warning", message="Please input both attribute and limit.")
        return
    wip, completed = load_records()
    new_set = []  # Store new items for the query

    for item in wip:
        if item not in completed:
            temp_set = new_set + [item]
            temp_query = f"{attribute_selected} in ({', '.join([f'\"{num}\"' for num in temp_set])})"

            if len(temp_query) > limit:
                break

            new_set.append(item)
    if not new_set:
        print("No new items could be added within the limit.")
        save_input_data()
        generate_query()
        return
    query = f"{attribute_selected} in ({', '.join([f'\"{num}\"' for num in new_set])})"
    print(f"Query: {query}")

    preview_box.config(state='normal', bg='DarkOliveGreen2')
    preview_box.delete("1.0", 'end')
    preview_box.insert("1.0", query)
    preview_box.config(state='disabled')
    pyperclip.copy(query)  # Copy query to clipboard
    with open("executed_records.txt", "a") as file:
        for item in new_set:
            file.write(f"{item}\n")
    get_query_button.configure(text="Next Query")
    progress_box.config(state='normal')
    progress_box.insert("1.0", "\n".join(new_set) + "\n")
    progress_box.config(state='disabled')
    load_records()


# 🟢 Save New Data from Input Box to `all_records.txt`
def save_input_data():
    input_data = input_box.get("1.0", "end-1c").strip()
    if input_data:  # Only save if there is content
        with open("all_records.txt", "w") as file:
            file.write(input_data + "\n")
        print("New data saved to all_records.txt")

    exec_data = progress_box.get("1.0", "end-1c").strip()
    if exec_data:
        with open("executed_records.txt", "w") as file2:
            file2.write(exec_data + "\n")
        print("New data saved to executed_records.txt")
    startup()  # Reload data


# 🟢 Load Initial Data into GUI
def startup():
    progress_box.config(state='normal')
    progress_box.delete("1.0", "end")
    input_box.delete("1.0", "end")

    wip, completed = load_records()

    input_box.insert("1.0", "\n".join(wip))
    progress_box.insert("1.0", "\n".join(completed))

    progress_box.config(state='disabled')
    preview_box.config(state='disabled')


# 🟢 Clear All Data & Reset Fields
def clear_all():
    for file in ["all_records.txt", "executed_records.txt"]:
        open(file, "w").close()  # Clear file content without deleting files
    input_box.delete("1.0", "end")
    progress_box.config(state='normal')
    progress_box.delete("1.0", "end")
    preview_box.delete("1.0", "end")
    progress_box.config(state='disabled')
    get_query_button.configure(text="Get Query")
    live_status.configure(text="")
    print("All records cleared!")

def adjust_transparency(value):
    root.attributes('-alpha', float(value))

def stay_ontop():
    current_state = root.attributes('-topmost')
    if current_state == False:
        root.attributes('-topmost', True)
    else:
        root.attributes('-topmost', False)


ontop_var = tk.BooleanVar(value=False)
transparency_var = tk.BooleanVar(value=False)

ontop_button = ctk.CTkCheckBox(third_frame, variable=ontop_var, command=stay_ontop, text='Stay on top')
ontop_button.grid(row=0, column=0, pady=5, padx=5)

transparency_slider = ctk.CTkSlider(third_frame, from_=0.3, to=1.0, number_of_steps=100, command=adjust_transparency)
transparency_slider.grid(row=1, column=0, pady=5, padx=5)
transparency_slider.set(1.0)

clear_button = ctk.CTkButton(third_frame, text="Clear", command=clear_all, fg_color='firebrick1', hover_color='brown1')
clear_button.grid(row=2, column=0, pady=5, padx=5)

settings_frame = ctk.CTkFrame(third_frame, fg_color=frame_background)
settings_frame.grid(row=5, column=0, pady=5, padx=5)

attribute_char_label = ctk.CTkLabel(settings_frame, text="Query attribute: ", width=90)
attribute_char_label.grid(row=0, column=0, pady=5, padx=5)

attribute_char = ctk.CTkEntry(settings_frame, width=75)
attribute_char.grid(row=0, column=1, pady=5, padx=5)


character_limit_label = ctk.CTkLabel(settings_frame, text="Characters limit: ")
character_limit_label.grid(row=1, column=0, pady=5, padx=5)

character_limit = ctk.CTkEntry(settings_frame, width=75)
character_limit.grid(row=1, column=1, pady=5, padx=5)

get_query_button = ctk.CTkButton(settings_frame, text="Get Query", command=generate_query)
get_query_button.grid(row=4, columnspan=2, pady=10, padx=5)

preview_box = tk.Text(settings_frame, width=30, height=13)
preview_box.grid(row=5, columnspan=2)

live_status = ctk.CTkLabel(settings_frame, text="")
live_status.grid(row=6, sticky='e')

startup()

root.mainloop()
