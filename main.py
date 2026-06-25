#!/usr/bin/env python3
"""
main.py - Ligne-Claire-Agent Pipeline
Startpunkt fuer die gesamte Pipeline:
 1. Trainingsdaten laden
 2. Prompt pruefen und bereinigen
 3. Bilderagentur starten (Aehnlichkeitspruefung)
 4. Review-Dashboard oeffnen
Ausfuehren: python main.py
"""
import sys
import argparse
from pathlib import Path

# --- Pfad-Setup: scripts/ dem Import-Pfad hinzufuegen ---
SCRIPTS_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from load_training_images import load_training_images, copy_to_reference
from prompt_gate import classify_prompt
from image_similarity_flagger import build_reference_index, flag_image, run_batch
from review_dashboard import cmd_list, cmd_stats

BANNER = """
================================================
 ligne-claire-agent | Ligne-Claire-Pipeline
================================================
"""


def step_load_images():
    print("\n[Schritt 1] Trainingsdaten laden...")
    try:
        images = load_training_images()
        if images:
            copy_to_reference(images)
            print(f"  {len(images)} Bild(er) in Referenzordner kopiert.")
        else:
            print("  Keine Bilder gefunden. Referenzordner bleibt unveraendert.")
    except FileNotFoundError as e:
        print(f"  Hinweis: {e}")
        print("  Lege data/training_images/ an und fuege eigene Bilder hinzu.")


def step_prompt_gate(prompt: str) -> str | None:
    print("\n[Schritt 2] Prompt-Gate pruefen...")
    result = classify_prompt(prompt)
    decision = result.get("decision")
    if decision == "block":
        print(f"  GESPERRT: Prompt enthaelt geschuetzte Begriffe.")
        print(f"  Treffer: {result.get('matches')}")
        return None
    elif decision == "rewrite":
        new_prompt = result.get("rewritten", prompt)
        print(f"  Prompt umgeschrieben:")
        print(f"  Vorher : {prompt}")
        print(f"  Nachher: {new_prompt}")
        return new_prompt
    else:
        print(f"  Prompt zugelassen: {prompt}")
        return prompt


def step_similarity_check(path: str, batch: bool = False):
    print("\n[Schritt 3] Aehnlichkeitspruefung...")
    ref_dir = Path(__file__).parent / "data" / "reference_images"
    try:
        reference_index = build_reference_index(ref_dir)
    except Exception:
        reference_index = []
        print("  Hinweis: Kein Referenzindex gefunden – Pruefung ohne Referenzbilder.")
    if batch:
        results = run_batch(Path(path), reference_index)
    else:
        result = flag_image(Path(path), reference_index)
        results = [result]
    for r in results:
        print(f"  Bild: {Path(r['generated_image']).name}  "
              f"Risiko: {r['risk_level']}  "
              f"Hamming: {r['hamming_distance']}")


def step_review_dashboard():
    print("\n[Schritt 4] Review-Queue anzeigen...")
    cmd_list()
    print("\nStatistik:")
    cmd_stats()


def main():
    print(BANNER)
    parser = argparse.ArgumentParser(
        description="Ligne-Claire-Agent: KI-Bildgenerations-Pipeline"
    )
    parser.add_argument(
        "--prompt", type=str, default=None,
        help="Prompt-Text fuer den Prompt-Gate (optional)"
    )
    parser.add_argument(
        "--generated", type=str, default=None,
        help="Pfad zu einem generierten Bild fuer die Aehnlichkeitspruefung"
    )
    parser.add_argument(
        "--batch", type=str, default=None,
        help="Pfad zu einem Ordner mit generierten Bildern (Batch-Modus)"
    )
    parser.add_argument(
        "--review", action="store_true",
        help="Review-Queue anzeigen"
    )
    parser.add_argument(
        "--load-images", action="store_true",
        help="Nur Trainingsdaten laden und in Referenzordner kopieren"
    )
    args = parser.parse_args()

    # Wenn keine Argumente: komplette Demo-Pipeline
    if len(sys.argv) == 1:
        step_load_images()
        demo_prompt = "Ein Abenteurer im Stil eines europaeischen Comics mit klaren Konturen"
        step_prompt_gate(demo_prompt)
        print("\n[Schritt 3] Aehnlichkeitspruefung:")
        print("  Kein Bild angegeben. Starte mit: python main.py --generated pfad/zum/bild.png")
        print("\n[Schritt 4] Review-Dashboard:")
        print("  Starte mit: python main.py --review")
        print("\nPipeline-Demo abgeschlossen. Alle Schritte verfuegbar.")
        return

    if args.load_images:
        step_load_images()
    if args.prompt:
        result = step_prompt_gate(args.prompt)
        if result is None:
            print("  Pipeline gestoppt: Prompt gesperrt.")
            sys.exit(1)
    if args.generated:
        step_similarity_check(args.generated, batch=False)
    if args.batch:
        step_similarity_check(args.batch, batch=True)
    if args.review:
        step_review_dashboard()


if __name__ == "__main__":
    main()
