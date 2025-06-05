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

# filepath: /univ-athlete-db/univ-athlete-db/src/config.py

DATABASE_URI = 'sqlite:///univ_athlete.db'  # Database connection string
DEBUG = True  # Enable debug mode for development
TIMEOUT = 10  # Timeout for HTTP requests in seconds

# Constants for scraping
BASE_URL = 'https://example.com/results'  # Base URL for scraping results
RESULTS_TABLE_ID = 'results'  # ID of the results table in the HTML

# Other configuration settings can be added here as needed