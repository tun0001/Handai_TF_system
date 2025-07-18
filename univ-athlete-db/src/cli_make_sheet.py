import os
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# スコープ設定
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive' # 共有設定のためにDriveのスコープも必要
]

# 認証情報を取得
creds_env = os.getenv("GOOGLE_ACCOUNT_KEY")

if not creds_env:
    print("❌ 環境変数 GOOGLE_ACCOUNT_KEY が設定されていません。")
    exit(1)

try:
    # JSON文字列をパース
    creds_dict = json.loads(creds_env)
    
    # Credentialsオブジェクトを作成
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    
    # --- Google Sheets APIサービスを構築 ---
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # --- 新しいスプレッドシートのプロパティを定義 ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    new_sheet_name = f"API_Direct_Sheet_{timestamp}"
    
    spreadsheet_body = {
        'properties': {
            'title': new_sheet_name
        }
    }
    
    # --- spreadsheets.create メソッドを直接呼び出す ---
    print(f"🔄 Google Sheets APIを直接呼び出し、'{new_sheet_name}' を作成しています...")
    spreadsheet = sheets_service.spreadsheets().create(
        body=spreadsheet_body,
        fields='spreadsheetId,spreadsheetUrl' # 必要なレスポンスフィールドを指定
    ).execute()
    
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    spreadsheet_url = spreadsheet.get('spreadsheetUrl')
    
    print("✅ スプレッドシートの作成に成功しました。")
    print(f"🆔 シートID: {spreadsheet_id}")
    
    # --- Google Drive APIを使用して権限を付与 ---
    print("🔄 Google Drive APIを呼び出し、共有設定を行っています...")
    drive_service = build('drive', 'v3', credentials=creds)
    permission_body = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': creds.service_account_email
    }
    
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body=permission_body,
        fields='id'
    ).execute()
    
    print("✅ 共有設定が完了しました。")
    print(f"📋 シート名: {new_sheet_name}")
    print(f"🔗 URL: {spreadsheet_url}")

except HttpError as e:
    # googleapiclientの具体的なHTTPエラーをキャッチ
    error_details = json.loads(e.content).get('error', {})
    error_message = error_details.get('message', '詳細不明')
    status_code = error_details.get('code', 'N/A')
    
    print(f"❌ Google APIエラーが発生しました (ステータス: {status_code})")
    print(f"   エラーメッセージ: {error_message}")
    if "quota" in error_message.lower():
        print("   -> ドライブのストレージクォータ超過の可能性があります。")
        print("      サービスアカウントが属するプロジェクトのオーナーのドライブ容量をご確認ください。")
    exit(1)

except json.JSONDecodeError as e:
    print(f"❌ 認証情報のJSONデコードに失敗しました: {e}")
    exit(1)
    
except Exception as e:
    print(f"❌ 不明なエラーが発生しました: {e}")
    exit(1)