#!/bin/bash

# コピー元画像
SOURCE="content/stations/三笠みかさ/main.jpg"

# チェック
if [ ! -f "$SOURCE" ]; then
  echo "❌ コピー元画像が見つかりません: $SOURCE"
  exit 1
fi

# 対象ディレクトリ
TARGET_ROOT="content/stations"

echo "🔁 main.jpg を一括コピー中..."

copied=0
skipped=0

for dir in "$TARGET_ROOT"/*/; do
  target_img="${dir}main.jpg"

  if [ -f "$target_img" ]; then
    echo "⏩ スキップ（すでに存在）: $target_img"
    ((skipped++))
  else
    cp "$SOURCE" "$target_img"
    echo "✅ コピー: $target_img"
    ((copied++))
  fi
done

echo
echo "✔️ 完了：$copied 件コピー / $skipped 件スキップ"
