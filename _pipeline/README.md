# CV → 홈페이지 자동화 파이프라인

OneDrive 의 **`information.xlsx`** 한 곳만 관리하면, 이 파이프라인이 al-folio 홈페이지
( https://sjh97.github.io ) 콘텐츠를 자동으로 만들어 배포합니다.

```
information.xlsx (OneDrive)            ┌─ _bibliography/papers.bib   (Publications)
        │  rclone 동기화               ├─ _data/cv_sections.yml      (CV 페이지)
        ▼                              ├─ _news/*.md                 (소식 = 언론보도)
  generate.py  ──────────────────────▶├─ _data/socials.yml          (소셜 아이콘)
        ▲                              └─ _pages/about.md            (자기소개)
   profile.yml (사이트 전용 정보)
        │  git push → GitHub Actions 자동 빌드/배포
        ▼
   https://sjh97.github.io
```

## 평소 사용법 (코드 한 줄 안 침)

1. OneDrive `바탕 화면/rholab/CV 관리/information.xlsx` 에서 정보 추가/수정 (평소 CV 만들 때처럼).
2. 터미널에서:
   ```bash
   cd ~/sjh97.github.io/_pipeline
   ./update.sh
   ```
   → OneDrive 동기화 → 콘텐츠 생성 → 커밋/푸시 → 1~3분 뒤 사이트 반영.

옵션:
- `./update.sh --no-push` : 푸시 없이 로컬 생성만 (검토용)
- `./update.sh --no-pull` : OneDrive 동기화 건너뛰고 생성만

---

## 어떤 정보를 주면 홈페이지가 채워지나?

### A. 엑셀(`information.xlsx`)에서 관리 — 자동 반영 (지금 그대로 쓰면 됨)
| 시트 | 홈페이지 위치 | 핵심 컬럼 |
|------|---------------|-----------|
| **Publication** | Publications 페이지 + about 강조 | 제목, 공동1저자/그외저자/교신저자, 저널명, Volume, 페이지, 연도, doi, IF |
| **Education** | CV › Education | 학위, 학과, 소속, 국가, 시작연도, 졸업연도, 지도교수 |
| **Award & Scholarship** | CV › Awards / Scholarships | 구분(수상/장학금), 수상명, 기관, 국가, 연도, 연도끝, 금액 |
| **Conference** | CV › Conference Presentations | 학회명, 도시, 국가, 월, 연도 |
| **Patent** | CV › Patents | 특허명, 전체발명자명, 출원(등록)번호, 일자, 국내/국제, 출원/등록 |
| **Peer review** | CV › Professional Service | 저널명, ORCID(verified) |
| **TA** | CV › Teaching | 학기, 학수번호, 교과목명 |
| **Press & Broadcast** | 소식(News) + CV › Press | 대표설명, 보도및게재처(영문), URL, 보도게재일자 |

> 새 논문/수상/특허는 **엑셀에 한 줄만 추가**하면 끝.

### B. `profile.yml` 에서 관리 — 엑셀에 없는 사이트 전용 정보 (가끔 한 번)
- **자기소개(bio)** · **연구 관심사** · **한 줄 소개(subtitle)**
- **Skills** (프로그래밍 언어, 프레임워크, 시뮬레이션 툴)
- **소셜 링크**: 이메일, GitHub, **Google Scholar ID**, **ORCID**, LinkedIn, ResearchGate
  → 채워주면 좋습니다 (지금 Scholar/ORCID/LinkedIn 은 비어 있음)
- **Selected publications**: about 상단에 강조할 논문 DOI

### C. 파일로 주면 되는 것
- **프로필 사진**: OneDrive `CV 관리/증명사진.jpg` 를 자동으로 가져옵니다. (바꾸려면 그 파일 교체)
- **PDF CV**: `CV 관리/CVs/` 의 최신 `Jehyeon_Shin_CV_*.pdf` 를 자동으로 가져와 CV 페이지 다운로드 버튼에 연결.

---

## 최초 1회 GitHub 설정 (배포 활성화)
1. 레포 **Settings → Actions → General → Workflow permissions** → **Read and write permissions** 선택 → Save.
2. `main` 브랜치에 한 번 push (또는 `./update.sh`). → Actions 가 빌드 후 `gh-pages` 브랜치 생성.
3. **Settings → Pages → Source**: *Deploy from a branch* → **`gh-pages` / (root)** → Save.
4. 1~2분 뒤 https://sjh97.github.io 접속.

## 의존성
- `rclone` (OneDrive 리모트 `onedrive:` 가 이미 설정돼 있어야 함)
- `uv` (Python 의존성 자동 관리 — pandas/openpyxl/pyyaml)
