import tkinter as tk
from tkinter import ttk
import pyperclip


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor for the Advanced Filter")

        self.drop_var = tk.StringVar()
        self.drop_var.set("ID")  # Default value
        self.processed_lines = 0

        self.format_strings = {
            'UPC': "UPC in ({})",
            'RETAILER STORE': "CAST([Desc2] As varchar(1000)) IN ({})",
            'DBKEY': "DBKey IN ({})",
            'RESET TIMING AND RETAILER STORE': "CAST([Desc10] As varchar(1000)) = N'{}' AND CAST([Desc2] As varchar(1000)) IN ({})",
            'STATE': "CAST([Desc5] As varchar(1000)) IN ({})",
            'TDLINX': "CAST([Desc21] As varchar(1000)) IN ({})",
            'ID': "ID in ({})",
            'MC RPL UPC': "Desc20 in ({})"
        }

        self.year_var = tk.StringVar()
        self.year_var.set("2022")  # Default year

        self.season_var = tk.StringVar()
        self.season_var.set("SPRING")  # Default season

        self.current_position = 0  # Track current position for chunked copying

        self.mirrored_text_frame = tk.Frame(self.root)
        self.mirrored_text_frame.grid(column=2, row=0, rowspan=4, padx=10, pady=5, sticky="nsew")

        self.mirrored_text = tk.Text(self.mirrored_text_frame, height=20, width=40, bg='light grey', wrap="none")
        self.mirrored_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.mirrored_text_scrollbar = tk.Scrollbar(self.mirrored_text_frame, command=self.mirrored_text.yview)
        self.mirrored_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.mirrored_text.config(yscrollcommand=self.mirrored_text_scrollbar.set)

        # Make the mirrored field unselectable
        self.mirrored_text.bind("<Key>", lambda e: "break")
        self.mirrored_text.bind("<Button-1>", lambda e: "break")

        self.init_ui()

    def init_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.drop = ttk.Combobox(self.root, textvariable=self.drop_var, width=50)
        self.drop['values'] = (
            'ID', 'UPC', 'MC RPL UPC', 'RETAILER STORE', 'DBKEY', 'RESET TIMING AND RETAILER STORE', 'STATE', 'TDLINX')
        self.drop.grid(column=0, row=0, padx=10, pady=5, sticky="w")
        self.drop.bind("<<ComboboxSelected>>", self.update_ui)

        self.year_drop = ttk.Combobox(self.root, textvariable=self.year_var, state='disabled', width=50)
        self.year_drop['values'] = list(range(2000, 2031))  # Years from 2000 to 2030
        self.year_drop.grid(column=0, row=1, padx=10, pady=5, sticky="w")

        self.season_drop = ttk.Combobox(self.root, textvariable=self.season_var, state='disabled', width=50)
        self.season_drop['values'] = ('SPRING', 'SUMMER', 'FALL', 'WINTER')  # Added 'WINTER' for completeness
        self.season_drop.grid(column=0, row=2, padx=10, pady=5, sticky="w")

        self.text_frame = tk.Frame(self.root)
        self.text_frame.grid(column=1, row=0, rowspan=4, padx=10, pady=5, sticky="nsew")

        self.text = tk.Text(self.text_frame, height=20, width=40)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text.config(yscrollcommand=self.scrollbar.set)

        self.clear_button = tk.Button(self.root, text="Clear", command=self.clear_text, width=30)
        self.clear_button.grid(column=0, row=4, columnspan=2, padx=10, pady=5)

        # New button for chunked copying
        self.chunk_copy_button = tk.Button(self.root, text="Progressive clipboard (batch)", command=self.copy_next_chunk, width=30)
        self.chunk_copy_button.grid(column=0, row=5, columnspan=2, padx=10, pady=5)

    def update_ui(self, event):
        if self.drop_var.get() == 'RESET TIMING AND RETAILER STORE':
            self.year_drop.config(state='normal')
            self.season_drop.config(state='normal')
        else:
            self.year_drop.config(state='disabled')
            self.season_drop.config(state='disabled')
        self.text.delete("1.0", "end")  # Clear the text input

    def update_mirrored_text(self):
        # Synchronize the mirrored text with the input text
        input_text = self.text.get("1.0", "end-1c")
        self.mirrored_text.delete("1.0", "end")
        self.mirrored_text.insert("1.0", input_text)

        # Calculate and highlight processed lines based on character count instead of line count
        all_text = self.mirrored_text.get("1.0", "end-1c")
        processed_chars = len(all_text) - len(input_text)

        # Find the line number where the last chunk ended
        end_line = self.mirrored_text.search('\n', f"1.0+{processed_chars}c", "end")
        if not end_line:  # If no newline is found, assume processing to the end of the text
            end_line = self.mirrored_text.index("end-1c")

        self.mirrored_text.tag_add("processed", "1.0", end_line)
        self.mirrored_text.tag_config("processed", background="dark grey")

        # Auto-scrolling to the start of the last processed chunk
        self.mirrored_text.see(end_line)

    def clear_text(self):
        self.text.delete("1.0", "end")
        self.current_position = 0  # Reset chunk position
        self.processed_lines = 0  # Reset processed lines count
        self.text.tag_remove("processed", "1.0", "end")
        self.mirrored_text.delete("1.0", "end")
        self.mirrored_text.tag_remove("processed", "1.0", "end")

    def copy_to_clipboard(self):
        values = self.text.get("1.0", "end-1c").split('\n')  # Split input by new lines
        values = [val for val in values if val]  # Remove empty strings
        values_str = ','.join(f"'{val}'" for val in values)  # Format as strings and join

        if self.drop_var.get() == 'RESET TIMING AND RETAILER STORE':
            result = self.format_strings[self.drop_var.get()].format(
                f"{self.year_var.get()} {self.season_var.get()}",
                values_str)  # Use the correct format string
        else:
            result = self.format_strings[self.drop_var.get()].format(values_str)  # Use the correct format string

        pyperclip.copy(result)

    def copy_next_chunk(self):
        # Considering the "ATTRIBUTE IN" part's length in the character limit
        attribute_in_length = len(self.format_strings[self.drop_var.get()].format('')) - 2  # Subtract placeholders
        max_length = 1024 - attribute_in_length
        text = self.text.get("1.0", "end-1c")
        values = text.split('\n')
        chunk = ''
        processed_chars = 0

        while values and processed_chars + len(values[0]) + len("','") <= max_length:
            if chunk:  # Add ',' between values but not before the first value
                chunk += "','"
                processed_chars += 3  # Length of "','"
            chunk += values.pop(0)
            processed_chars += len(chunk[-len(values[0]):])  # Add the length of the last added value

        formatted_text = self.format_strings[self.drop_var.get()].format(chunk)
        pyperclip.copy(formatted_text)

        # Update input and mirrored text areas
        self.update_mirrored_text()

        # Update the input text area with remaining values
        self.text.delete("1.0", "end")
        self.text.insert("1.0", '\n'.join(values))

    def highlight_processed_lines(self, line_count):
        start = f"{self.processed_lines + 1}.0"
        end = f"{self.processed_lines + line_count}.0"
        self.text.tag_add("processed", start, end)
        self.text.tag_config("processed", background="light grey")

        self.processed_lines += line_count  # Update the count of processed lines


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
