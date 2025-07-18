from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os,json

# --- 設定項目 ---
# サービスアカウントの認証情報（ADCを使用するため、通常は不要）
# ローカルでテストする場合など、特定のサービスアカウントキーを使用したい場合は設定
# SERVICE_ACCOUNT_FILE = 'path/to/your-service-account-key.json'

# スプレッドシート作成に使用する認証スコープ
# スプレッドシートの作成とDriveでの共有（パーミッション変更）に必要なスコープ
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets', # スプレッドシートの作成・編集
    'https://www.googleapis.com/auth/drive'         # Drive上でのファイル操作（共有設定など）
]

# 新しく作成するスプレッドシートの名前
NEW_SPREADSHEET_NAME = 'My New Spreadsheet for Service Account'

# アクセス権限を付与したいサービスアカウントのメールアドレス
# Google Cloud Console の「IAM と管理」->「サービスアカウント」で確認できます
# 例: my-service-account@your-project-id.iam.gserviceaccount.com
#SERVICE_ACCOUNT_EMAIL_TO_SHARE = 'edit-tf-schedule@handai-tf-system-control.iam.gserviceaccount.com'
SERVICE_ACCOUNT_EMAIL_TO_SHARE = 'sheet-creater@handai-tf-system-control.iam.gserviceaccount.com'
# -----------------

def create_and_share_spreadsheet():
    """
    新しいGoogleスプレッドシートを作成し、サービスアカウントと共有します。
    """
    try:
        # サービスアカウントとして認証情報を取得 (Application Default Credentialsを使用)
        # Google Cloud上で実行する場合、環境変数やインスタンスメタデータから自動的に取得
        # ローカルで特定のキーファイルを使用する場合は from_service_account_file() を使用
        #creds = service_account.DefaultCredentials(scopes=SCOPES)
        creds_env = os.getenv("GOOGLE_ACOUNT_KEY_SHEET")
        
        if not creds_env:
            print("エラー: 環境変数 'GOOGLE_ACCOUNT_KEY' が設定されていません。")
            return

        creds_dict = json.loads(creds_env)
        
        # --- ここからデバッグコードを追加 ---
        # 実際に使用しているサービスアカウントのメールアドレスを表示
        client_email = creds_dict.get('client_email')
        print(f"--- 認証情報デバッグ ---")
        print(f"使用中のサービスアカウント: {client_email}")
        print(f"----------------------")
        # --- ここまでデバッグコード ---

        # Credentialsオブジェクトを作成
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

        # Sheets API サービスを構築
        sheets_service = build('sheets', 'v4', credentials=creds)
        # Drive API サービスを構築 (共有設定のため)
        drive_service = build('drive', 'v3', credentials=creds)

        # 1. 新しいスプレッドシートを作成
        spreadsheet_body = {
            'properties': {
                'title': NEW_SPREADSHEET_NAME
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(
            body=spreadsheet_body,
            fields='spreadsheetId,spreadsheetUrl' # 作成後にIDとURLを取得
        ).execute()

        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')

        print(f"スプレッドシート '{NEW_SPREADSHEET_NAME}' を作成しました。")
        print(f"ID: {spreadsheet_id}")
        print(f"URL: {spreadsheet_url}")

        # 2. サービスアカウントにアクセス権限を付与
        # 権限設定のボディ
        permission_body = {
            'type': 'user',    # ユーザー（サービスアカウントもユーザータイプ）
            'role': 'writer',  # 編集者として権限を付与
            'emailAddress': SERVICE_ACCOUNT_EMAIL_TO_SHARE # サービスアカウントのメールアドレス
        }

        # Drive API を使ってパーミッションを追加
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission_body,
            fields='id' # 作成されたパーミッションIDを取得
        ).execute()

        print(f"サービスアカウント '{SERVICE_ACCOUNT_EMAIL_TO_SHARE}' に編集権限を付与しました。")
        print("これにより、このサービスアカウントは作成されたスプレッドシートを操作できます。")

    except HttpError as error:
        print(f"APIエラーが発生しました: {error}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == '__main__':
    create_and_share_spreadsheet()