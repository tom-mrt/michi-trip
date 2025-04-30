import os
import re
import unicodedata
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
def slugify(text):
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_]+', '-', text).lower()

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
