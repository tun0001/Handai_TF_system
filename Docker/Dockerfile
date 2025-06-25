# FROM python:3.10-slim

# # 必要最小限のシステムパッケージのみインストール
# RUN apt-get update && apt-get install -y \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # 作業ディレクトリを設定
# WORKDIR /app

# # ディレクトリ構造を作成
# RUN mkdir -p /app/univ-athlete-db/database

# # 必要なファイルをコピー
# COPY ./univ-athlete-db/requirements.txt .
# #COPY univ-athlete-db/requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # アプリケーションファイルをコピー
# COPY univ-athlete-db/src ./src
# COPY Docker/entry_point.sh ./entrypoint.sh
# RUN chmod +x ./entrypoint.sh

# # コンテナ実行のための環境変数
# ENV PYTHONPATH=/app

# # エントリーポイント設定
# ENTRYPOINT ["./entrypoint.sh"]
# # Change this line
FROM python:3.10-slim

# 必要最小限のシステムパッケージのみインストール
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# ディレクトリ構造を作成
RUN mkdir -p /app/univ-athlete-db/database

# requirements.txtが存在するか確認するためのデバッグコマンド
RUN echo "Current directory: $(pwd)"

# 必要なファイルをコピー
# 注意: パスはビルドコンテキストからの相対パス
COPY univ-athlete-db/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY univ-athlete-db/src ./univ-athlete-db/src
COPY entry_point.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# コンテナ実行のための環境変数
ENV PYTHONPATH=/app

# エントリーポイント設定
ENTRYPOINT ["./entrypoint.sh"]
