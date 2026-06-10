#!/usr/bin/env bash
# =============================================================================
#  홈페이지 업데이트 — 이 스크립트 하나만 실행하면 끝.
#
#    OneDrive(information.xlsx, 최신 CV PDF) 동기화
#      → al-folio 콘텐츠 생성 → Git 커밋/푸시 → GitHub Actions 자동 배포
#
#  사용법:
#    cd _pipeline && ./update.sh            # 동기화 + 생성 + 커밋 + 푸시
#    ./update.sh --no-push                  # 푸시 없이 로컬 생성만 (미리보기/검토용)
#    ./update.sh --no-pull                  # OneDrive 동기화 건너뛰고 생성만
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
REMOTE="onedrive:바탕 화면/rholab/CV 관리"
CACHE="$HERE/cache"

DO_PULL=1; DO_PUSH=1
for arg in "$@"; do
  case "$arg" in
    --no-pull) DO_PULL=0 ;;
    --no-push) DO_PUSH=0 ;;
    *) echo "알 수 없는 옵션: $arg"; exit 1 ;;
  esac
done

if [ "$DO_PULL" -eq 1 ]; then
  echo "▶ OneDrive 동기화..."
  mkdir -p "$CACHE"
  rclone copy "$REMOTE/information.xlsx" "$CACHE/"
  # 가장 최근 날짜의 CV PDF → assets/pdf/cv.pdf
  LATEST_PDF="$(rclone lsf "$REMOTE/CVs/" --include '*.pdf' 2>/dev/null | sort | tail -1 || true)"
  if [ -n "$LATEST_PDF" ]; then
    mkdir -p "$REPO/assets/pdf"
    rclone copyto "$REMOTE/CVs/$LATEST_PDF" "$REPO/assets/pdf/cv.pdf"
    echo "  ✔ CV PDF: $LATEST_PDF → assets/pdf/cv.pdf"
  fi
  # 증명사진 → 프로필 사진
  if rclone lsf "$REMOTE/증명사진.jpg" >/dev/null 2>&1; then
    rclone copyto "$REMOTE/증명사진.jpg" "$REPO/assets/img/prof_pic.jpg"
    echo "  ✔ 프로필 사진: 증명사진.jpg → assets/img/prof_pic.jpg"
  fi
fi

echo "▶ 콘텐츠 생성..."
( cd "$HERE" && uv run generate.py )

if [ "$DO_PUSH" -eq 1 ]; then
  echo "▶ Git 커밋 & 푸시..."
  cd "$REPO"
  git add -A
  if git diff --cached --quiet; then
    echo "  변경사항 없음 — 푸시 생략."
  else
    git commit -m "Update site from CV data ($(date +%Y-%m-%d))"
    git push
    echo "  ✔ 푸시 완료 — GitHub Actions 가 1~3분 내 https://sjh97.github.io 에 배포합니다."
  fi
else
  echo "▶ (--no-push) 로컬 생성만 완료. 검토 후 직접 커밋/푸시하세요."
fi
