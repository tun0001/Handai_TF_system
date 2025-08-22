#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
競技結果ページから指定大学の結果のみを抽出して出力するスクリプト
Usage:
  python scrape_univ_results.py <url> <大学名> [--json]
"""
import argparse
import requests
from bs4 import BeautifulSoup
import json

def fetch_html(url):
    """指定URLからHTMLを取得して文字列で返す"""
    resp = requests.get(url)
    resp.raise_for_status()
    # 適切な文字エンコーディングを設定してデコード
    encoding = resp.apparent_encoding
    return resp.content.decode(encoding, errors='replace')


def fetch_results(url):
    """指定URLから結果テーブルをパースして辞書のリストを返す"""
    html = fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        raise RuntimeError('結果テーブルが見つかりません')
    # ヘッダーは <th> タグから取得 (colspanを考慮)
    headers = []
    for th in table.find_all('th'):
        col = int(th.get('colspan', 1)) if th.get('colspan') else 1
        text = th.get_text(strip=True)
        if col > 1 and '氏名' in text:
            # 氏名列: 最初を氏名、2番目以降をフリガナ
            headers.append(text)
            headers.append(f"{text}_kana")
            # 追加分をスキップ
            continue
        # 通常の列
        headers.extend([text] * col)
    results = []
    # tdを持つ行のみデータ行とみなす
    for row in table.find_all('tr'):
        cols = row.find_all('td')
        if not cols:
            continue
        texts = [td.get_text(strip=True) for td in cols]
        if len(texts) != len(headers):
            continue
        results.append(dict(zip(headers, texts)))
    return results


def filter_by_univ(results, univ):
    """大学名を含むエントリのみフィルタ"""
    key_candidates = ['大学', '所属', '大学名', 'Affiliation']
    filtered = []
    for r in results:
        text = ' '.join(r.get(k, '') for k in key_candidates)
        if univ in text:
            filtered.append(r)
    return filtered


def main():
    parser = argparse.ArgumentParser(description='競技結果ページから指定大学の結果を抽出')
    parser.add_argument('url', help='結果ページのURL')
    parser.add_argument('univ', help='大学名 （部分一致可）')
    parser.add_argument('--json', action='store_true', help='JSONフォーマットで出力')
    args = parser.parse_args()

    results = fetch_results(args.url)
    print(f'取得した結果数: {len(results)}')
    print(results[:3])  # 最初の3件を表示
    selected = filter_by_univ(results, args.univ)

    # 名前カラムを自動検出
    name_candidates = ['氏名', '選手', 'Name']
    headers = list(results[0].keys()) if results else []
    name_key = next((c for c in name_candidates if c in headers), None)
    if not name_key:
        # フォールバック: ヘッダーに「名」を含むキーを探す
        name_key = next((h for h in headers if '名' in h), None)
    if not name_key:
        raise RuntimeError('名前カラムが見つかりません')
    # 指定大学の選手名リスト
    names = [r[name_key] for r in selected]

    if args.json:
        print(json.dumps(names, ensure_ascii=False, indent=2))
    else:
        for n in names:
            print(n)

if __name__ == '__main__':
    main()
