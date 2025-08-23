#!/bin/bash
set -e  # エラー時に即座に終了

# イメージ名とタグを設定
IMAGE_NAME="handai-tf-system"
TAG="latest"

# カラー出力用の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# クリーンアップ関数
cleanup() {
    if [ -d "univ-athlete-db" ]; then
        log_info "Cleaning up temporary files..."
        rm -rf univ-athlete-db
    fi
}

# シグナルハンドラーでクリーンアップを実行
trap cleanup EXIT INT TERM

log_info "Building Docker image: ${IMAGE_NAME}:${TAG}..."

# 必要なディレクトリの存在確認
if [ ! -d "../univ-athlete-db" ]; then
    log_error "Source directory '../univ-athlete-db' not found!"
    exit 1
fi

# 必要なファイルをDockerディレクトリにコピー
log_info "Copying source files..."
cp -r ../univ-athlete-db .

# Dockerイメージをビルド
log_info "Starting Docker build..."
if docker build -t ${IMAGE_NAME}:${TAG} .; then
    log_info "Successfully built Docker image: ${IMAGE_NAME}:${TAG}"
    
    # イメージサイズを表示
    IMAGE_SIZE=$(docker images ${IMAGE_NAME}:${TAG} --format "table {{.Size}}" | tail -n 1)
    log_info "Image size: ${IMAGE_SIZE}"
    
    # イメージの確認
    docker images ${IMAGE_NAME}:${TAG}
else
    log_error "Failed to build Docker image."
    exit 1
fi