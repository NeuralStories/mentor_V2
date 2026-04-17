"""
Smoke test del parser.
"""
import sys
from pathlib import Path

from core.tools.document_parser import DocumentParser


def main():
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.smoke_parser <archivo>")
        sys.exit(1)

    path = Path(sys.argv[1])
    valid, message = DocumentParser.validate_file(str(path))
    print(f"Validación: {valid} | {message}")
    if not valid:
        sys.exit(2)

    content, metadata = DocumentParser.parse_file(path)
    for key, value in metadata.items():
        print(f"{key}: {value}")
    print(content[:400].replace("\n", " "))


if __name__ == "__main__":
    main()
