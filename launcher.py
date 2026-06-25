#!/usr/bin/env python3
"""
launcher.py - Grafischer Starter fuer den Ligne-Claire-Agent
Doppelklick genuegt. Benoetigt: Python 3.10+ (Tkinter eingebaut)
"""
import sys
import subprocess
import threading
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, scrolledtext, messagebox, ttk
except ImportError:
    print("FEHLER: Tkinter nicht gefunden.")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
MAIN_PY = BASE_DIR / "main.py"


class LigneClaireLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ligne-Claire-Agent")
        self.geometry("680x540")
        self.resizable(True, True)
        self.configure(bg="#1e1e2e")
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="ligne-claire-agent",
                 font=("Helvetica", 18, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(18, 2))
        tk.Label(self, text="Prompt-Gate  |  Similarity-Check  |  Review",
                 font=("Helvetica", 9), fg="#6c7086",
                 bg="#1e1e2e").pack(pady=(0, 14))

        f = tk.Frame(self, bg="#1e1e2e")
        f.pack(fill="x", padx=30)

        self._btn(f, "Schritt 1:  Bilder laden",
                  "Trainingsdaten in Referenzordner kopieren",
                  self.run_load_images)

        prompt_row = tk.Frame(f, bg="#1e1e2e")
        prompt_row.pack(fill="x", pady=4)
        tk.Label(prompt_row, text="Schritt 2:  Prompt pruefen:",
                 fg="#cdd6f4", bg="#1e1e2e", width=26,
                 anchor="w").pack(side="left")
        self.prompt_var = tk.StringVar()
        tk.Entry(prompt_row, textvariable=self.prompt_var,
                 bg="#313244", fg="#cdd6f4",
                 insertbackground="white", relief="flat",
                 width=30).pack(side="left", padx=6)
        tk.Button(prompt_row, text="Pruefen",
                  command=self.run_prompt_gate,
                  bg="#89b4fa", fg="#1e1e2e", relief="flat",
                  font=("Helvetica", 9, "bold"),
                  padx=10).pack(side="left")

        self._btn(f, "Schritt 3a: Einzelbild pruefen",
                  "Datei auswaehlen und Aehnlichkeit pruefen",
                  self.run_single_image)
        self._btn(f, "Schritt 3b: Batch-Ordner pruefen",
                  "Ordner auswaehlen und alle Bilder pruefen",
                  self.run_batch)
        self._btn(f, "Schritt 4:  Review-Dashboard",
                  "Markierte Bilder pruefen und freigeben",
                  self.run_review)

        ttk.Separator(self, orient="horizontal").pack(
            fill="x", padx=30, pady=12)

        tk.Label(self, text="Ausgabe:", fg="#6c7086",
                 bg="#1e1e2e", font=("Helvetica", 9)).pack(
            anchor="w", padx=30)
        self.console = scrolledtext.ScrolledText(
            self, height=10, bg="#181825", fg="#a6e3a1",
            font=("Courier", 9), relief="flat", state="disabled")
        self.console.pack(fill="both", expand=True,
                          padx=30, pady=(2, 16))

    def _btn(self, parent, label, tip, cmd):
        row = tk.Frame(parent, bg="#1e1e2e")
        row.pack(fill="x", pady=4)
        tk.Button(row, text=label, command=cmd,
                  bg="#313244", fg="#cdd6f4", relief="flat",
                  font=("Helvetica", 10), anchor="w",
                  padx=14, pady=6,
                  activebackground="#45475a",
                  activeforeground="#cdd6f4",
                  width=34).pack(side="left")
        tk.Label(row, text=tip, fg="#6c7086",
                 bg="#1e1e2e",
                 font=("Helvetica", 8)).pack(side="left", padx=10)

    def _log(self, text):
        self.console.configure(state="normal")
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        self.console.configure(state="disabled")

    def _run(self, args):
        def task():
            self._log(f"\n> python main.py {' '.join(args)}")
            try:
                r = subprocess.run(
                    [sys.executable, str(MAIN_PY)] + args,
                    capture_output=True, text=True,
                    cwd=str(BASE_DIR))
                if r.stdout:
                    self._log(r.stdout)
                if r.stderr:
                    self._log("[FEHLER] " + r.stderr)
            except Exception as e:
                self._log(f"[AUSNAHME] {e}")
        threading.Thread(target=task, daemon=True).start()

    def run_load_images(self):
        self._run(["--load-images"])

    def run_prompt_gate(self):
        p = self.prompt_var.get().strip()
        if not p:
            messagebox.showwarning(
                "Kein Prompt",
                "Bitte einen Prompt-Text eingeben.")
            return
        self._run(["--prompt", p])

    def run_single_image(self):
        path = filedialog.askopenfilename(
            title="Bild auswaehlen",
            filetypes=[("Bilder",
                        "*.png *.jpg *.jpeg *.webp *.bmp")])
        if path:
            self._run(["--generated", path])

    def run_batch(self):
        path = filedialog.askdirectory(
            title="Bildordner auswaehlen")
        if path:
            self._run(["--batch", path])

    def run_review(self):
        self._run(["--review"])


if __name__ == "__main__":
    app = LigneClaireLauncher()
    app.mainloop()
