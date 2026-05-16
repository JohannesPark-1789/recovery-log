"""
Build two artifacts from the receipt PDFs:

1. ../../costs.json — served by GitHub Pages alongside index.html. The PWA
   fetches this at startup and merges into state.costs (dedup by date+
   label+amount+vendor). Idempotent — re-running the import only adds
   new entries.

2. _import_costs.console.js — legacy DevTools console snippet for the
   PC-paste workflow. Kept for users who don't want to redeploy.
"""
import os, io, json, base64, sys
import pypdfium2 as pdfium
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.chdir(r'C:\Dev\recovery-log\docs\receipt')

sources = [
    {
        'pdf': '외래_진료비계산서영수증.pdf',
        'cost': {
            'date': '2026-05-09',
            'category': 'treatment',
            'type': 'expense',
            'payer': 'self',
            'label': '외래 진찰료 (정형외과)',
            'vendor': '청구성심병원',
            'amount': 59890,
            'note': '총진료비 ₩87,634 / 본인부담 ₩59,890 (카드 일시불, 5107****, 승인 31934732). 영수증번호 20260509-072.'
        }
    },
    {
        'pdf': '조제약복약안내.pdf',
        'cost': {
            'date': '2026-05-09',
            'category': 'medication',
            'type': 'expense',
            'payer': 'self',
            'label': '처방약 (건일로딘정·에릭손정·스테렌정)',
            'vendor': '가온약국',
            'amount': 3000,
            'note': '약제비 총액 ₩10,000 / 본인부담 ₩3,000 (현금영수증). 영수증번호 20260509-00017. 투약일수 2일 · 1일 3회 식후30분.'
        }
    },
    {
        'pdf': '입원_퇴원_진료비계산서영수증.pdf',
        'cost': {
            'date': '2026-05-15',
            'category': 'admission',
            'type': 'expense',
            'payer': 'self',
            'label': '입원 4박5일 진료비 (병실 312, 4인실)',
            'vendor': '청구성심병원',
            'amount': 2754090,
            'note': '진료기간 2026-05-11 ~ 05-15. 총진료비 ₩5,484,254 (급여 본인 1,032,937 + 공단 2,730,120 + 선택진료 87,297 + 비급여 1,633,900) / 본인부담 ₩2,754,090 (카드 일시불, 4619****, 승인 19904100). 영수증번호 20260515-S430. 세부산정내역서 별첨.'
        }
    },
    {
        'pdf': '입원_중간_진료비계산서영수증.pdf',
        'cost': {
            'date': '2026-05-15',
            'category': 'admission',
            'type': 'expense',
            'payer': 'self',
            'label': '입원 중간정산 (기타 비급여)',
            'vendor': '청구성심병원',
            'amount': 23000,
            'note': '총진료비 ₩23,000 (전액 기타 비급여) / 본인부담 ₩23,000 (카드 일시불, 4619****, 승인 18904100). 영수증번호 20260515-S43.'
        }
    },
]

TARGET_WIDTH = 1400
JPEG_QUALITY = 78


def pdf_first_page_to_jpeg_dataurl(pdf_path: str) -> tuple[str, int]:
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[0]
    scale = TARGET_WIDTH / page.get_width()
    pil = page.render(scale=scale).to_pil()
    if pil.mode != 'RGB':
        bg = Image.new('RGB', pil.size, (255, 255, 255))
        bg.paste(pil, mask=pil.split()[-1] if pil.mode == 'RGBA' else None)
        pil = bg
    buf = io.BytesIO()
    pil.save(buf, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    raw = buf.getvalue()
    return f'data:image/jpeg;base64,{base64.b64encode(raw).decode("ascii")}', len(raw)


entries = []
total_bytes = 0
for src in sources:
    print(f'Rendering: {src["pdf"]}')
    data_url, sz = pdf_first_page_to_jpeg_dataurl(src['pdf'])
    total_bytes += sz
    print(f'  jpeg size: {sz:,} bytes')
    entries.append({**src['cost'], 'receipt': data_url})

print(f'\nTotal receipt-jpeg payload: {total_bytes:,} bytes (~{total_bytes/1024:.0f} KB)')

# 1) costs.json at repo root (served by GitHub Pages next to index.html)
costs_json_path = os.path.join('..', '..', 'costs.json')
payload = {
    'schemaVersion': 1,
    'generatedAt': None,  # intentionally null — let the PWA show "imported D{N}"
    'sourceNote': 'Auto-generated from docs/receipt/*.pdf by docs/receipt/_build_costs.py',
    'costs': entries
}
with open(costs_json_path, 'w', encoding='utf-8') as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=2)
print(f'Wrote {costs_json_path} ({os.path.getsize(costs_json_path):,} bytes)')

# 2) Console snippet (kept for backwards-compat)
js = f'''(() => {{
  const KEY = 'recovery_log_v1';
  let state;
  try {{ state = JSON.parse(localStorage.getItem(KEY) || '{{}}'); }}
  catch (e) {{ console.error('Could not parse existing state:', e); return; }}
  if (!Array.isArray(state.costs)) state.costs = [];

  const incoming = {json.dumps(entries, ensure_ascii=False, indent=2)};

  const key = c => `${{c.date}}|${{c.label}}|${{c.amount}}|${{c.vendor || ''}}`;
  const existing = new Set(state.costs.map(key));
  let added = 0, skipped = 0;
  for (const e of incoming) {{
    if (existing.has(key(e))) {{ skipped++; continue; }}
    const surgery = (state.profile && state.profile.date) || '2026-05-11';
    const [sy, sm, sd] = surgery.split('-').map(Number);
    const [dy, dm, dd] = e.date.split('-').map(Number);
    const day = Math.floor((Date.UTC(dy, dm - 1, dd) - Date.UTC(sy, sm - 1, sd)) / 86400000);
    state.costs.push({{ id: Date.now() + Math.floor(Math.random() * 1000) + added, day, ...e }});
    added++;
  }}

  state.costs.sort((a, b) => (b.date + String(b.id)).localeCompare(a.date + String(a.id)));
  localStorage.setItem(KEY, JSON.stringify(state));
  console.log(`Cost import done: ${{added}} added, ${{skipped}} skipped (duplicates).`);
  console.log('Reloading page in 1s...');
  setTimeout(() => location.reload(), 1000);
}})();
'''

with open('_import_costs.console.js', 'w', encoding='utf-8') as fh:
    fh.write(js)
print(f'Wrote _import_costs.console.js ({len(js):,} bytes)')
