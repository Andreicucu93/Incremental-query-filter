import tkinter as tk
from tkinter import ttk
import pyperclip
import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps
import shutil, os


clear_img = Image.open(os.path.normpath('clear.png'))
clear_img_size = clear_img.size
print(f'Original size: {clear_img_size}')

clear_img_new_size = (int(clear_img_size[0] / 3) , int(clear_img_size[1] / 3))
print(f'New size: {clear_img_new_size}')