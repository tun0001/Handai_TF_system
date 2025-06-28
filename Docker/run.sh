#!/bin/bash
# filepath: /home/t-kobayashi/Handai_TF_system/Docker/run.sh

# イメージ名とタグを設定
IMAGE_NAME="handai-tf-system"
TAG="latest"

# コンテナ名
CONTAINER_NAME="handai-tf-container"

# ソースディレクトリとデータベースディレクトリのマウント
SRC_DIR="$(pwd)/../univ-athlete-db/src"
DB_DIR="$(pwd)/../univ-athlete-db/database"  # データベースディレクトリ
CONTAINER_SRC_DIR="/univ-athlete-db/src"
CONTAINER_DB_DIR="/univ-athlete-db/database"  # コンテナ内のデータベースディレクトリ

echo "Starting Docker container: ${CONTAINER_NAME}..."
echo "Mounting source directory: ${SRC_DIR} -> ${CONTAINER_SRC_DIR}"
echo "Mounting database directory: ${DB_DIR} -> ${CONTAINER_DB_DIR}"

ENV_FILE="$HOME/.config/handai-tf-system/env.sh"
if [ -f "$ENV_FILE" ]; then
    echo "環境変数ファイルを読み込み中: ${ENV_FILE}"
    source "$ENV_FILE"
else
    echo "環境変数ファイルが見つかりません: ${ENV_FILE}"
    echo "ファイルを作成してください"
    exit 1
fi

# データベースディレクトリが存在しない場合は作成
if [ ! -d "$DB_DIR" ]; then
    echo "Creating database directory: ${DB_DIR}"
    mkdir -p "$DB_DIR"
fi

# Dockerコンテナを実行
docker run --rm -it \
    --dns=8.8.8.8 \
    --name ${CONTAINER_NAME} \
    -v ${SRC_DIR}:${CONTAINER_SRC_DIR} \
    -v ${DB_DIR}:${CONTAINER_DB_DIR} \
    -e DISCORD_BOT_TOKEN="${DISCORD_BOT_TOKEN}" \
    -e GOOGLE_SHEETS_CREDENTIALS="${GOOGLE_SHEETS_CREDENTIALS}" \
    ${IMAGE_NAME}:${TAG} "$@"