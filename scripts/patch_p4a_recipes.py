"""Patch p4a recipes for compatibility with numpy 1.x + NDK 25b + GitHub CI.

Two fixes applied to a local clone of python-for-android (loaded via buildozer's
``p4a.source_dir``):

1. opencv recipe: p4a hardcodes the numpy 2.x include path ``numpy/_core/include``,
   but numpy 1.26.x keeps headers in ``numpy/core/include``. Rewrite to the 1.x
   path so opencv finds ``numpy/ndarrayobject.h``.

2. libthorvg recipe: it does ``clang_lib_dir = glob(pattern)[0]`` to find the
   OpenMP ``libomp.so``. On some NDK layouts the glob matches nothing, raising
   an IndexError. Make it tolerant: if libomp is missing, skip copying it
   (OpenMP is optional for thorvg).

Usage: python patch_p4a_recipes.py <p4a-source-dir>
"""

import io
import os
import sys


def patch_file(path, replacements):
    if not os.path.isfile(path):
        return f"not found: {path}"
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    changed = False
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            changed = True
    if changed:
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return f"patched: {path}"
    return f"no change: {path}"


def main():
    if len(sys.argv) < 2:
        print("usage: patch_p4a_recipes.py <p4a-source-dir>")
        return 1

    root = sys.argv[1]

    # 1) opencv numpy include path (numpy 1.x uses 'core', not '_core')
    opencv = os.path.join(root, "pythonforandroid", "recipes", "opencv", "__init__.py")
    print(patch_file(opencv, [('"numpy/_core/include"', '"numpy/core/include"')]))

    # 2) libthorvg: tolerate a missing libomp (glob may match nothing)
    thorvg = os.path.join(root, "pythonforandroid", "recipes", "libthorvg", "__init__.py")
    old_block = (
        '            clang_lib_dir = glob(pattern)[0]\n'
        '            libomp = join(clang_lib_dir, "libomp.so")\n'
        '            shprint(sh.cp, libomp, join("install", "lib"))\n'
    )
    new_block = (
        '            clang_lib_dirs = glob(pattern)\n'
        '            if clang_lib_dirs:\n'
        '                libomp = join(clang_lib_dirs[0], "libomp.so")\n'
        '                shprint(sh.cp, libomp, join("install", "lib"))\n'
        '            else:\n'
        '                print("WARNING: libomp not found, skipping (openmp disabled)")\n'
    )
    print(patch_file(thorvg, [(old_block, new_block)]))

    return 0


if __name__ == "__main__":
    sys.exit(main())
