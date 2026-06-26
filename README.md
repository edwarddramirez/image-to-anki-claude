# Anki Vocab Upload Workflow

Workflow for converting vocabulary images into Anki flashcards.
Full setup reference: https://claude.ai/chat/164dc35d-7a65-445e-ab9e-003e62ca373d

---

## Prerequisites

- Anki open on Windows with AnkiConnect add-on installed (code: `2055492159`)
- WSL with mirrored networking (`C:\Users\<you>\.wslconfig` contains `networkingMode=mirrored`)
- `requests` installed: `pip install requests`
- `anki_flashcards.py` and `hindi_to_anki.py` in your working directory

Quick sanity check — AnkiConnect is reachable:
```bash
curl http://localhost:8765
# Expected: {"result": "AnkiConnect v.6", "error": null}
```

---

## Step 1 — Convert vocab images to CSV

Take a photo or screenshot of the vocab page and send it to Claude with this prompt:

> "Please extract all vocab words into a CSV with columns: `hindi, pronunciation, english`.
> Dedupe by word — if a word appears multiple times, keep one row.
> If multiple meanings exist on one line, separate with semicolons."

Claude will return a CSV. Save it as `hindi_vocab.csv` (or append new words to the existing file).

### CSV format

```
hindi,pronunciation,english
नमस्ते,namaste,hello; goodbye
मैं,maī,I
```

---

## Step 2 — Preview before uploading (dry run)

Always do this first to confirm what will be added vs skipped:

```bash
python hindi_to_anki.py hindi_vocab.csv --dry-run
```

Output will show:
- ✅ Cards that **would be added**
- ⏭️ Cards that **would be skipped** (already exist in the deck)

The skip check works by fetching all existing card fronts from Anki and comparing locally — no duplicates will be created.

---

## Step 3 — Upload cards

Once the dry run looks good:

```bash
python hindi_to_anki.py hindi_vocab.csv
```

Cards are created in Anki under:
```
TY Hindi :: Chapter 1: Greetings, Questions, Adjectives
```

Card format:
- **Front:** Hindi word (e.g. `नमस्ते`)
- **Back:** English meaning + pronunciation (e.g. `hello; goodbye (namaste)`)

To target a different deck or subdeck:
```bash
python hindi_to_anki.py hindi_vocab.csv --deck "TY Hindi" --subdeck "Chapter 2: Family"
```

---

## Files

| File | Purpose |
|---|---|
| `anki_flashcards.py` | `AnkiClient` and `Flashcard` classes — core API wrapper |
| `hindi_to_anki.py` | CLI script to load a CSV and upload to Anki |
| `hindi_vocab.csv` | Master vocab list — append new chapters here |

---

## Troubleshooting

**AnkiConnect not reachable:**
- Make sure Anki is open on Windows
- Confirm `.wslconfig` has `networkingMode=mirrored` and WSL was restarted after (`wsl --shutdown`)
- Check AnkiConnect config in Anki has `"webBindAddress": "0.0.0.0"`

**Cards not showing up in Anki:**
- The deck name must match exactly — check spelling and capitalization
- Re-run with `--dry-run` to confirm the cards are being targeted at the right deck
