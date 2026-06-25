# ligne-claire-agent

> An AI-assisted image generation pipeline for producing artwork in the **Ligne Claire** style — characterised by clean outlines, flat colour fills, and clear visual storytelling. The pipeline includes a prompt guardrail, a perceptual similarity checker, and a human review dashboard.

---

## About This Project

**Ligne Claire** (French: *clear line*) is a graphic art style that originated in Franco-Belgian comics during the early-to-mid 20th century. It is defined by uniform line weights, minimal shading, and strong compositional clarity. This project uses that visual style as the **target aesthetic** for AI-generated images.

This repository provides a set of tools to:

1. **Filter and sanitise prompts** before they are sent to an image generation model, ensuring no protected character names, trademarked titles, or copyrighted IP references are passed through.
2. **Detect visual similarity** between AI-generated output and a set of reference images, flagging results that are too close to known protected works.
3. **Queue flagged images for human review** via a lightweight dashboard before any output is published or used.

> **Copyright notice:** This project does not reproduce, distribute, or reference any copyrighted artworks, characters, or titles. The Ligne Claire art *style* itself is not subject to copyright protection — only specific character designs, story elements, and original artwork are. All reference images used with this pipeline must be either original works or images for which you hold the appropriate rights.

---

## Quickstart — GUI Launcher (empfohlen)

Kein Terminal erforderlich. Einfach Doppelklick auf `launcher.py`:

```bash
python launcher.py
```

Das öffnet ein grafisches Fenster mit 5 Schaltflächen:

| Schaltfläche | Aktion |
|---|---|
| **Schritt 1: Bilder laden** | Kopiert Trainingsbilder aus `data/training_images/` in `data/reference_images/` |
| **Schritt 2: Prompt prüfen** | Gibt einen Prompt ein und prüft ihn durch den Prompt-Gate |
| **Schritt 3a: Einzelbild prüfen** | Wählt eine Bilddatei und prüft sie auf Ähnlichkeit |
| **Schritt 3b: Batch-Ordner prüfen** | Wählt einen Ordner und prüft alle Bilder darin |
| **Schritt 4: Review-Dashboard** | Zeigt die Review-Queue und Statistiken an |

Alle Ausgaben erscheinen im eingebauten Konsolenfenster der GUI.

---

## Quickstart — Kommandozeile

```bash
# Demo-Pipeline (alle Schritte, kein Bild erforderlich)
python main.py

# Schritt 1: Trainingsbilder laden
python main.py --load-images

# Schritt 2: Prompt prüfen
python main.py --prompt "Ein Abenteurer im klaren Linienstil"

# Schritt 3a: Einzelbild prüfen
python main.py --generated pfad/zum/bild.png

# Schritt 3b: Ordner prüfen (Batch)
python main.py --batch pfad/zum/ordner/

# Schritt 4: Review-Queue anzeigen
python main.py --review
```

---

## Voraussetzungen

- Python 3.10 oder neuer
- Tkinter (in Python eingebaut, kein `pip install` nötig)
- `Pillow` und `imagehash` für die Bildvergleichsfunktion:

```bash
pip install Pillow imagehash
```

> Alle anderen Abhängigkeiten (`pathlib`, `argparse`, `json`, `re`, `uuid`, `threading`, `subprocess`, `types`) sind Python-Standardbibliotheken — **keine Kosten, keine externen Dienste**.

---

## Projektstruktur

```
ligne-claire-agent/
├── launcher.py              # GUI-Starter (Tkinter) ← hier starten
├── main.py                  # CLI-Einstiegspunkt
├── scripts/
│   ├── load_training_images.py    # Schritt 1: Referenzbilder laden
│   ├── prompt_gate.py             # Schritt 2: Prompt filtern & umschreiben
│   ├── image_similarity_flagger.py # Schritt 3: Perceptual Hashing
│   └── review_dashboard.py        # Schritt 4: Review-Queue & Statistiken
├── data/
│   ├── training_images/   # Eigene Referenzbilder hier ablegen
│   └── reference_images/  # Wird automatisch befüllt
├── logs/
│   ├── review_queue.jsonl # Markierte Bilder (automatisch)
│   └── audit_log.jsonl    # Entscheidungsprotokoll
├── README.md
└── LICENSE                  # MIT
```

---

## Pipeline-Ablauf

```
[Eigene Bilder]  -->  load_training_images.py  -->  [Referenzindex]
                                                          |
[Prompt-Eingabe] -->     prompt_gate.py         -->  [Geprüfter Prompt]
                                                          |
[Generiertes Bild] --> image_similarity_flagger.py --> [Risikostufe: LOW/MEDIUM/HIGH]
                                                          |
                            [HIGH/MEDIUM] --> review_dashboard.py --> [Freigabe / Ablehnung]
```

---

## Lizenz

MIT License. Siehe [LICENSE](LICENSE).
