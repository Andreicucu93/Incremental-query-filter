"""Incremental Query Filter — desktop UI."""
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import pyperclip

import query_core as qc
import storage

ALL_RECORDS = "all_records.txt"
EXECUTED = "executed_records.txt"
SETTINGS = "settings.json"

DEFAULT_ATTRIBUTE = "DBKEY"
DEFAULT_LIMIT = 1024

ctk.set_appearance_mode("dark")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Incremental query filter")
        self.geometry("700x740")
        self.minsize(640, 680)
        self.locked = False
        self._build_ui()
        self._load_state()

    # ---------- UI construction ----------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)   # paste + current-query row expands with height

        # --- Attribute + char limit ---
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top, text="Attribute:").grid(row=0, column=0, padx=(12, 6), pady=(10, 4), sticky="w")
        self.attr_entry = ctk.CTkEntry(top)
        self.attr_entry.grid(row=0, column=1, padx=(0, 12), pady=(10, 4), sticky="ew")
        ctk.CTkLabel(top, text="Char limit:").grid(row=1, column=0, padx=(12, 6), pady=(4, 10), sticky="w")
        self.limit_entry = ctk.CTkEntry(top)
        self.limit_entry.grid(row=1, column=1, padx=(0, 12), pady=(4, 10), sticky="ew")

        # --- Overall progress card ---
        card = ctk.CTkFrame(self)
        card.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text="OVERALL PROGRESS", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 2))
        self.progress = ctk.CTkProgressBar(card)
        self.progress.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        self.progress.set(0)
        self.percent_lbl = ctk.CTkLabel(card, text="0%", width=44)
        self.percent_lbl.grid(row=1, column=1, padx=(6, 12))
        self.totals_lbl = ctk.CTkLabel(card, text="Total 0  ·  Done 0  ·  Remaining 0", anchor="w")
        self.totals_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(2, 2))
        self.batches_lbl = ctk.CTkLabel(card, text="▶  Batches remaining:  0",
                                        font=ctk.CTkFont(size=15, weight="bold"), anchor="w")
        self.batches_lbl.grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(2, 10))

        # --- Action row: Load list / Next query / Clear ---
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, padx=12, pady=6, sticky="ew")
        for c in range(3):
            actions.grid_columnconfigure(c, weight=1)
        ctk.CTkButton(actions, text="Load list", height=38, command=self.load_list).grid(
            row=0, column=0, padx=4, sticky="ew")
        self.next_btn = ctk.CTkButton(actions, text="▶ Next query", height=38,
                                      font=ctk.CTkFont(size=14, weight="bold"), command=self.next_batch)
        self.next_btn.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkButton(actions, text="Clear", height=38, fg_color="firebrick1",
                      hover_color="brown1", command=self.clear_all).grid(row=0, column=2, padx=4, sticky="ew")

        # --- Paste column + Current query, side by side ---
        pq = ctk.CTkFrame(self, fg_color="transparent")
        pq.grid(row=3, column=0, sticky="nsew", padx=12, pady=6)
        pq.grid_columnconfigure(0, weight=1)
        pq.grid_columnconfigure(1, weight=1)
        pq.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(pq, text="PASTE COLUMN", anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=(4, 6), pady=(0, 2))
        self.paste_box = ctk.CTkTextbox(pq, height=200)
        self.paste_box.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(pq, text="CURRENT QUERY", anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=1, sticky="w", padx=(6, 4), pady=(0, 2))
        self.query_box = ctk.CTkTextbox(pq, height=200)
        self.query_box.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        self.status_lbl = ctk.CTkLabel(pq, text="", anchor="w")
        self.status_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 0))

        # --- Swap OUT / Swap IN scratch fields; LOCK spans both rows beside Copy ---
        swap = ctk.CTkFrame(self)
        swap.grid(row=4, column=0, sticky="ew", padx=12, pady=6)
        swap.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(swap, text="Swap OUT", width=64).grid(row=0, column=0, padx=(12, 6), pady=(10, 4), sticky="w")
        self.swap_out_entry = ctk.CTkEntry(swap)
        self.swap_out_entry.grid(row=0, column=1, padx=6, pady=(10, 4), sticky="ew")
        ctk.CTkButton(swap, text="Copy", width=64,
                      command=lambda: self._copy_field(self.swap_out_entry, "Swap OUT")).grid(
            row=0, column=2, padx=6, pady=(10, 4))
        ctk.CTkLabel(swap, text="Swap IN", width=64).grid(row=1, column=0, padx=(12, 6), pady=(4, 10), sticky="w")
        self.swap_in_entry = ctk.CTkEntry(swap)
        self.swap_in_entry.grid(row=1, column=1, padx=6, pady=(4, 10), sticky="ew")
        ctk.CTkButton(swap, text="Copy", width=64,
                      command=lambda: self._copy_field(self.swap_in_entry, "Swap IN")).grid(
            row=1, column=2, padx=6, pady=(4, 10))
        self.lock_btn = ctk.CTkButton(swap, text="LOCK", width=88, command=self._toggle_lock)
        self.lock_btn.grid(row=0, column=3, rowspan=2, padx=(6, 12), pady=10, sticky="ns")

        # --- Footer: stay-on-top + transparency ---
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", padx=12, pady=(4, 12))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)
        self.ontop_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(footer, text="Stay on top", variable=self.ontop_var,
                        command=self._toggle_ontop).grid(row=0, column=0, sticky="w", padx=4)
        tframe = ctk.CTkFrame(footer, fg_color="transparent")
        tframe.grid(row=0, column=1, sticky="e", padx=4)
        ctk.CTkLabel(tframe, text="Transparency").grid(row=0, column=0, padx=(0, 6))
        self.alpha = ctk.CTkSlider(tframe, from_=0.3, to=1.0, number_of_steps=70,
                                   width=120, command=self._set_alpha)
        self.alpha.set(1.0)
        self.alpha.grid(row=0, column=1)

    # ---------- helpers ----------
    def _set_box(self, box, lines):
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", "\n".join(lines))
        box.configure(state="disabled")   # current-query box is read-only

    def _toggle_ontop(self):
        self.attributes("-topmost", self.ontop_var.get())

    def _set_alpha(self, value):
        self.attributes("-alpha", float(value))

    def _toggle_lock(self):
        self.locked = not self.locked
        state = "disabled" if self.locked else "normal"
        self.swap_in_entry.configure(state=state)
        self.swap_out_entry.configure(state=state)
        self.lock_btn.configure(text="Unlock" if self.locked else "LOCK")

    def _copy_field(self, entry, label):
        value = entry.get().strip()
        if not value:
            self.status_lbl.configure(text=f"{label} is empty")
            return
        pyperclip.copy(value)
        self.status_lbl.configure(text=f"Copied {label}: {value} ✓")

    # ---------- logic ----------
    def _validate(self):
        attribute = self.attr_entry.get().strip()
        limit_raw = self.limit_entry.get().strip()
        if not attribute:
            messagebox.showinfo("Missing attribute", "Please enter a query attribute.")
            return None
        if not limit_raw.isdecimal() or int(limit_raw) <= 0:
            messagebox.showinfo("Bad limit", "Char limit must be a positive whole number.")
            return None
        return attribute, int(limit_raw)

    def refresh(self):
        all_records = qc.dedup_preserve_order(storage.read_lines(ALL_RECORDS))
        done = storage.read_lines(EXECUTED)
        pending = qc.pending_records(all_records, done)

        total = len(all_records)
        done_n = total - len(pending)
        frac = (done_n / total) if total else 0
        self.progress.set(frac)
        self.percent_lbl.configure(text=f"{round(frac * 100)}%")
        self.totals_lbl.configure(
            text=f"Total {total}  ·  Done {done_n}  ·  Remaining {len(pending)}")

        attribute = self.attr_entry.get().strip()
        limit_raw = self.limit_entry.get().strip()
        if pending and attribute and limit_raw.isdecimal() and int(limit_raw) > 0:
            n = qc.count_batches(pending, attribute, int(limit_raw))
            txt = "▶  Batches remaining:  —  (limit too small)" if n is None \
                else f"▶  Batches remaining:  {n}"
        elif not pending and total:
            txt = "✅  All done"
        else:
            txt = "▶  Batches remaining:  —"
        self.batches_lbl.configure(text=txt)

        self.next_btn.configure(state="disabled" if not pending else "normal")

    def load_list(self):
        items = qc.dedup_preserve_order(self.paste_box.get("1.0", "end-1c").splitlines())
        if not items:
            messagebox.showinfo("Nothing to load", "Paste a column of IDs first.")
            return
        if storage.read_lines(EXECUTED):
            if not messagebox.askyesno(
                    "Start fresh?", "Loading a new list resets all progress. Continue?"):
                return
        storage.write_lines(ALL_RECORDS, items)
        storage.clear_file(EXECUTED)
        self.status_lbl.configure(text=f"Loaded {len(items)} records.")
        self.refresh()

    def next_batch(self):
        validated = self._validate()
        if not validated:
            return
        attribute, limit = validated
        storage.save_settings(SETTINGS, {"attribute": attribute, "limit": limit})

        all_records = qc.dedup_preserve_order(storage.read_lines(ALL_RECORDS))
        pending = qc.pending_records(all_records, storage.read_lines(EXECUTED))
        if not pending:
            self.status_lbl.configure(text="✅ All done — nothing left to query.")
            self.refresh()
            return
        batch = qc.pack_batch(pending, attribute, limit)
        if not batch:
            messagebox.showinfo(
                "Limit too small", "A single ID won't fit in the character limit. Raise the limit.")
            return
        query = qc.build_query(attribute, batch)
        pyperclip.copy(query)
        storage.append_lines(EXECUTED, batch)
        self._set_box(self.query_box, [query])
        used = qc.query_length(attribute, batch)
        self.status_lbl.configure(
            text=f"Copied {len(batch)} IDs ✓  ·  {used} / {limit} chars used")
        self.refresh()

    def clear_all(self):
        if not messagebox.askyesno(
                "Clear everything?", "This wipes the loaded list AND all progress. Continue?"):
            return
        storage.clear_file(ALL_RECORDS)
        storage.clear_file(EXECUTED)
        self.paste_box.delete("1.0", "end")
        self._set_box(self.query_box, [])
        self.status_lbl.configure(text="")
        self.refresh()

    def _load_state(self):
        s = storage.load_settings(SETTINGS)
        self.attr_entry.insert(0, s.get("attribute") or DEFAULT_ATTRIBUTE)
        self.limit_entry.insert(0, str(s.get("limit") or DEFAULT_LIMIT))
        self.refresh()


if __name__ == "__main__":
    App().mainloop()
