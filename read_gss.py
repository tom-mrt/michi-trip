import os
import re
import unicodedata
from unidecode import unidecode
import requests
import gspread
import deepl
from dotenv import load_dotenv

# .env ファイルを読み込む
load_dotenv()

# === 設定 ===
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY") # 任意で .env に追加可能
NUM_STATIONS = 10  # MVP 用に最初の10駅だけ生成
OUTPUT_DIR = "content/stations"
PREFECTURE = 0
STATION_NAME = 1
ADDRESS = 4
URL = 5
DESCRIPTION = 6


# === スラグ変換関数 ===
def slugify(text, fallback_prefix=None, idx=None):
    """
    text: 元の駅名
    fallback_prefix: フォールバック時に使う接頭辞（例: 都道府県名の英字）
    idx: フォールバック時の識別子（例: 行番号）
    """
    text = unicodedata.normalize('NFKC', text)
    
    # ローマ字化
    slug = unidecode(text)
    
    slug = re.sub(r'[^\w\s-]', '', slug)
    
    # スペース/アンダースコアをハイフンに
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # 連続するハイフンを1つにまとめる
    slug = re.sub(r'-+', '-', slug)
    
    slug = slug.strip("-").lower()
    
    # 空文字ならフォールバック
    if not slug:
        if fallback_prefix and idx is not None:
            slug = f"{fallback_prefix}-{idx}"
        else:
            slug = "station-" + str(idx or 0)
    
    return slug

# === DeepL API 英訳関数 ===
def translate_text(text, target_lang="EN-US"):
    translator = deepl.Translator(DEEPL_API_KEY)
    result = translator.translate_text(text, target_lang=target_lang)
    
    return result.text

# === Google Sheets 読み込み ===
def load_sheet_data():
    gc = gspread.oauth()

    sheet = gc.open_by_key("1n5c8WqgjAN0U8Q90MUpu9WFCY4pv76F3f3_wlRRzb2k").sheet1

    rows = sheet.get_all_values()
    return rows

# === Markdown ファイルの書き出し ===
def write_markdown(row):
    title = row[STATION_NAME]
    slug = slugify(title)
    prefecture = row[PREFECTURE]
    address = row[ADDRESS]
    klook_url = row[URL]
    description_ja = row[DESCRIPTION]
    description_en = translate_text(description_ja)

    content = f"""---
title: "{title}"
prefecture: {prefecture}
address: {address}
affiliate:
  klook: "{klook_url}"
---

**Why visit?** {description_en}
"""

    path = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "index.md"), "w", encoding="utf-8") as f:
        f.write(content)

# === メイン処理 ===
def main():
    rows = load_sheet_data()
    for row in rows[:NUM_STATIONS]:
        print(f"生成中: {row[STATION_NAME]}")
        write_markdown(row)
    print("✅ 全 Markdown ファイル生成完了！")

if __name__ == "__main__":
    main()
