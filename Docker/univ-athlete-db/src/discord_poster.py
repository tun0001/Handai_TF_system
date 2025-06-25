import argparse
import os
import asyncio
import discord

'''
使い方例（コマンドライン）:
    python discord_poster.py \
      --channel_id 123456789012345678 \
      --thread_name "試合速報スレッド" \
      --content "選手Aが○○mをマークしました！"
'''

# ─── argparse で引数を受け取る ─────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="指定チャンネルにスレッドを作成（なければ作成）、既存なら流用してメッセージを送信するスクリプト"
    )
    parser.add_argument(
        "--channel_id",
        type=int,
        required=True,
        help="投稿先のチャンネルID（整数）"
    )
    parser.add_argument(
        "--thread_name",
        type=str,
        required=True,
        help="作成 or 再利用したいスレッドの名前"
    )
    parser.add_argument(
        "--content",
        type=str,
        required=True,
        help="スレッド内に送信するメッセージ本文"
    )
    return parser.parse_args()


# ─── メインロジック: スレッド作成（または既存流用）+ メッセージ送信 ─────────────────────────
async def send_to_thread(token: str, channel_id: int, thread_name: str, content: str):
    # message_content Intent を有効化
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True          # スレッド取得にはギルド Intent も必要
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        # ログインが完了したら実行される
        print(f"✅ Logged in as {client.user} (id: {client.user.id})")

        #2) 投稿先チャンネルオブジェクトを取得
        channel = client.get_channel(channel_id)
        print(f"▶️ チャンネルID {channel_id} を取得中...")
        if channel is None:
            print(f"❌ 指定したチャンネルID {channel_id} が見つかりません。")
            await client.close()
            return
        

        # まずチャンネル履歴にアクセスできるかを確認
        print("▶️ チャンネル履歴取得テスト開始...")
        try:
            recent = [msg async for msg in channel.history(limit=5)]
            print(f"▶️ 取得メッセージ数: {len(recent)}")
            for msg in recent:
                print(f"  • {msg.author.display_name}: {msg.content}")
        except Exception as e:
            print(f"❌ 履歴取得エラー: {e}")
            await client.close()
            return

        # キャッシュ済みのスレッド一覧を見るだけなら await は不要
        active_threads = channel.threads   # TextChannel.threads プロパティ
        print(f"▶️ キャッシュ済みスレッド数: {len(active_threads)}")
        for t in active_threads:
            print(f"  • [ID:{t.id}] {t.name}")

        # HTTP でアクティブスレッドを取りに行きたい場合は
        # fetch_active_threads() を使うと確実です（要権限）。
        #   resp = await channel.fetch_active_threads()
        #   active_threads = resp.threads
        #   print(f"▶️ API取得アクティブスレッド数: {len(active_threads)}")

        target_thread = None
        for t in active_threads:
            print(t.name)
            if t.name == thread_name:
                target_thread = t
                break

        print(" 4) スレッドがなければ、親メッセージを使って新規スレッドを作成する")
        if target_thread is None:
            # 親メッセージは「チャンネルに新しく送信したメッセージ」を使う
            parent_msg = await channel.send(f" **【{thread_name}**速報スレッド】")
            # auto_archive_duration: 60, 1440, 4320, 10080 のいずれか（分単位）
            target_thread = await parent_msg.create_thread(
                name=thread_name,
                auto_archive_duration=1440  # 例：24時間で自動アーカイブ
            )
            print(f"🆕 新規スレッド作成: {thread_name}")
        else:
            print(f"🔁 既存スレッドを使用: {thread_name}")

        # 5) 取得または作成したスレッド内にメッセージを送信
        await target_thread.send(content)
        print(f"✉️ スレッド「{thread_name}」にメッセージ送信完了")

        # 6) 投稿し終わったら Bot をログアウトしてスクリプトを終了
        await client.close()

    # Botを起動（イベントループを開始）
    try:
        await client.start(token)
    except Exception as e:
        print(f"❌ Botの起動中にエラー: {e}")


# ─── エントリポイント: asyncio.run で実行 ─────────────────────────────────────
def main():
    # 1) 引数を取得
    #args = parse_args()

    # 2) 環境変数または固定値で Bot トークンを取得
    #    → 実運用では Secrets や環境変数から読み込むことを強く推奨
    
    #channel_id = os.environ["CHANNEL_TEST_ID"]  # 対象チャンネルのID（右クリック→IDコピーで取得）
    #token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id=1380200984256450751
    token = "MTM4MDM5MTAyMDIzMDg3MzIyOQ.G8AWcn.3r4zWwN8ygdvQue3DFsNVZ3TV447MRclYs3C30"
    thread_name = "全日本インカレ"  # 作成 or 再利用するスレッド名
    content = "選手Aが○○mをマークしました！"  # スレッド内に送信するメッセージ本文
    if token is None:
        print("❌ 環境変数 DISCORD_BOT_TOKEN が設定されていません。")
        return

    # 3) 非同期関数を実行
    asyncio.run(send_to_thread(
        token=token,
        channel_id=channel_id,
        thread_name=thread_name,
        content=content
    ))


if __name__ == "__main__":
    main()