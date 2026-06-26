"""
Usage:
    python hindi_to_anki.py hindi_vocab.csv
    python hindi_to_anki.py hindi_vocab.csv --dry-run
    python hindi_to_anki.py hindi_vocab.csv --deck "TY Hindi" --subdeck "Chapter 1: Greetings, Questions, Adjectives"

Requires anki_flashcards.py in the same directory.
"""

import csv
import sys
import argparse
from anki_flashcards import AnkiClient, Flashcard


DEFAULT_DECK = "TY Hindi"
DEFAULT_SUBDECK = "Chapter 1: Greetings, Questions, Adjectives"


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} rows from {path}")
    return rows


def csv_to_flashcards(rows: list[dict], deck: str, subdeck: str) -> list[Flashcard]:
    cards = []
    for row in rows:
        hindi = row["hindi"].strip()
        pronunciation = row["pronunciation"].strip()
        english = row["english"].strip()

        cards.append(Flashcard(
            deck=deck,
            subdeck=subdeck,
            front=hindi,
            back=f"{english} ({pronunciation})",
            tags=["hindi", "ty-hindi"],
        ))
    return cards


def main():
    parser = argparse.ArgumentParser(description="Import Hindi vocab CSV into Anki")
    parser.add_argument("csv_file", help="Path to the CSV file")
    parser.add_argument("--deck", default=DEFAULT_DECK, help="Anki deck name")
    parser.add_argument("--subdeck", default=DEFAULT_SUBDECK, help="Anki subdeck name")
    parser.add_argument("--dry-run", action="store_true", help="Preview what would be added without writing to Anki")
    args = parser.parse_args()

    client = AnkiClient()

    if not client.ping():
        print("Error: Could not reach AnkiConnect. Is Anki open?")
        sys.exit(1)

    rows = load_csv(args.csv_file)
    cards = csv_to_flashcards(rows, args.deck, args.subdeck)

    if args.dry_run:
        client.dry_run(cards)
        sys.exit(0)

    new_cards, skipped_cards = client.filter_new_cards(cards)

    if skipped_cards:
        print(f"Skipping {len(skipped_cards)} cards already in deck:")
        for card in skipped_cards:
            print(f"  - {card.front}")

    if not new_cards:
        print("Nothing to add — all cards already exist in deck.")
        sys.exit(0)

    note_ids = client.add_cards(new_cards)

    added = sum(1 for nid in note_ids if nid is not None)
    failed = sum(1 for nid in note_ids if nid is None)
    print(f"Done! Added: {added}, Skipped (already existed): {len(skipped_cards)}, Failed: {failed}")


if __name__ == "__main__":
    main()
