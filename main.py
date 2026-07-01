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

ctk.set_appearance_mode("dark")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Incremental query filter")
        self.geometry("920x660")
        self._build_ui()
        self._load_state()

    # ---------- UI construction ----------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        ctk.CTkLabel(top, text="Attribute:").grid(row=0, column=0, padx=(12, 4), pady=10)
        self.attr_entry = ctk.CTkEntry(top, width=180)
        self.attr_entry.grid(row=0, column=1, padx=(0, 20), pady=10)
        ctk.CTkLabel(top, text="Char limit:").grid(row=0, column=2, padx=(0, 4), pady=10)
        self.limit_entry = ctk.CTkEntry(top, width=100)
        self.limit_entry.grid(row=0, column=3, padx=(0, 12), pady=10)

        card = ctk.CTkFrame(self)
        card.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text="OVERALL PROGRESS", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 2))
        self.progress = ctk.CTkProgressBar(card)
        self.progress.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        self.progress.set(0)
        self.percent_lbl = ctk.CTkLabel(card, text="0%")
        self.percent_lbl.grid(row=1, column=1, padx=12)
        self.totals_lbl = ctk.CTkLabel(card, text="Total 0  ·  Done 0  ·  Remaining 0", anchor="w")
        self.totals_lbl.grid(row=2, column=0, sticky="w", padx=12, pady=(2, 2))
        self.batches_lbl = ctk.CTkLabel(card, text="▶  Batches remaining:  0",
                                        font=ctk.CTkFont(size=15, weight="bold"), anchor="w")
        self.batches_lbl.grid(row=3, column=0, sticky="w", padx=12, pady=(2, 10))

        panels = ctk.CTkFrame(self)
        panels.grid(row=2, column=0, padx=16, pady=8, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        for c in range(3):
            panels.grid_columnconfigure(c, weight=1)
        panels.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(panels, text="PASTE COLUMN").grid(row=0, column=0, pady=(8, 2))
        self.paste_box = ctk.CTkTextbox(panels, width=240)
        self.paste_box.grid(row=1, column=0, padx=8, sticky="nsew")
        ctk.CTkButton(panels, text="Load list", command=self.load_list).grid(row=2, column=0, pady=8)

        ctk.CTkLabel(panels, text="PENDING (in order)").grid(row=0, column=1, pady=(8, 2))
        self.pending_box = ctk.CTkTextbox(panels, width=240)
        self.pending_box.grid(row=1, column=1, padx=8, sticky="nsew")

        ctk.CTkLabel(panels, text="DONE").grid(row=0, column=2, pady=(8, 2))
        self.done_box = ctk.CTkTextbox(panels, width=240)
        self.done_box.grid(row=1, column=2, padx=8, sticky="nsew")

        actions = ctk.CTkFrame(self)
        actions.grid(row=3, column=0, padx=16, pady=8, sticky="ew")
        self.next_btn = ctk.CTkButton(actions, text="▶ Next batch", command=self.next_batch,
                                      height=40, font=ctk.CTkFont(size=15, weight="bold"))
        self.next_btn.grid(row=0, column=0, padx=12, pady=10)
        ctk.CTkButton(actions, text="Clear", command=self.clear_all,
                      fg_color="firebrick1", hover_color="brown1").grid(row=0, column=1, padx=12, pady=10)

        bottom = ctk.CTkFrame(self)
        bottom.grid(row=4, column=0, padx=16, pady=(8, 16), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(bottom, text="Current query", anchor="w").grid(
            row=0, column=0, sticky="w", padx=12, pady=(8, 2))
        self.query_box = ctk.CTkTextbox(bottom, height=70)
        self.query_box.grid(row=1, column=0, columnspan=2, padx=12, sticky="ew")
        self.status_lbl = ctk.CTkLabel(bottom, text="", anchor="w")
        self.status_lbl.grid(row=2, column=0, sticky="w", padx=12, pady=(4, 8))

        self.ontop_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(bottom, text="Stay on top", variable=self.ontop_var,
                        command=self._toggle_ontop).grid(row=2, column=1, sticky="e", padx=12)
        self.alpha = ctk.CTkSlider(bottom, from_=0.3, to=1.0, command=self._set_alpha)
        self.alpha.set(1.0)
        self.alpha.grid(row=3, column=1, sticky="e", padx=12, pady=(0, 8))

    # ---------- helpers ----------
    def _set_box(self, box, lines):
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", "\n".join(lines))
        box.configure(state="disabled")   # pending/done/query are read-only

    def _toggle_ontop(self):
        self.attributes("-topmost", self.ontop_var.get())

    def _set_alpha(self, value):
        self.attributes("-alpha", float(value))

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
        self._set_box(self.pending_box, pending)
        pending_set = set(pending)
        self._set_box(self.done_box, [x for x in all_records if x not in pending_set])

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
        self.next_btn.configure(text="▶ Next batch")
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
        self.next_btn.configure(text="▶ Next Query")
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
        self.next_btn.configure(text="▶ Next batch")
        self.refresh()

    def _load_state(self):
        s = storage.load_settings(SETTINGS)
        if s.get("attribute"):
            self.attr_entry.insert(0, s["attribute"])
        if s.get("limit"):
            self.limit_entry.insert(0, str(s["limit"]))
        self.refresh()


if __name__ == "__main__":
    App().mainloop()
