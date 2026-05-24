"""Render pill photos from 복약안내문.pdf as 200x200 JPEG and emit base64.

Used by SEED_IMAGES in index.html. Re-run if the source PDF changes:
    python docs/medication/_extract_pills.py
The script prints a JSON object {key: b64} that should replace the
pill_* entries in SEED_IMAGES.
"""
import json
import io
import base64
import os
import fitz
from PIL import Image

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, '복약안내문.pdf')


def sq(cx, cy, side):
    half = side // 2
    return (cx - half, cy - half, cx + half, cy + half)


# Hand-tuned crop centers (cx, cy, side) inside a 200dpi render of the page.
# Each box squares onto a single pill so it reads as a recognizable thumbnail
# at 72×72 in the PWA medication card.
CROPS = {
    'cefradine': sq(200,  560, 200),   # 한미세프라딘 캡슐
    'lacstar':   sq(200,  910, 180),   # 락스타 더블 캡슐
    'rodin':     sq(200, 1280, 170),   # 건일로딘정
    'stillen':   sq(250, 1600, 170),   # 스테렌정 60mg
}


def main():
    doc = fitz.open(SRC)
    page = doc[0]
    pix = page.get_pixmap(dpi=200)
    img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)

    out = {}
    for key, box in CROPS.items():
        crop = img.crop(box)
        crop = crop.resize((200, 200), Image.LANCZOS)
        buf = io.BytesIO()
        crop.save(buf, 'JPEG', quality=78)
        out[key] = base64.b64encode(buf.getvalue()).decode('ascii')
    print(json.dumps(out))


if __name__ == '__main__':
    main()
