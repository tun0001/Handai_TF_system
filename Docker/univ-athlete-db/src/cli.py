import argparse
from scraper.fetcher import fetch_html, fetch_url_univ
#from database.db import save_results
#from scraper.parser import find_university_link_and_count,parse_results_from_univ,parse_event_detail_for_player
from urllib.parse import urljoin, urlparse
import pandas as pd
"""
以下は一般的なプロジェクト構成における　cli.py　と　config.py　の役割です。

cli.py

コマンドラインインターフェイス（CLI）のエントリポイント
argparse 等で引数を受け取り、fetcher や parser の関数を呼び出す
ユーザーからの「どこから何を実行するか」を受け付ける責務
config.py

各種設定値（設定可能なデフォルト値や定数）をまとめるモジュール
• API のベース URL
• デフォルトの大学名や出力パス
• データベース接続情報、タイムアウト／リトライ設定 など
コード中に「ハードコーディング」せず、設定を一元管理して可読性・保守性を向上

"""
def main():
    parser = argparse.ArgumentParser(description='Fetch and store university athlete results.')
    parser.add_argument('url',default="https://gold.jaic.org/jaic/icaak/record/2025/4_KSIC/kyougi.html", help='URL of the results page')
    parser.add_argument('univ',default="大阪大" ,help='University name (partial match allowed)')
    args = parser.parse_args()

    url=args.url
    univ= args.univ

    # URLと大学名を指定して、競技者一覧を取得
    fetch_url_univ(url, univ)
    # # get_base_url関数を使用して、指定されたURLからベースURLを取得
    # base_url= get_base_url(url)
    # #print(f'Base URL: {base_url}')
    # #  Get Url"競技者一覧画面""
    # url_kyougisya_itirann = urljoin(base_url, 'master.html')
    # html_kyougisya_itirann = fetch_html(url_kyougisya_itirann)
    # #Get url "大学名の競技者一覧"
    # url_univ_kyougisya,univ_count = find_university_link_and_count(html_kyougisya_itirann, univ)
    # #print(f"リンク: {url_univ_kyougisya}")
    # #print(f"人数: {univ_count}")
    # url_univ_kyougisya= urljoin(base_url, url_univ_kyougisya)
    # #Get Url "大学名の索引ページ"のHTMLを取得
    # #print(url_univ_kyougisya)
    # html_univ_kyougisya = fetch_html(url_univ_kyougisya)

    # result=parse_results_from_univ(html_univ_kyougisya, univ)
    # #print(result[:25])  # 最初の3件を表示
    # df= pd.DataFrame(result)
    # #print(df.head(20))
    # # 非リレー種目のみの href をフル URL 化してリスト化
    # player_url = df['出場種目'] \
    #     .apply(lambda evs: [
    #         urljoin(base_url, e['href'])
    #         for e in evs
    #         if e.get('href') and e.get('type') =='Other'
    #     ])
    # #print(player_url.head(20))
    # # 平坦化して順次 parse_event_detail_for_player を実行、結果を配列に格納
    # details = []
    # for idx, urls in enumerate(player_url):
    #     player_name = df.at[idx, '氏名']
    #     for u in urls:
    #         html_ev = fetch_html(u)
    #         print(player_name, u)
    #         detail = parse_event_detail_for_player(html_ev, player_name=player_name)
    #         print(detail)
    #         details.append(detail)

    # # 結果一覧を表示 or DataFrame にする
    # #print(details)
    # df_details = pd.DataFrame(details)
    # print(df_details.head(20))

if __name__ == '__main__':
    main()