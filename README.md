# ligne-claire-agent

> An AI-assisted image generation pipeline for producing artwork in the **Ligne Claire** style — characterised by clean outlines, flat colour fills, and clear visual storytelling. The pipeline includes a prompt guardrail, a perceptual similarity checker, and a human review dashboard.

---

## About This Project

**Ligne Claire** (French: *clear line*) is a graphic art style that originated in Franco-Belgian comics during the early-to-mid 20th century. It is defined by uniform line weights, minimal shading, and strong compositional clarity. This project uses that visual style as the **target aesthetic** for AI-generated images.

This repository provides a set of tools to:

1. **Filter and sanitise prompts** before they are sent to an image generation model, ensuring no protected character names, trademarked titles, or copyrighted IP references are passed through.
2. **Detect visual similarity** between AI-generated output and a set of reference images, flagging results that are too close to known protected works.
3. **Queue flagged images for human review** via a lightweight dashboard before any output is published or used.

> **Copyright notice:** This project does not reproduce, distribute, or reference any copyrighted artworks, characters, or titles. The Ligne Claire art *style* itself is not subject to copyright protection — only specific character designs, story elements, and original artwork are. All reference images used with this pipeline must be either original works, public domain material, or images for which the user holds appropriate rights.

---

## Repository Structure

```
ligne-claire-agent/
├── data/
│   ├── reference_images/   # Your own reference images (original or public domain)
│   └── training_images/    # Source images for loading into the pipeline
├── logs/                   # Runtime logs (auto-generated)
├── scripts/
│   ├── load_training_images.py     # Scans training_images/ and copies to reference_images/
│   ├── prompt_gate.py              # Guardrail: blocks and rewrites prompts
│   ├── image_similarity_flagger.py # Compares output to references via perceptual hashing
│   └── review_dashboard.py        # Dashboard for reviewing flagged images
├── .gitignore
├── LICENSE
└── README.md
```

---

## Scripts Overview

### `load_training_images.py`
Scans `data/training_images/` for supported image formats (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`) and copies them into `data/reference_images/` for use by the similarity flagger.

```bash
python scripts/load_training_images.py
```

### `prompt_gate.py`
A text-based guardrail that analyses prompts **before** they reach the image model. It:
- **Blocks** prompts containing names of specific copyrighted characters or creators
- **Rewrites** prompts that use style-related terminology into legally neutral equivalents (e.g. genre references are replaced with descriptive style terms)
- **Allows** prompts that already use abstract, style-appropriate language

```bash
python scripts/prompt_gate.py
```

### `image_similarity_flagger.py`
Compares AI-generated images against the reference set using **perceptual hashing** (aHash + dHash via the `imagehash` library). Images above a configurable similarity threshold are flagged as high or medium risk and written to a review queue.

```bash
# Single image
python scripts/image_similarity_flagger.py --generated path/to/image.png

# Batch folder
python scripts/image_similarity_flagger.py --batch path/to/generated_folder/
```

### `review_dashboard.py`
A terminal-based dashboard that reads the review queue (`review_queue.jsonl`) and allows a human reviewer to approve or reject flagged images before they are used or published.

```bash
python scripts/review_dashboard.py
```

---

## Setup

### Requirements
- Python 3.10+
- Dependencies:

```bash
pip install Pillow imagehash
```

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ecca88quick-oss/ligne-claire-agent.git
cd ligne-claire-agent

# 2. Install dependencies
pip install Pillow imagehash

# 3. Add your own reference images to data/training_images/
# (use only original works or public domain images you have rights to)

# 4. Load them into the reference set
python scripts/load_training_images.py

# 5. Run the prompt gate before generating
python scripts/prompt_gate.py

# 6. After generation, run the similarity check
python scripts/image_similarity_flagger.py --batch path/to/output/

# 7. Review flagged images
python scripts/review_dashboard.py
```

---

## Legal Notes

- The **Ligne Claire art style** is a historical and widely practised graphic style. It is not owned by any individual or company and is free to use as a stylistic reference.
- This pipeline is specifically designed to **prevent** the generation of images that could infringe on copyrighted character designs or protected artworks.
- Users are responsible for ensuring that any images placed in `data/reference_images/` or `data/training_images/` are either original, public domain, or used with appropriate permission.
- This project does not ship with any reference images.

---

## License

See [LICENSE](LICENSE) for details.
