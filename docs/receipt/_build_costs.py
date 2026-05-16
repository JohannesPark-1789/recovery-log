"""
Convert the 4 actual receipt PDFs into JPEG dataURLs and emit a JS snippet
that the user can paste into the app's DevTools console to add the cost
entries (with attached receipts) to existing localStorage data without
overwriting anything else.
"""
import os, io, json, base64, sys
import pypdfium2 as pdfium
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.chdir(r'C:\Dev\recovery-log\docs\receipt')

# (filename, target_width_px) — wider for the dense incoming bill so amounts stay legible
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
    """Render page 1 of a PDF to a JPEG dataURL, capped at TARGET_WIDTH px wide."""
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[0]
    # Determine scale so width hits TARGET_WIDTH px
    base_w_pt = page.get_width()
    scale = TARGET_WIDTH / base_w_pt
    pil = page.render(scale=scale).to_pil()
    # White background to avoid transparent JPEG quirks
    if pil.mode != 'RGB':
        bg = Image.new('RGB', pil.size, (255, 255, 255))
        bg.paste(pil, mask=pil.split()[-1] if pil.mode == 'RGBA' else None)
        pil = bg
    buf = io.BytesIO()
    pil.save(buf, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    raw = buf.getvalue()
    b64 = base64.b64encode(raw).decode('ascii')
    return f'data:image/jpeg;base64,{b64}', len(raw)


# Build entries
entries = []
total_bytes = 0
for src in sources:
    pdf_path = src['pdf']
    print(f'Rendering: {pdf_path}')
    data_url, sz = pdf_first_page_to_jpeg_dataurl(pdf_path)
    total_bytes += sz
    print(f'  jpeg size: {sz:,} bytes')
    entry = dict(src['cost'])
    entry['receipt'] = data_url
    entries.append(entry)

print()
print(f'Total receipt-jpeg payload: {total_bytes:,} bytes (~{total_bytes/1024:.0f} KB)')

# Emit the JS snippet
js = f'''(() => {{
  const KEY = 'recovery_log_v1';
  let state;
  try {{ state = JSON.parse(localStorage.getItem(KEY) || '{{}}'); }}
  catch (e) {{ console.error('Could not parse existing state:', e); return; }}
  if (!Array.isArray(state.costs)) state.costs = [];

  const incoming = {json.dumps(entries, ensure_ascii=False, indent=2)};

  // Dedupe by (date+label+amount+vendor) — re-running the snippet is safe.
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
  console.log('Reloading page in 1s so the Cost tab picks up the new entries...');
  setTimeout(() => location.reload(), 1000);
}})();
'''

out_path = r'C:\Dev\recovery-log\docs\receipt\_import_costs.console.js'
with open(out_path, 'w', encoding='utf-8') as fh:
    fh.write(js)
print(f'Wrote {out_path} ({len(js):,} bytes)')
