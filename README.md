![image](https://github.com/user-attachments/assets/a9f96da3-0832-4065-a96b-c8509345cecc)

# Incremental Query Filter

A lightweight **Python desktop tool** (Tkinter + CustomTkinter) that helps build **incremental SQL `IN` queries** from large lists of IDs/keys.  
It respects a user-defined character limit (useful for database filter constraints) and copies each generated query to your clipboard.

## 🔹 Features
- Paste a column of data (IDs, DB keys, etc.).
- Generate progressive queries under a **custom character limit**.
- Track already executed vs. pending records.
- Auto-copy query to clipboard via `pyperclip`.
- UI tweaks: transparency, stay-on-top, clear/reset.
- Saves progress between runs (`all_records.txt`, `executed_records.txt`).

## 🚦 Status
✅ Fully functional and maintained.

## 🛠️ Tech Stack
- Python 3
- Tkinter / CustomTkinter (GUI)
- Pyperclip (clipboard)

## 📦 Installation
```bash
# (Optional) create a venv
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install customtkinter pyperclip
