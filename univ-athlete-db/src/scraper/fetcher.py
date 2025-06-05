import requests
from scraper.parser import find_university_link_and_count,parse_results_from_univ,parse_event_detail_for_player_track
from urllib.parse import urljoin, urlparse
import pandas as pd
import argparse

"""
• fetcher  
  – HTTP リクエスト／レスポンス取得（fetch_html, fetch_url_univ など）  
  – URL の組み立て（get_base_url, urljoin など）  
  – I/O（ファイル保存／読み込み、ログ出力など）  

ポイントは「fetcher は“どこから”取ってくるか」「parser は“どう読み解く”か」に専念させることです。これによりテストや保守がしやすくなります。
"""
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
        encoding = response.apparent_encoding
        return response.content.decode(encoding, errors='replace')
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
            detail = parse_event_detail_for_player_track(html_ev, player_name=player_name)
            print(detail)
            details.append(detail)

    # 結果一覧を表示 or DataFrame にする
    #print(details)
    df_details = pd.DataFrame(details)
    print(df_details.head(20))