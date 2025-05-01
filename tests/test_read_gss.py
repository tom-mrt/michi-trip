import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
import read_gss # テスト対象のモジュールをインポート

# === テストデータ ===
MOCK_SHEET_DATA = [
    ["北海道", "道の駅 あさひかわ", "", "", "北海道旭川市", "https://example.com/asahikawa", "旭川の観光拠点"],
    ["青森県", "道の駅 ろくのへ", "", "", "青森県六戸町", "https://example.com/rokunohe", "六戸の魅力満載"],
    ["", "Invalid Station", "", "", "", "", ""], # 空の都道府県
    ["岩手県", "道の駅　平泉", "", "", "岩手県平泉町", "https://example.com/hiraizumi", "世界遺産の近く"], # 全角スペース
    ["宮城県", "道の駅　上品の郷", "", "", "宮城県石巻市", "https://example.com/joubon", "温泉もある道の駅"], # 複雑な名前
    ["秋田県", "", "", "", "秋田県", "https://example.com/akita", "Empty Name"], # 空の駅名
    ["山形県", "道の駅 🍒 チェリーランド", "", "", "山形県寒河江市", "https://example.com/cherry", "さくらんぼ！"], # 絵文字
    ["福島県", "道の駅 ふくしま東和", "", "", "福島県二本松市", "https://example.com/fukushima", "和紙の里"],
    ["茨城県", "道の駅 ひたちおおた", "", "", "茨城県常陸太田市", "https://example.com/hitachiota", "黄門様のふるさと"],
    ["栃木県", "道の駅 もてぎ", "", "", "栃木県茂木町", "https://example.com/motegi", "SLが見れる"],
    ["群馬県", "道の駅 川場田園プラザ", "", "", "群馬県川場村", "https://example.com/kawaba", "人気の田園プラザ"], # 11番目以降のデータ
]

# === slugify 関数のテスト ===
@pytest.mark.parametrize("text, expected_slug", [
    ("道の駅 あさひかわ", "dao-noyi-asahikawa"),
    ("道の駅　平泉", "dao-noyi-ping-quan"),
    ("道の駅 🍒 チェリーランド", "dao-noyi-chieri-rando"),
    ("Invalid Station Name!", "invalid-station-name"),
    ("ＡＢＣ １２３", "abc-123"),
    ("   leading and trailing spaces  ", "leading-and-trailing-spaces"),
    ("multiple--hyphens", "multiple-hyphens"),
    ("underscore_test", "underscore-test"),
])
def test_slugify_normal(text, expected_slug):
    assert read_gss.slugify(text) == expected_slug

@pytest.mark.parametrize("text, fallback_prefix, idx, expected_slug", [
    ("", "hokkaido", 1, "hokkaido-1"),
    ("   ", "aomori", 2, "aomori-2"),
    ("!@#$", "iwate", 3, "iwate-3"), # 変換後空になる
    ("", None, 4, "station-4"), # fallback_prefix なし
    ("日本語", None, None, "ri-ben-yu"), # idx なし (fallback しない)
    ("", "fallback", None, "station-0"), # idx なし (fallback する)
])
def test_slugify_fallback(text, fallback_prefix, idx, expected_slug):
    assert read_gss.slugify(text, fallback_prefix, idx) == expected_slug

# === translate_text 関数のテスト ===
@patch('read_gss.deepl.Translator')
def test_translate_text(mock_translator):
    # deepl.Translator のインスタンスと translate_text メソッドをモック
    mock_instance = mock_translator.return_value
    mock_instance.translate_text.return_value = MagicMock(text="Translated Text")

    result = read_gss.translate_text("元のテキスト")

    # deepl.Translator が正しい API キーで初期化されたか確認
    mock_translator.assert_called_once_with(read_gss.DEEPL_API_KEY)
    # translate_text が正しい引数で呼び出されたか確認
    mock_instance.translate_text.assert_called_once_with("元のテキスト", target_lang="EN-US")
    # 結果が正しいか確認
    assert result == "Translated Text"

# === load_sheet_data 関数のテスト ===
@patch('read_gss.gspread.oauth')
def test_load_sheet_data(mock_oauth):
    # gspread の認証とシート取得処理をモック
    mock_gc = MagicMock()
    mock_sheet = MagicMock()
    mock_worksheet = MagicMock()

    mock_oauth.return_value = mock_gc
    mock_gc.open_by_key.return_value = mock_sheet
    mock_sheet.sheet1 = mock_worksheet
    mock_worksheet.get_all_values.return_value = MOCK_SHEET_DATA

    result = read_gss.load_sheet_data()

    # 各メソッドが期待通りに呼ばれたか確認
    mock_oauth.assert_called_once()
    mock_gc.open_by_key.assert_called_once_with("1n5c8WqgjAN0U8Q90MUpu9WFCY4pv76F3f3_wlRRzb2k")
    mock_worksheet.get_all_values.assert_called_once()
    # 結果が正しいか確認
    assert result == MOCK_SHEET_DATA

# === write_markdown 関数のテスト ===
@patch('read_gss.os.makedirs')
@patch('read_gss.open', new_callable=mock_open)
@patch('read_gss.translate_text')
@patch('read_gss.slugify')
def test_write_markdown(mock_slugify, mock_translate, mock_open_func, mock_makedirs, tmp_path):
    # モックの設定
    mock_slugify.return_value = "test-slug"
    mock_translate.return_value = "English Description"

    # テストデータ
    test_row = ["北海道", "テスト駅", "", "", "北海道テスト市", "https://example.com/test", "日本語の説明"]

    # 一時ディレクトリを使用するように OUTPUT_DIR を変更
    original_output_dir = read_gss.OUTPUT_DIR
    read_gss.OUTPUT_DIR = str(tmp_path) # pytestのtmp_pathフィクスチャを利用
    expected_dir_path = os.path.join(str(tmp_path), "test-slug")
    expected_file_path = os.path.join(expected_dir_path, "index.md")

    try:
        read_gss.write_markdown(test_row)

        # slugify と translate_text が呼ばれたか確認
        mock_slugify.assert_called_once_with("テスト駅")
        mock_translate.assert_called_once_with("日本語の説明")

        # os.makedirs が正しいパスで呼ばれたか確認
        mock_makedirs.assert_called_once_with(expected_dir_path, exist_ok=True)

        # open が正しいパスとモードで呼ばれたか確認
        mock_open_func.assert_called_once_with(expected_file_path, "w", encoding="utf-8")

        # 書き込まれる内容を検証
        handle = mock_open_func() # mock_open のファイルハンドルを取得
        expected_content = f"""---
title: "テスト駅"
prefecture: 北海道
address: 北海道テスト市
affiliate:
  klook: "https://example.com/test"
---

**Why visit?** English Description
"""
        handle.write.assert_called_once_with(expected_content)

    finally:
        # OUTPUT_DIR を元に戻す
        read_gss.OUTPUT_DIR = original_output_dir


# === main 関数のテスト ===
@patch('read_gss.load_sheet_data')
@patch('read_gss.write_markdown')
@patch('builtins.print') # print関数をモック
def test_main(mock_print, mock_write_markdown, mock_load_sheet_data):
    # load_sheet_data の戻り値を設定 (NUM_STATIONS 分だけ返すようにスライス)
    mock_load_sheet_data.return_value = MOCK_SHEET_DATA

    # NUM_STATIONS を一時的にテスト用に設定 (元の値を保持)
    original_num_stations = read_gss.NUM_STATIONS
    read_gss.NUM_STATIONS = 5 # テスト用に5件に設定
    expected_call_count = 5

    try:
        read_gss.main()

        # load_sheet_data が呼ばれたか確認
        mock_load_sheet_data.assert_called_once()

        # write_markdown が NUM_STATIONS 回呼ばれたか確認
        assert mock_write_markdown.call_count == expected_call_count
        # write_markdown が正しい引数で呼ばれたか確認 (最初の呼び出しのみ)
        mock_write_markdown.assert_called_with(MOCK_SHEET_DATA[expected_call_count-1]) # 最後の呼び出しをチェック

        # print が期待通り呼ばれたか確認
        assert mock_print.call_count == expected_call_count + 1 # 各行の生成メッセージ + 完了メッセージ
        mock_print.assert_any_call(f"生成中: {MOCK_SHEET_DATA[0][read_gss.STATION_NAME]}")
        mock_print.assert_any_call("✅ 全 Markdown ファイル生成完了！")

    finally:
        # NUM_STATIONS を元に戻す
        read_gss.NUM_STATIONS = original_num_stations
