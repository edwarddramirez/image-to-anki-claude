import requests
from dataclasses import dataclass


ANKI_CONNECT = "http://localhost:8765"


@dataclass
class Flashcard:
    deck: str
    subdeck: str
    front: str
    back: str
    tags: list[str] = None

    @property
    def full_deck_name(self) -> str:
        return f"{self.deck}::{self.subdeck}"


class AnkiClient:
    def __init__(self, url: str = ANKI_CONNECT, api_key: str = None):
        self.url = url
        self.api_key = api_key

    def _invoke(self, action: str, **params) -> dict:
        payload = {"action": action, "version": 6, "params": params}
        if self.api_key:
            payload["key"] = self.api_key

        response = requests.post(self.url, json=payload)
        response.raise_for_status()

        result = response.json()
        # Only raise for top-level errors — addNotes returns per-note errors in result list
        if result.get("error") and not isinstance(result.get("result"), list):
            raise RuntimeError(f"AnkiConnect error: {result['error']}")

        return result["result"]

    def ping(self) -> bool:
        """Check if AnkiConnect is reachable."""
        try:
            self._invoke("version")
            return True
        except Exception:
            return False

    def _ensure_deck_exists(self, deck_name: str) -> None:
        """Create deck (and parent) if it doesn't already exist."""
        self._invoke("createDeck", deck=deck_name)

    def add_card(self, card: Flashcard) -> int:
        """
        Add a single flashcard to Anki.
        Creates the deck/subdeck if they don't exist.
        Returns the new note ID.
        """
        self._ensure_deck_exists(card.full_deck_name)

        note = {
            "deckName": card.full_deck_name,
            "modelName": "Basic",
            "fields": {
                "Front": card.front,
                "Back": card.back,
            },
            "tags": card.tags or [],
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck",
            },
        }

        note_id = self._invoke("addNote", note=note)
        return note_id

    def get_existing_fronts(self, deck: str, subdeck: str = None) -> set[str]:
        """
        Return a set of all Front field values already in a deck (or subdeck).
        """
        full_deck = f"{deck}::{subdeck}" if subdeck else deck
        note_ids = self._invoke("findNotes", query=f'deck:"{full_deck}"')
        if not note_ids:
            return set()
        notes_info = self._invoke("notesInfo", notes=note_ids)
        return {note["fields"]["Front"]["value"] for note in notes_info}

    def filter_new_cards(self, cards: list[Flashcard]) -> tuple[list[Flashcard], list[Flashcard]]:
        """
        Split cards into (new, skipped) by checking existing fronts per deck.
        Returns (new_cards, skipped_cards).
        """
        # Group by deck to minimize API calls
        decks: dict[tuple, set[str]] = {}
        for card in cards:
            key = (card.deck, card.subdeck)
            if key not in decks:
                decks[key] = self.get_existing_fronts(card.deck, card.subdeck)

        new_cards, skipped_cards = [], []
        for card in cards:
            key = (card.deck, card.subdeck)
            if card.front in decks[key]:
                skipped_cards.append(card)
            else:
                new_cards.append(card)
                decks[key].add(card.front)  # prevent dupes within the batch itself

        return new_cards, skipped_cards

    def dry_run(self, cards: list[Flashcard]) -> None:
        """
        Preview what would be added/skipped without writing anything to Anki.
        """
        new_cards, skipped_cards = self.filter_new_cards(cards)

        print(f"\n{'='*50}")
        print(f"DRY RUN — no cards will be added")
        print(f"{'='*50}")
        print(f"\n✅ Would ADD ({len(new_cards)}):")
        for card in new_cards:
            print(f"  [{card.full_deck_name}]  {card.front}  →  {card.back}")

        if skipped_cards:
            print(f"\n⏭️  Would SKIP ({len(skipped_cards)}) — already in deck:")
            for card in skipped_cards:
                print(f"  {card.front}")

        print(f"\n{'='*50}")
        print(f"Summary: {len(new_cards)} to add, {len(skipped_cards)} to skip")
        print(f"{'='*50}\n")

    def add_cards(self, cards: list[Flashcard]) -> list[int]:
        """
        Add multiple flashcards, grouping by deck for efficiency.
        Returns a list of new note IDs (None for any that failed/were duplicates).
        """
        # Ensure all decks exist
        deck_names = {card.full_deck_name for card in cards}
        for deck_name in deck_names:
            self._ensure_deck_exists(deck_name)

        notes = [
            {
                "deckName": card.full_deck_name,
                "modelName": "Basic",
                "fields": {
                    "Front": card.front,
                    "Back": card.back,
                },
                "tags": card.tags or [],
                "options": {
                    "allowDuplicate": False,
                    "duplicateScope": "deck",
                },
            }
            for card in cards
        ]

        results = self._invoke("addNotes", notes=notes)
        # results is a list where each entry is either a note ID (int) or None (duplicate/error)
        return results


# --- Example usage ---
if __name__ == "__main__":
    client = AnkiClient()

    if not client.ping():
        print("Could not reach AnkiConnect. Is Anki open?")
        exit(1)

    # Single card
    card = Flashcard(
        deck="Languages",
        subdeck="French",
        front="What is 'hello' in French?",
        back="Bonjour",
        tags=["greetings"],
    )
    note_id = client.add_card(card)
    print(f"Added card with note ID: {note_id}")

    # Multiple cards at once
    cards = [
        Flashcard(deck="Languages", subdeck="French", front="Thank you", back="Merci"),
        Flashcard(deck="Languages", subdeck="French", front="Goodbye", back="Au revoir"),
        Flashcard(deck="Languages", subdeck="Spanish", front="Hello", back="Hola"),
    ]
    note_ids = client.add_cards(cards)
    print(f"Added cards with note IDs: {note_ids}")
