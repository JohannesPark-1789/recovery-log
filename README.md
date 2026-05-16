# Recovery Log

쇄골 ORIF 수술 회복 추적용 PWA. 박해준 · 2026-05-11 수술 기준.

## Features

- **Today** · Patient banner (ID·Room), 일일 NRS 통증 기록, vitals 로그 (SpO₂·PR·RR·BP·Temp·Sleep), 14일 통증 추세선
- **Move** · 회복 단계별 재활운동 체크리스트 + ROM (굴곡/외전/외회전) 추적
- **Plan** · 외래·드레싱·복약 일정 + 처방약 5종 라이브러리 (약 사진 + 성분 + 효능 + 주의사항)
- **Phase** · 8단계 회복 타임라인, 수술부 사진 / X-ray / 진단서 기록, Fraunces serif 저널 (사진 첨부 가능)
- **Learn** · **의학용어집 66개 항목** 12개 카테고리 (해부학·진단·수술·골절치유·세포·조직회복·통증·활력징후·재활·약리·의료기기·상처관리), 한/영/약어 검색 지원
- **Cost** · 사고 관련 전체 비용 추적 (진료비·약값·교통·보조용품·소모품·입원비·기타), 영수증 사진 첨부, 보험·산재·가족 환급 차감해 순 본인부담 계산, 카테고리별 비중 표시
- **Data** · JSON export/import, Markdown 보고서 복사, 프로필 관리

모든 날짜·시간은 **KST (Asia/Seoul) 기준**으로 고정되어 기기 시간대와 무관하게 동작합니다.

## First-run seeded data

- **Patient:** 박해준 (PT 01463490, RM 312, 청구성심병원 정형외과)
- **Vitals D1:** 2026-05-11 20:30 · SpO₂ 97%, PR 64bpm, RR 8, PI 10.6% (mobiCARE +Pulse)
- **Medications:** 칼디플러스정, 베베란정, 락스타더블캡슐, 스테렌정, 뉴트라셋세미정 (각 효능·복용시간·주의사항)
- **Glossary:** 사고 기록의 모든 의료 용어 정리 (Clavicle / ORIF / Osteoblast / NRS / SpO₂ / Pendulum exercise / Wolff law / Athletic bradycardia 등)

## Deploy to GitHub Pages

1. 이 폴더 전체를 GitHub repo의 root 또는 `docs/` 폴더에 push
2. repo Settings → Pages → Source 를 `main` branch / `/` (root) 또는 `/docs` 로 지정
3. 몇 분 후 `https://<username>.github.io/<repo-name>/` 에서 접근 가능
4. 모바일 Safari/Chrome 으로 접속 → 공유 → 홈 화면에 추가 → 풀스크린 앱으로 작동

## Local preview

```bash
python3 -m http.server 8080
# http://localhost:8080
```

## Data

- 모든 데이터는 브라우저 `localStorage` 에 저장됨
- 기기 변경/브라우저 데이터 삭제 시 손실되므로 **정기적 JSON export 권장**
- 사진은 1200px 로 압축되어 JPEG 70% 품질로 저장 (localStorage 용량 절약)
- 첫 실행 시 D1 mobiCARE 측정값이 자동 시드됨

## Files

```
index.html      # 단일 페이지 앱 (HTML + CSS + JS + 임베드 약 사진 + 글로서리)
manifest.json   # PWA manifest
sw.js           # Service worker (오프라인 캐싱)
icon-192.png    # 앱 아이콘
icon-512.png    # 앱 아이콘
```

## Customization

- 수술일 변경: 앱 내 Data 탭 → Surgery date
- 환자 정보: Data 탭 → Patient ID / Room
- 재활 운동 추가/수정: `index.html` 내 `EXERCISES_BY_PHASE` 상수
- 회복 단계 조정: `PHASES` 배열
- 의학 용어 추가: `GLOSSARY` 배열 (cat / en / ko / def)
- 약 추가: `MEDICATIONS` 배열
- 비용 카테고리 추가/변경: `COST_CATEGORIES`, `COST_CAT_LABELS`, `COST_CAT_EN`
- 결제 출처 추가: `COST_PAYERS`, `COST_PAYER_LABELS`

## Disclaimer

이 앱은 환자 본인의 학습·기록 목적으로 만들어졌으며,
의학적 의사결정의 근거가 될 수 없습니다.
증상에 대한 판단은 항상 담당의의 진료를 따르세요.

## License

Personal use only.
