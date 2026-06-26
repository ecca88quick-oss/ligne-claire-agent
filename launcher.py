import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import io
import os
import sys
from pathlib import Path
import datetime

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip3 install requests")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
except ImportError:
    print("Pillow not installed. Run: pip3 install Pillow")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

HF_API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"

LIGNE_CLAIRE_STYLE = (
    "ligne claire comic art style, clean bold outlines, flat colour fills, "
    "Franco-Belgian comic book illustration, Tintin style, "
    "no shading, no gradients, white background, high contrast"
)


def get_hf_token():
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("HF_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    break
    return token


def generate_image(prompt, token):
    full_prompt = prompt + ", " + LIGNE_CLAIRE_STYLE
    headers = {"Authorization": "Bearer " + token}
    payload = {"inputs": full_prompt}
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=120)
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content))
    else:
        raise RuntimeError("API Fehler " + str(response.status_code) + ": " + response.text[:200])


class LigneClaireApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Ligne-Claire Comic Generator")
        self.geometry("900x750")
        self.resizable(True, True)
        self.current_image = None
        self.current_pil_image = None
        self._build_ui()

    def _build_ui(self):
        token_frame = ttk.LabelFrame(self, text="HuggingFace Token", padding=8)
        token_frame.pack(fill="x", padx=12, pady=(10, 4))
        self.token_var = tk.StringVar(value=get_hf_token())
        self._token_entry = ttk.Entry(token_frame, textvariable=self.token_var, show="*", width=60)
        self._token_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(token_frame, text="Anzeigen", command=self._toggle_token).pack(side="left", padx=4)
        self._token_shown = False
        ttk.Label(token_frame, text="(nicht gespeichert)", foreground="gray").pack(side="left", padx=6)

        prompt_frame = ttk.LabelFrame(self, text="Bildprompt", padding=8)
        prompt_frame.pack(fill="x", padx=12, pady=4)
        self.prompt_var = tk.StringVar(value="Ein Detektiv in Paris bei Nacht")
        prompt_entry = ttk.Entry(prompt_frame, textvariable=self.prompt_var, width=70)
        prompt_entry.pack(side="left", fill="x", expand=True)
        prompt_entry.bind("<Return>", lambda e: self._start_generation())
        self.gen_button = ttk.Button(prompt_frame, text="Generieren", command=self._start_generation)
        self.gen_button.pack(side="left", padx=6)

        self.status_var = tk.StringVar(value="Bereit.")
        ttk.Label(self, textvariable=self.status_var, anchor="w", foreground="blue").pack(fill="x", padx=12)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=12, pady=2)

        img_frame = ttk.LabelFrame(self, text="Generiertes Bild", padding=6)
        img_frame.pack(fill="both", expand=True, padx=12, pady=4)
        self.canvas = tk.Canvas(img_frame, bg="#1a1a1a")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

        save_frame = ttk.Frame(self)
        save_frame.pack(fill="x", padx=12, pady=(2, 10))
        self.save_button = ttk.Button(save_frame, text="Bild speichern", command=self._save_image, state="disabled")
        self.save_button.pack(side="right")
        ttk.Label(save_frame, text="Ausgabe: " + str(OUTPUT_DIR), foreground="gray").pack(side="left")

    def _toggle_token(self):
        self._token_shown = not self._token_shown
        self._token_entry.config(show="" if self._token_shown else "*")

    def _start_generation(self):
        prompt = self.prompt_var.get().strip()
        token = self.token_var.get().strip()
        if not prompt:
            messagebox.showwarning("Kein Prompt", "Bitte einen Bildprompt eingeben.")
            return
        if not token:
            messagebox.showerror("Kein Token", "Bitte HuggingFace Token eingeben.\n\nErstelle .env:\nHF_TOKEN=hf_...")
            return
        self.gen_button.config(state="disabled")
        self.status_var.set("Bild wird generiert ... (30-60 Sek.)")
        self.progress.start(10)
        threading.Thread(target=self._generate_thread, args=(prompt, token), daemon=True).start()

    def _generate_thread(self, prompt, token):
        try:
            pil_image = generate_image(prompt, token)
            self.after(0, self._display_image, pil_image)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _display_image(self, pil_image):
        self.progress.stop()
        self.current_pil_image = pil_image
        self._render_image()
        self.save_button.config(state="normal")
        self.gen_button.config(state="normal")
        self.status_var.set("Fertig! Bild speichern oder neuen Prompt eingeben.")

    def _render_image(self):
        if not self.current_pil_image:
            return
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600
        img = self.current_pil_image.copy()
        img.thumbnail((cw, ch), Image.LANCZOS)
        self.current_image = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, anchor="center", image=self.current_image)

    def _on_resize(self, event):
        self._render_image()

    def _show_error(self, msg):
        self.progress.stop()
        self.gen_button.config(state="normal")
        self.status_var.set("Fehler: " + msg[:80])
        messagebox.showerror("Generierungsfehler", msg)

    def _save_image(self):
        if not self.current_pil_image:
            return
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = OUTPUT_DIR / ("ligne_claire_" + timestamp + ".png")
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Alle Dateien", "*.*")],
            initialdir=str(OUTPUT_DIR),
            initialfile=default_name.name,
            title="Bild speichern"
        )
        if path:
            self.current_pil_image.save(path)
            self.status_var.set("Gespeichert: " + path)


if __name__ == "__main__":
    app = LigneClaireApp()
    app.mainloop()
