"""Uso: python3 -m quizfmt [quiz_root]   (por defecto: ./quiz)"""
import sys
from pathlib import Path

from quizfmt import quiz_files, validate_tree

root = Path(sys.argv[1] if len(sys.argv) > 1 else "quiz")
if not root.is_dir():
    print(f"No existe {root}/")
    sys.exit(1)
issues = validate_tree(root)
if issues:
    print("\n".join(f"- {i}" for i in issues))
    sys.exit(1)
print(f"OK: {len(quiz_files(root))} archivo(s) válidos")
