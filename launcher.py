#!/usr/bin/env python3
"""
launcher.py - Ligne-Claire-Agent mit integriertem Bildgenerator
Benoetigt: Python 3.10+, pip install Pillow imagehash requests
"""
import sys
import subprocess
import threading
import io
import os
from pathlib import Path
from datetime import datetime

try:
 import tkinter as tk
 from tkinter import filedialog, scrolledtext, messagebox, ttk
except ImportError:
 print("FEHLER: Tkinter nicht gefunden.")
 sys.exit(1)

try:
 import requests
 from PIL import Image, ImageTk
except ImportError:
 pass

BASE_DIR = Path(__file__).parent
MAIN_PY = BASE_DIR / "main.py"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_TOKEN = "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"

LIGNE_CLAIRE_STYLE = (
 "ligne claire comic art style, clean bold outlines, flat colour fills, "
 "Franco-Belgian comic book illustration, Tintin style, clear visual storytelling, "
 "no shading, no gradients, white background, high contrast"
)


class LigneClaireLauncher(tk.Tk):
 def __init__(self):
 super().__init__()
 self.title("Ligne-Claire-Agent")
 self.geometry("780x700")
 self.resizable(True, True)
 self.configure(bg="#1e1e2e")
 self._img_ref = None
 self._build_ui()

 def _build_ui(self):
 tk.Label(self, text="ligne-claire-agent",
 font=("Helvetica", 18, "bold"),
 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(18, 2))
 tk.Label(self, text="Bildgenerator | Prompt-Gate | Similarity-Check | Review",
 font=("Helvetica", 9), fg="#6c7086",
 bg="#1e1e2e").pack(pady=(0, 10))

 # --- BILDGENERATOR SEKTION ---
 gen_frame = tk.LabelFrame(self, text=" Bild generieren (Ligne-Claire-Stil) ",
 fg="#a6e3a1", bg="#1e1e2e",
 font=("Helvetica", 10, "bold"))
 gen_frame.pack(fill="x", padx=30, pady=(0, 10))

 prompt_row = tk.Frame(gen_frame, bg="#1e1e2e")
 prompt_row.pack(fill="x", padx=10, pady=8)
 tk.Label(prompt_row, text="Prompt:",
 fg="#cdd6f4", bg="#1e1e2e", width=8,
 anchor="w").pack(side="left")
 self.gen_prompt_var = tk.StringVar()
 self.gen_entry = tk.Entry(prompt_row,
 textvariable=self.gen_prompt_var,
 bg="#313244", fg="#cdd6f4",
 insertbackground="white", relief="flat",
 width=45, font=("Helvetica", 10))
 self.gen_entry.pack(side="left", padx=6)
 self.gen_entry.bind("<Return>", lambda e: self.generate_image())

 self.gen_btn = tk.Button(prompt_row, text="Generieren",
 command=self.generate_image,
 bg="#a6e3a1", fg="#1e1e2e", relief="flat",
 font=("Helvetica", 10, "bold"),
 padx=12, pady=4)
 self.gen_btn.pack(side="left", padx=4)

 self.save_btn = tk.Button(gen_frame, text="Bild speichern",
 command=self.save_image,
 bg="#89b4fa", fg="#1e1e2e", relief="flat",
 font=("Helvetica", 9), padx=10,
 state="disabled")
 self.save_btn.pack(anchor="e", padx=10, pady=(0, 6))

 self.img_label = tk.Label(gen_frame, bg="#181825",
 text="Hier erscheint das generierte Bild",
 fg="#6c7086", font=("Helvetica", 9))
 self.img_label.pack(fill="both", expand=True,
 padx=10, pady=(0, 10),
 ipadx=10, ipady=10)

 # --- PIPELINE SEKTION ---
 f = tk.Frame(self, bg="#1e1e2e")
 f.pack(fill="x", padx=30)

 prompt_row2 = tk.Frame(f, bg="#1e1e2e")
 prompt_row2.pack(fill="x", pady=4)
 tk.Label(prompt_row2, text="Prompt-Gate pruefen:",
 fg="#cdd6f4", bg="#1e1e2e", width=22,
 anchor="w").pack(side="left")
 self.prompt_var = tk.StringVar()
 tk.Entry(prompt_row2, textvariable=self.prompt_var,
 bg="#313244", fg="#cdd6f4",
 insertbackground="white", relief="flat",
 width=28).pack(side="left", padx=6)
 tk.Button(prompt_row2, text="Pruefen",
 command=self.run_prompt_gate,
 bg="#89b4fa", fg="#1e1e2e", relief="flat",
 font=("Helvetica", 9, "bold"),
 padx=10).pack(side="left")

 self._btn(f, "Bilder laden",
 "Referenzbilder in Trainingsordner laden",
 self.run_load_images)
 self._btn(f, "Einzelbild pruefen",
 "Bild auf Aehnlichkeit pruefen",
 self.run_single_image)
 self._btn(f, "Batch-Ordner pruefen",
 "Ganzen Ordner scannen",
 self.run_batch)
 self._btn(f, "Review-Dashboard",
 "Geflaggte Bilder freigeben oder ablehnen",
 self.run_review)

 ttk.Separator(self, orient="horizontal").pack(
 fill="x", padx=30, pady=8)

 tk.Label(self, text="Ausgabe:", fg="#6c7086",
 bg="#1e1e2e", font=("Helvetica", 9)).pack(
 anchor="w", padx=30)
 self.console = scrolledtext.ScrolledText(
 self, height=6, bg="#181825", fg="#a6e3a1",
 font=("Courier", 9), relief="flat", state="disabled")
 self.console.pack(fill="both", expand=False,
 padx=30, pady=(2, 16))

 def _btn(self, parent, label, tip, cmd):
 row = tk.Frame(parent, bg="#1e1e2e")
 row.pack(fill="x", pady=2)
 tk.Button(row, text=label, command=cmd,
 bg="#313244", fg="#cdd6f4", relief="flat",
 font=("Helvetica", 9), anchor="w",
 padx=14, pady=4,
 activebackground="#45475a",
 activeforeground="#cdd6f4",
 width=28).pack(side="left")
 tk.Label(row, text=tip, fg="#6c7086",
 bg="#1e1e2e",
 font=("Helvetica", 8)).pack(side="left", padx=10)

 def _log(self, text):
 self.console.configure(state="normal")
 self.console.insert(tk.END, text + "\n")
 self.console.see(tk.END)
 self.console.configure(state="disabled")

 def generate_image(self):
 prompt = self.gen_prompt_var.get().strip()
 if not prompt:
 messagebox.showwarning("Kein Prompt",
 "Bitte einen Prompt eingeben.")
 return
 self.gen_btn.configure(state="disabled", text="Generiere...")
 self.img_label.configure(text="Bild wird generiert, bitte warten...",
 image="")
 self._img_ref = None
 self.save_btn.configure(state="disabled")
 self._log(f"\nGeneriere Bild: '{prompt}'")

 def task():
 try:
 full_prompt = f"{prompt}, {LIGNE_CLAIRE_STYLE}"
 headers = {"Authorization": f"Bearer {HF_TOKEN}"}
 payload = {"inputs": full_prompt,
 "parameters": {"num_inference_steps": 30,
 "guidance_scale": 7.5}}
 resp = requests.post(HF_API_URL, headers=headers,
 json=payload, timeout=120)
 if resp.status_code == 200:
 img = Image.open(io.BytesIO(resp.content))
 img.thumbnail((512, 512))
 self._current_image = img
 photo = ImageTk.PhotoImage(img)
 self._img_ref = photo
 self.img_label.configure(image=photo, text="")
 self.save_btn.configure(state="normal")
 self._log("Bild erfolgreich generiert!")
 else:
 self._log(f"[FEHLER] Status {resp.status_code}: {resp.text[:200]}")
 self.img_label.configure(
 text=f"Fehler: {resp.status_code}")
 except Exception as e:
 self._log(f"[AUSNAHME] {e}")
 self.img_label.configure(text=f"Fehler: {e}")
 finally:
 self.gen_btn.configure(state="normal", text="Generieren")

 threading.Thread(target=task, daemon=True).start()

 def save_image(self):
 if not hasattr(self, "_current_image"):
 return
 ts = datetime.now().strftime("%Y%m%d_%H%M%S")
 default = str(OUTPUT_DIR / f"ligne_claire_{ts}.png")
 path = filedialog.asksaveasfilename(
 defaultextension=".png",
 filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
 initialfile=default)
 if path:
 self._current_image.save(path)
 self._log(f"Gespeichert: {path}")

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

 def run_load_images(self): self._run(["--load-images"])
 def run_prompt_gate(self):
 p = self.prompt_var.get().strip()
 if not p:
 messagebox.showwarning("Kein Prompt",
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
 def run_review(self): self._run(["--review"])


if __name__ == "__main__":
 app = LigneClaireLauncher()
 app.mainloop()
