from google.oauth2 import service_account
from googleapiclient.discovery import build
import os,json
# サービスアカウントキーファイルへのパス（Google Cloud 環境では通常不要）
# ローカルでテストする場合などに使用。本番環境ではADCを推奨。
# SERVICE_ACCOUNT_FILE = 'path/to/your-service-account-key.json'

# Drive APIのスコープ（必要な権限範囲を指定）
SCOPES = ['https://www.googleapis.com/auth/drive.readonly'] # 閲覧権限の例

def list_drive_files():
    # サービスアカウントとして認証
    # Google Cloud 環境（Compute Engine, Cloud Runなど）では自動的に認証情報を取得
    # ローカルの場合は service_account.Credentials.from_service_account_file() を使用
    #creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    # 認証情報を取得
    creds_env = os.getenv("GOOGLE_ACCOUNT_KEY")
    creds_dict = json.loads(creds_env)
    # Credentialsオブジェクトを作成
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    #creds = service_account.DefaultCredentials(scopes=SCOPES)
    
    # Drive APIクライアントの構築
    service = build('drive', 'v3', credentials=creds)

    # ファイルのリストを取得
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

if __name__ == '__main__':
    list_drive_files()
