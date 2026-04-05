import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MAX_NAME_LENGTH = 4


def clean_word_list(path: Path) -> list[str]:
    cleaned = []
    seen = set()

    for line in path.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if not word:
            continue

        if len(word) > MAX_NAME_LENGTH:
            continue

        lowered = word.lower()
        if lowered == "list" or lowered in seen:
            continue

        seen.add(lowered)
        cleaned.append(word.title())

    return cleaned


def main() -> None:
    adjectives = clean_word_list(DATA_DIR / "adj.txt")
    animals = clean_word_list(DATA_DIR / "animals.txt")

    output = {
        "adjectives": adjectives,
        "animals": animals,
    }

    output_path = DATA_DIR / "name_lists.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(adjectives)} adjectives and {len(animals)} animals to {output_path}")


if __name__ == "__main__":
    main()
