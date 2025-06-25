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

# データベースディレクトリが存在しない場合は作成
if [ ! -d "$DB_DIR" ]; then
    echo "Creating database directory: ${DB_DIR}"
    mkdir -p "$DB_DIR"
fi

# Dockerコンテナを実行
docker run --rm -it \
    --name ${CONTAINER_NAME} \
    -v ${SRC_DIR}:${CONTAINER_SRC_DIR} \
    -v ${DB_DIR}:${CONTAINER_DB_DIR} \
    ${IMAGE_NAME}:${TAG} "$@"