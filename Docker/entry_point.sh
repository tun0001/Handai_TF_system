#!/bin/bash
# filepath: /home/t-kobayashi/Handai_TF_system/Docker/entrypoint.sh

# データベースディレクトリが存在することを確認
DB_DIR="/univ-athlete-db/database"
if [ ! -d "$DB_DIR" ]; then
    echo "Creating database directory inside container: ${DB_DIR}"
    mkdir -p "$DB_DIR"
fi

# データベースディレクトリの権限を設定（オプション）
chmod -R 777 "$DB_DIR"

echo "Database directory is available at: ${DB_DIR}"

# カレントディレクトリとPythonパスを確認
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Files in src directory:"
ls -la /univ-athlete-db/src

# cli_spread.pyを実行
echo "Starting cli_spread.py..."
python /univ-athlete-db/src/cli_spread.py "$@"

# 対話的シェルが必要な場合は、以下を使用
# if [ $# -eq 0 ]; then
#     echo "No arguments provided, starting interactive shell"
#     exec bash
# else
#     python ./src/cli_spread.py "$@"
# fi