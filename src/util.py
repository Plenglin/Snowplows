"""
Misc. functions
"""
import random
import string

LETTERS = string.ascii_letters + string.digits + '-_'


def offset_box(cx, cy, length, width):
    hl = length / 2
    hw = width / 2
    x1 = float(cx - hl)
    x2 = float(cx + hl)
    y1 = float(cy - hw)
    y2 = float(cy + hw)
    return [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]


def random_string(n, charset=LETTERS) -> str:
    return ''.join(random.choice(charset) for _ in range(n))

