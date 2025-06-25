import dis, marshal, sys
# ヘッダ（マジックナンバ＋タイムスタンプ等）16バイトをスキップ
with open("univ-athlete-db/src/cli/__pycache__/real_time.cpython-312.pyc", "rb") as f:
    f.read(16)
    code_obj = marshal.load(f)
# モジュールレベルのコードを逆アセンブル
dis.dis(code_obj)