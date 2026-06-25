"""Prompt Gate - Guardrail-System fuer Ligne-Claire-Comic-Agent.
Stufe 1: Input-Filter und Rewrite fuer Prompts."""

import re
import sys
import json
from datetime import datetime

# BLOCK-Muster: direkte Nachahmungswuensche
BLOCK_PATTERNS = [
    r"herge",
    r"herge["]", r"herge[m]    r"1[:]|(zu)? 1|eins(:|\s)zu\s*1",
    r"tim\s*und\s*struppi",
    r"tintin",
    r"milou",
    r"tr"][i\s_n\s]+
]
# REWRITE-Muster: zu abstraktem Ligne-Claire-Stil umschreiben
REWRITE_MAPPINGS = [
    (r"frankobelgisch", "europaeischer Abenteuercomic des 20. Jahrhunderts"),
    (r"bande\s*dessinee", "europaeische Comic-Stilrichtung"),
    (r"clear\s*line", "klare Konturen und flaeche Kolorierung"),
]

def check_prompt(prompt):
    matches = []
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            matches.append(pattern)
    return matches

def rewrite_prompt(prompt):
    for pattern, replacement in REWRITE_MAPPINGS:
        prompt = re.sub(pattern, replacement, prompt, flags=re.IGNORECASE)
    return prompt

def classify_prompt(prompt):
    matches = check_prompt(prompt)
    rewritten = rewrite_prompt(prompt)
    if matches:
        return {"decision": "block", "matches": matches, "rewritten": rewritten}
    if re.search(r"linie|ligne|clear\s*line|klare\s*kontur|flaeche\s*farbe", prompt, re.IGNORECASE):
        return {"decision": "allow", "matches": [], "rewritten": prompt}
    return {"decision": "rewrite", "matches": [], "rewritten": rewritten}

def save_review_entry(result, raw, reason=""):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "raw_prompt": raw,
        "result": result,
        "reason": reason
    }
    print(json.dumps(entry))

def run_tests():
    tests = [
        ("zeichne wie herge", "block"),
        ("zeichne wie Tim und Struppi", "block"),
        ("tintin im frankobelgischen stil", "block"),
        ("eine figur im klaren linien stil", "allow"),
        ("comic im clearen linien stil", "allow"),
    ]
    passed = 0
    for prompt, expected in tests:
        result = classify_prompt(prompt)
        if result["decision"] == expected:
            passed += 1
            print(f"PASS: {prompt} -> {result['decision']}")
        else:
            print(f"FAIL: {prompt} -> {result['decision']} (expected {expected})")
    print(f"Tests: {passed}/{len(tests)} passed")
    return passed == len(tests)

def main():
    if len(sys.argv) < 2:
        print("usage: python prompt_gate.py <prompt>")
        print("   or: python prompt_gate.py --test")
        sys.exit(1)
    prompt = " ".join(sys.argv[1:])
    if prompt == "--test":
        run_tests()
        sys.exit(0)
    result = classify_prompt(prompt)
    print(f"Decision: {result['decision']}")
    if result['matches']:
        print(f"Blocked reasons: {result['matches']}")
    if result['decision'] in ('rewrite', 'block'):
        print(f"Rewritten: {result['rewritten']}")
    if result['decision'] == 'rewrite':
        save_review_entry(result, prompt, "auto-rewrite")
    elif result['decision'] == 'block':
        save_review_entry(result, prompt, "blocked-input")

if __name__ == "__main__":
    main()
