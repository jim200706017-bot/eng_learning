"""vocab-view: Generate vocabulary library overview from JSON files."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
INDEX = ROOT / "index.json"
OUTPUT = ROOT / "README.md"

def load_index():
    if INDEX.exists():
        return json.loads(INDEX.read_text(encoding="utf-8"))
    return {}

def get_word_data(word, index_entry):
    word_file = ROOT / f"{word}.json"
    if word_file.exists():
        return json.loads(word_file.read_text(encoding="utf-8"))
    return index_entry

def main():
    index = load_index()
    words = []

    for word, entry in index.items():
        data = get_word_data(word, entry)
        words.append({
            "word": word,
            "domain": data.get("domain", entry.get("domain", "general")),
            "cefr": data.get("cefr", entry.get("cefr", "—")),
            "status": data.get("status", entry.get("status", "receptive")),
            "srs_stage": data.get("srs_stage", entry.get("srs_stage", 0)),
            "next_review": data.get("srs_next", entry.get("srs_next", "—")),
            "added_date": data.get("added_date", entry.get("added_date", "—")),
        })

    words.sort(key=lambda w: w["added_date"])

    total = len(words)
    receptive = sum(1 for w in words if w["status"] == "receptive")
    productive = sum(1 for w in words if w["status"] == "productive")
    domains = {}
    for w in words:
        domains[w["domain"]] = domains.get(w["domain"], 0) + 1

    lines = [
        "# Vocabulary Library",
        "",
        "> Auto-generated vocabulary library overview. Run `python vocab-view.py` to refresh.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total Words | {total} |",
        f"| Receptive | {receptive} |",
        f"| Productive | {productive} |",
    ]
    for domain, count in sorted(domains.items()):
        lines.append(f"| {domain.title()} | {count} |")

    lines += [
        "",
        "## All Words",
        "",
        "| # | Word | Domain | CEFR | Status | SRS Stage | Next Review | Added |",
        "|---|------|--------|------|--------|-----------|-------------|-------|",
    ]

    for i, w in enumerate(words, 1):
        lines.append(
            f"| {i} | {w['word']} | {w['domain']} | {w['cefr']} | {w['status']} | {w['srs_stage']} | {w['next_review']} | {w['added_date']} |"
        )

    lines += [
        "",
        "---",
        "> Vocabulary JSON files: `vocabulary/<word>.json`",
        "> Index: `vocabulary/index.json`",
        "",
    ]

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"vocab-view: generated {OUTPUT} ({total} words)")


if __name__ == "__main__":
    main()
