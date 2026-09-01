"""Patch p4a's opencv recipe to find numpy 1.x headers.

p4a's opencv recipe hardcodes the numpy 2.x include path
``numpy/_core/include``, but numpy 1.26.x keeps its headers in
``numpy/core/include``. This script rewrites the recipe to use the 1.x path
so opencv can find ``numpy/ndarrayobject.h``.

Usage: python patch_p4a_opencv.py <p4a-source-dir>
"""

import io
import os
import sys


def main():
    if len(sys.argv) < 2:
        print("usage: patch_p4a_opencv.py <p4a-source-dir>")
        return 1

    root = sys.argv[1]
    recipe_path = os.path.join(
        root, "pythonforandroid", "recipes", "opencv", "__init__.py"
    )
    if not os.path.isfile(recipe_path):
        print(f"recipe not found: {recipe_path}")
        return 1

    with io.open(recipe_path, "r", encoding="utf-8") as f:
        text = f.read()

    old = '"numpy/_core/include"'
    new = '"numpy/core/include"'
    if old not in text:
        print(f"pattern {old} not found; opencv recipe may be already patched")
        return 0

    text = text.replace(old, new)
    with io.open(recipe_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"patched opencv recipe: {recipe_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
