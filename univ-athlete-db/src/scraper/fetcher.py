import requests
from scraper.parser import *
#from parser import *
from urllib.parse import urljoin, urlparse
import pandas as pd
import argparse
import numpy as np
import os
from bs4 import BeautifulSoup
import random
import time

"""
• fetcher  
  – HTTP リクエスト／レスポンス取得（fetch_html, fetch_url_univ など）  
  – URL の組み立て（get_base_url, urljoin など）  
  – I/O（ファイル保存／読み込み、ログ出力など）  

ポイントは「fetcher は“どこから”取ってくるか」「parser は“どう読み解く”か」に専念させることです。これによりテストや保守がしやすくなります。
"""


# ユーザーエージェントのリストを定義
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
]

def check_url_exists(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        # 200: OK, 403: Forbidden, 405: Method Not Allowed も存在とみなす
        if response.status_code in [200, 403, 405]:
            # Content-Typeがtext/htmlならTrue
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                return True
        # 一部サーバーはHEADを許可しないのでGETも試す
        if response.status_code == 404:
            return False
        response = requests.get(url, allow_redirects=True, timeout=5)
        if response.status_code in [200, 403]:
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                return True
        return False
    except requests.RequestException:
        return False

def find_competition_link(output_file="competition_urls.txt"):

    year_list = ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30']
    number_list = [str(i) for i in range(1, 31)]
    middle_list = ['jaic/icaak']
    comp_list = [
        "OSIC",  # 大阪インカレ
        "HYIC",  # 兵庫インカレ        
        "OSICHYIC",  # 大阪兵庫インカレ
        "HYIC%20OSIC",  # 大阪兵庫インカレ
        "KYIC",  # 京都インカレ
        "KSIC",  # 関西インカレ
        "NIDAISEN",  # 二大戦
        "GK1",  # 学連記録会1
        "GK2",  # 学連記録会2
        "KYOKA",  # 長距離強化記録会
        "SHUMOKU",  # 種目別選手権
        'ISE',  # 全日本駅伝予選会
        'NEW',  # 関西新人
        'KANJO',  # 関西女子駅伝
        'TANGO',  # 丹後駅伝
    ]
    url_list = []
    osaka="https://www.oaaa.jp/results/r_24/osk_champ/tt.html"
    osaka_2="https://gold.jaic.org/osaka/2023/osk_champ/tt.html"
    osaka_3="https://www.oaaa.jp/results/r_22/osk_champ/tt.html"
    middle_osaka=["www.oaaa.jp/results","gold.jaic.org/osaka"]

    hyougo_1="http://www.haaa.jp/2024/hyo/web/tt.html"
    hyougo_2="http://www.haaa.jp/2022/hyo/web/tt.html"
    
    zennnihonn_innkare="https://iuau.jp/ev2024/93ic/res/tt.html"

    # 既存のURLをセットとして読み込む
    existing_urls = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                existing_urls.add(line.strip())
    print(existing_urls)
    for year in year_list:
        for number in number_list:
            for middle in middle_list:
                for comp in comp_list:
                    url = f'https://gold.jaic.org/{middle}/record/20{year}/{number}_{comp}/tt.html'
                    if url in existing_urls:
                        continue  # 既に存在する場合はスキップ
                    if check_url_exists(url):
                        
                        print(f"Competition found: {url}")
                        url_list.append(url)
                        existing_urls.add(url)  # 追加したURLもセットに入れる
    for year in year_list:
        for middle in middle_osaka:
            urls = [
                f'https://{middle}/r_{year}/osk_champ/tt.html',#大阪選手権
                f'https://{middle}/20{year}/osk_champ/tt.html',# 大阪選手権
                f"http://www.haaa.jp/20{year}/hyo/web/tt.html",#  # 兵庫選手権
                f"https://iuau.jp/ev20{year}/{int(year)+69}ic/res/tt.html" # 全日本インカレ
                ]
            for url in urls:
                if url in existing_urls:
                    continue
                if check_url_exists(url):
                    
                    print(f"Competition found: {url}")
                    url_list.append(url)
                    existing_urls.add(url)  # 追加したURLもセットに入れる

    # ファイルに追記（重複なし）
    if url_list:
        with open(output_file, "a", encoding="utf-8") as f:
            for url in url_list:
                f.write(url + "\n")

def get_base_url(url):
    """指定されたURLからベースURLを取得"""
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path.rsplit('/', 1)[0]}/"
    return base_url

def fetch_html(url, retries=10):
    """
    ウェブページのHTMLを取得する関数（改良版）
    
    Args:
        url: 取得するURL
        retries: リトライ回数
    
    Returns:
        HTMLコンテンツ（文字列）またはNone（取得失敗時）
    """
    for attempt in range(retries):
        try:
            # ランダムなユーザーエージェントを選択
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Pragma': 'no-cache'
            }
            
            print(f"[INFO] Requesting {url} (Attempt {attempt+1}/{retries})")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # 文字化け防止: BeautifulSoup にバイト列を渡して<meta>等からエンコーディング自動判別
                try:
                    # 明示的なエンコーディング指定なしでBeautifulSoupにバイト列を渡す
                    soup = BeautifulSoup(response.content, "html.parser", from_encoding=None)
                    return soup.prettify()
                except Exception as e:
                    print(f"[WARN] BeautifulSoup parsing failed: {e}")
                    
                    # フォールバック: requests の推定エンコーディングを使用
                    try:
                        response.encoding = response.apparent_encoding
                        return response.text
                    except Exception as e:
                        print(f"[WARN] Fallback decoding failed for {url}: {e}")
                        return ""
            elif response.status_code == 403:
                print(f"[WARN] 403 Forbidden, retrying {url} with alternate UA")
                # 次のリトライまでの待機時間を徐々に増やす
                time.sleep(2 + attempt * 2)
            else:
                print(f"[ERROR] HTTP status code {response.status_code} for {url}")
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Exception when fetching {url}: {e}")
            time.sleep(1)
    
    print(f"[ERROR] Failed to fetch {url} after {retries} attempts")
    return ""


# def fetch_html(url: str, timeout: float = 10.0) -> str | None:
#     """
#     URL から HTML を取得し、以下の特徴を持ちます:
#     - Forbidden(403) が返ってきたら User-Agent を変えて再試行
#     - 適切に文字コードを扱い文字化けを防止
#     - エラー時は空文字を返す
#     """
#     # 初回リクエスト用ヘッダー
#     # headers = {
#     #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
#     #     "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
#     #     "Referer": url.rsplit('/', 1)[0] + '/'
#     # }
#     headers = random.choice(USER_AGENTS)
#     try:
#         resp = requests.get(url, headers=headers, timeout=timeout)
#         resp.raise_for_status()
#     except requests.HTTPError as e:
#         # 403 Forbidden の場合だけ再試行
#         if resp.status_code == 403:
#             print(f"[WARN] 403 Forbidden, retrying {url} with alternate UA")
#             headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
#             try:
#                 resp = requests.get(url, headers=headers, timeout=timeout)
#                 resp.raise_for_status()
#             except Exception:
#                 print(f"[ERROR] Still forbidden: {url}")
#                 return ""
#         else:
#             print(f"[WARN] HTTP error for {url}: {e}")
#             return ""
#     except requests.RequestException as e:
#         print(f"[WARN] fetch_html failed for {url}: {e}")
#         return ""

#     # 文字化け防止: BeautifulSoup にバイト列を渡して<meta>等からエンコーディング自動判別
#     try:
#         # 明示的なエンコーディング指定なしでBeautifulSoupにバイト列を渡す
#         soup = BeautifulSoup(resp.content, "html.parser", from_encoding=None)
#         return soup.prettify()
#     except Exception as e:
#         print(f"[WARN] BeautifulSoup parsing failed: {e}")
        
#         # フォールバック: requests の推定エンコーディングを使用
#         try:
#             resp.encoding = resp.apparent_encoding
#             return resp.text
#         except Exception as e:
#             print(f"[WARN] Fallback decoding failed for {url}: {e}")
#             return ""

def fetch_url_univ(url,univ):
    # get_base_url関数を使用して、指定されたURLからベースURLを取得
    base_url= get_base_url(url)
    
    #  Get Url and HTML "競技者一覧画面""
    url_kyougisya_itirann = urljoin(base_url, 'master.html')
    html_kyougisya_itirann = fetch_html(url_kyougisya_itirann)
    
    #Get url and HTML "大学名の索引ページ"
    url_univ_kyougisya,univ_count = find_university_link_and_count(html_kyougisya_itirann, univ)
    url_univ_kyougisya = urljoin(base_url, url_univ_kyougisya)
    html_univ_kyougisya = fetch_html(url_univ_kyougisya)

    #Get results from "大学名の索引ページ"
    result=parse_results_from_univ(html_univ_kyougisya, univ)
    
    #--------------------------------
    df= pd.DataFrame(result)
    #print(df.head(20))
    # 非リレー種目のみの href をフル URL 化してリスト化
    player_url = df['出場種目'] \
        .apply(lambda evs: [
            urljoin(base_url, e['href'])
            for e in evs
            if e.get('href') and e.get('type') =='Other'
        ])
    #print(player_url.head(20))
    # 平坦化して順次 parse_event_detail_for_player を実行、結果を配列に格納
    details = []
    for idx, urls in enumerate(player_url):
        player_name = df.at[idx, '氏名']
        for u in urls:
            html_ev = fetch_html(u)
            print(player_name, u)
            detail = parse_event_detail_track(html_ev, player_name=player_name)
            print(detail)
            details.append(detail)

    # 結果一覧を表示 or DataFrame にする
    #print(details)
    df_details = pd.DataFrame(details)
    print(df_details.head(20))

if __name__ == "__main__":
    # Fetch and process data
    file="/workspaces/Handai_TF_system/univ-athlete-db/database/com_url.txt"
    find_competition_link(file)
