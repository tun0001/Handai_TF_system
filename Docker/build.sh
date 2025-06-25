#!/bin/bash
# filepath: /home/t-kobayashi/Handai_TF_system/Docker/build.sh

# イメージ名とタグを設定
IMAGE_NAME="handai-tf-system"
TAG="latest"

echo "Building Docker image: ${IMAGE_NAME}:${TAG}..."

# 必要なファイルをDockerディレクトリにコピー
cp -r ../univ-athlete-db .
# cp -r ../univ-athlete-db/src .
# cp -r ../univ-athlete-db/database .


# Dockerイメージをビルド
docker build -t ${IMAGE_NAME}:${TAG} .

# コピーしたファイルを削除（オプション）
rm -rf requirements.txt src database

if [ $? -eq 0 ]; then
    echo "Successfully built Docker image: ${IMAGE_NAME}:${TAG}"
else
    echo "Failed to build Docker image."
    exit 1
fi