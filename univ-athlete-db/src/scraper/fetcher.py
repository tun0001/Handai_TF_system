import requests
from scraper.parser import *
#from parser import *
from urllib.parse import urljoin, urlparse
import pandas as pd
import argparse
import numpy as np
import os

"""
• fetcher  
  – HTTP リクエスト／レスポンス取得（fetch_html, fetch_url_univ など）  
  – URL の組み立て（get_base_url, urljoin など）  
  – I/O（ファイル保存／読み込み、ログ出力など）  

ポイントは「fetcher は“どこから”取ってくるか」「parser は“どう読み解く”か」に専念させることです。これによりテストや保守がしやすくなります。
"""
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
        "SYUMOKU",  # 種目別選手権
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

def fetch_html(url):
    """Fetch HTML content from the specified URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        # 明示的に Shift_JIS としてデコード
        response.encoding = 'shift_jis'
        return response.text
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"Warning: 404 Not Found for url: {url}")
            return None
        else:
            raise RuntimeError(f"Error fetching data from {url}: {e}")
    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching data from {url}: {e}")

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