# ligne-claire-agent

> An AI-assisted image generation pipeline for producing artwork in the **Ligne Claire** style — characterised by clean outlines, flat colour fills, and clear visual storytelling. The pipeline includes a prompt guardrail, a perceptual similarity checker, and a human review dashboard.

---

## About This Project

**Ligne Claire** (French: *clear line*) is a graphic art style from Franco-Belgian comics (early-to-mid 20th century), defined by uniform line weights, minimal shading, and strong compositional clarity.

This repository provides tools to:

1. **Filter and sanitise prompts** — no protected names, trademarks, or copyrighted IP pass through.
2. **Detect visual similarity** between AI-generated output and reference images.
3. **Queue flagged images for human review** before any output is published.

> **Copyright notice:** This project does not reproduce or reference any copyrighted artworks or characters. The Ligne Claire *style* is not subject to copyright. All reference images must be original works or images for which you hold appropriate rights.

---

## Quickstart — GUI Launcher (empfohlen)

Kein Terminal erforderlich. Doppelklick auf `launcher.py` oder:

```bash
python launcher.py
```

Es öffnet sich ein Fenster mit 5 Schaltflächen:

| Schaltfläche | Funktion |
|---|---|
| Schritt 1: Bilder laden | Kopiert `data/training_images/` → `data/reference_images/` |
| Schritt 2: Prompt prüfen | Prompt eingeben und durch den Gate schicken |
| Schritt 3a: Einzelbild prüfen | Bilddatei wählen und Ähnlichkeit prüfen |
| Schritt 3b: Batch-Ordner prüfen | Ganzen Ordner mit Bildern prüfen |
| Schritt 4: Review-Dashboard | Review-Queue und Statistiken anzeigen |

Alle Ausgaben erscheinen im Konsolenfenster der GUI.

---

## Quickstart — Kommandozeile

```bash
# Demo (alle Schritte ohne Bild)
python main.py

# Schritt 1: Bilder laden
python main.py --load-images

# Schritt 2: Prompt prüfen
python main.py --prompt "Abenteurer im klaren Linienstil"

# Schritt 3a: Einzelbild
python main.py --generated pfad/bild.png

# Schritt 3b: Batch
python main.py --batch pfad/zum/ordner/

# Schritt 4: Review
python main.py --review
```

---

## Voraussetzungen

- Python 3.10+
- Tkinter (eingebaut, kein pip nötig)
- Für Bildvergleich:

```bash
pip install Pillow imagehash
```

> Alle anderen Abhängigkeiten sind Python-Standardbibliotheken — **kostenlos, keine externen Dienste**.

---

## Projektstruktur

```
ligne-claire-agent/
├── launcher.py                    # GUI-Starter (Tkinter) ← hier starten
├── main.py                        # CLI-Einstiegspunkt
├── scripts/
│   ├── load_training_images.py    # Schritt 1: Referenzbilder laden
│   ├── prompt_gate.py             # Schritt 2: Prompt filtern & umschreiben
│   ├── image_similarity_flagger.py # Schritt 3: Perceptual Hashing
│   └── review_dashboard.py        # Schritt 4: Review-Queue & Statistiken
├── data/
│   ├── training_images/           # Eigene Bilder hier ablegen
│   └── reference_images/          # Wird automatisch befüllt
├── logs/
│   ├── review_queue.jsonl         # Markierte Bilder (auto)
│   └── audit_log.jsonl            # Entscheidungsprotokoll
└── LICENSE                        # MIT
```

---

## Pipeline-Ablauf

```
[Bilder]  --> load_training_images  --> [Referenzindex]
                                              |
[Prompt]  --> prompt_gate           --> [Geprüfter Prompt]
                                              |
[Bild]    --> image_similarity_flagger --> [LOW / MEDIUM / HIGH]
                                              |
             [MEDIUM/HIGH] --> review_dashboard --> [Freigabe / Ablehnung]
```

---

## Lizenz

MIT License — siehe [LICENSE](LICENSE).
