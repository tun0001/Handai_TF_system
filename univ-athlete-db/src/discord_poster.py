import argparse
import os
import asyncio
import discord
import aiohttp

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

# async def send_to_thread(token: str, channel_id: int, thread_name: str, content: str):
#     """
#     discord_2.pyのスレッド探索機能とdiscord.pyの書き込み方式を組み合わせた関数
    
#     Args:
#         token: Discordボットトークン
#         channel_id: チャンネルID
#         thread_name: スレッド名
#         content: 送信するテキスト
#     """
#     BASE_URL = 'https://discord.com/api/v10'
    
#     # discord.pyライブラリの属性チェック
#     try:
#         if not hasattr(discord, 'Intents'):
#             print("❌ discord.Intentsが見つかりません。discord.pyライブラリが正しくインストールされていない可能性があります。")
#             return
#         if not hasattr(discord, 'Client'):
#             print("❌ discord.Clientが見つかりません。discord.pyライブラリが正しくインストールされていない可能性があります。")
#             return
#         print("✅ discord.pyライブラリの属性チェック完了")
#     except Exception as e:
#         print(f"❌ discord.pyライブラリの属性チェックエラー: {e}")
#         return
    
#     # discord.pyライブラリでスレッド探索を行う
#     try:
#         intents = discord.Intents.default()
#         intents.message_content = True
#         intents.guilds = True
#         client = discord.Client(intents=intents)
#         print("✅ Discordクライアントの初期化完了")
#     except Exception as e:
#         print(f"❌ Discordクライアントの初期化エラー: {e}")
#         return
    
#     # スレッドIDを格納する変数（外部スコープで定義）
#     target_thread_id = None
#     exploration_completed = False
    
#     @client.event
#     async def on_ready():
#         nonlocal target_thread_id, exploration_completed
        
#         print(f"✅ Logged in as {client.user} (id: {client.user.id})")
        
#         try:
#             # 投稿先チャンネルオブジェクトを取得
#             channel = client.get_channel(channel_id)
#             if channel is None:
#                 print(f"❌ 指定したチャンネルID {channel_id} が見つかりません。")
#                 return
            
#             print(f"▶️ チャンネル「{channel.name}」でスレッド探索を開始...")
            
#             target_thread = None
#             # スレッド取得部分を修正
#             # if target_thread is None:
#             #     print("▶️ チャンネルからスレッドを取得中...")
#             #     try:
#             #         # 非同期ジェネレータを適切に処理
#             #         thread_list = []
#             #         async for thread in channel.archived_threads(limit=100):
#             #             thread_list.append(thread)
#             #             print(f"  • [ID:{thread.id}] {thread.name}")
#             #             if thread.name == thread_name:
#             #                 target_thread = thread
#             #                 target_thread_id = thread.id
#             #                 print(f"🔍 アーカイブされたスレッドを発見: {thread_name} (ID: {target_thread_id})")
#             #                 break
                        
#             #         print(f"▶️ アーカイブスレッド取得数: {len(thread_list)}")
                        
#             #     except Exception as e:
#             #         print(f"⚠️ スレッド取得エラー: {e}")
#             #         import traceback
#             #         traceback.print_exc()
#                     #キャッシュになければ、APIでアクティブスレッドを取得
#             if target_thread is None:
#                 print("▶️ APIでアクティブスレッドを取得中...")
#                 try:
#                     resp = await channel.fetch_active_threads()
#                     api_threads = resp.threads
#                     print(f"▶️ API取得アクティブスレッド数: {len(api_threads)}")
                    
#                     for t in api_threads:
#                         print(f"  • [ID:{t.id}] {t.name}")
#                         if t.name == thread_name:
#                             target_thread = t
#                             target_thread_id = t.id
#                             print(f"🔍 APIでスレッドを発見: {thread_name} (ID: {target_thread_id})")
#                             break
#                 except Exception as e:
#                     print(f"⚠️ アクティブスレッド取得エラー: {e}")
#              #キャッシュ済みのスレッド一覧から探索
#             active_threads = channel.threads
#             print(f"▶️ キャッシュ済みスレッド数: {len(active_threads)}")
            
            
#             for t in active_threads:
#                 print(f"  • [ID:{t.id}] {t.name}")
#                 if t.name == thread_name:
#                     target_thread = t
#                     target_thread_id = t.id
#                     print(f"🔍 既存スレッドを発見: {thread_name} (ID: {target_thread_id})")
#                     break


#             # スレッドが見つからない場合は新規作成
#             if target_thread is None:
#                 print(f"🆕 スレッド '{thread_name}' が見つからないため、新規作成します...")
#                 try:
#                     # 親メッセージを送信
#                     parent_msg = await channel.send(f"**【{thread_name}】速報スレッド**")
                    
#                     # スレッドを作成
#                     target_thread = await parent_msg.create_thread(
#                         name=thread_name,
#                         auto_archive_duration=1440  # 24時間で自動アーカイブ
#                     )
#                     target_thread_id = target_thread.id
#                     print(f"✅ 新規スレッド作成完了: {thread_name} (ID: {target_thread_id})")
                    
#                 except Exception as e:
#                     print(f"❌ スレッド作成エラー: {e}")
#                     return
            
#             print(f"🎯 対象スレッドID: {target_thread_id}")
            
#         except Exception as e:
#             print(f"❌ スレッド探索中にエラー: {e}")
#         finally:
#             exploration_completed = True
#             await client.close()
    
#     # discord.pyライブラリでスレッド探索を実行
#     print("🔍 discord.pyライブラリでスレッド探索を開始...")
#     try:
#         await client.start(token)
#     except Exception as e:
#         print(f"❌ Bot起動エラー: {e}")
#         return
    
#     # スレッド探索が完了するまで待機
#     while not exploration_completed:
#         await asyncio.sleep(0.1)
    
#     # スレッドIDが取得できなかった場合は終了
#     if target_thread_id is None:
#         print("❌ スレッドIDが取得できませんでした。処理を終了します。")
#         return
    
#     # aiohttp（discord.py方式）でメッセージ送信
#     print("📝 aiohttpでメッセージ送信を開始...")
#     headers = {
#         'Authorization': f'Bot {token}',
#         'Content-Type': 'application/json'
#     }
    
#     try:
#         timeout = aiohttp.ClientTimeout(total=10)
        
#         async with aiohttp.ClientSession(timeout=timeout) as session:
#             # スレッドにメッセージを送信
#             async with session.post(
#                 f'{BASE_URL}/channels/{target_thread_id}/messages',
#                 headers=headers,
#                 json={'content': content}
#             ) as response:
#                 if response.status == 200:
#                     print(f"✅ メッセージ送信完了: スレッド「{thread_name}」(ID: {target_thread_id})")
#                     print(f"📄 送信内容: {content}")
#                 else:
#                     error_text = await response.text()
#                     print(f"❌ メッセージ送信エラー: {response.status}")
#                     print(f"📄 エラー詳細: {error_text}")
                    
#     except aiohttp.ClientError as e:
#         print(f"❌ HTTP接続エラー: {e}")
#     except asyncio.TimeoutError:
#         print("❌ タイムアウトエラー: Discord APIとの接続がタイムアウトしました")
#     except Exception as e:
#         print(f"❌ 予期しないエラー: {e}")

# チャンネル内の全スレッドを削除
async def delete_all_threads(token: str, channel_id: int):
    """チャンネル内の全スレッドを削除する"""
    # discord.pyの初期化
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    client = discord.Client(intents=intents)
    
    threads_deleted = 0
    
    @client.event
    async def on_ready():
        nonlocal threads_deleted
        try:
            # チャンネル取得
            channel = client.get_channel(channel_id)
            if not channel:
                print(f"❌ チャンネルID {channel_id} が見つかりません")
                await client.close()
                return
                
            print(f"▶️ チャンネル「{channel.name}」の全スレッドを削除します...")
            
            # キャッシュ済みスレッド削除
            active_threads = channel.threads
            print(f"▶️ キャッシュ済みスレッド: {len(active_threads)}件")
            
            for thread in active_threads:
                print(f"  • スレッド「{thread.name}」(ID: {thread.id})を削除中...")
                try:
                    await thread.delete()
                    threads_deleted += 1
                    print(f"  ✅ スレッド「{thread.name}」を削除しました")
                except Exception as e:
                    print(f"  ❌ スレッド削除エラー: {e}")
            
            # アーカイブ済みスレッドの取得と削除
            try:
                print("▶️ アーカイブ済みスレッドを取得中...")
                archived_threads = []
                async for thread in channel.archived_threads(limit=100):
                    archived_threads.append(thread)
                
                print(f"▶️ アーカイブ済みスレッド: {len(archived_threads)}件")
                for thread in archived_threads:
                    print(f"  • アーカイブスレッド「{thread.name}」(ID: {thread.id})を削除中...")
                    try:
                        await thread.delete()
                        threads_deleted += 1
                        print(f"  ✅ アーカイブスレッド「{thread.name}」を削除しました")
                    except Exception as e:
                        print(f"  ❌ アーカイブスレッド削除エラー: {e}")
            except Exception as e:
                print(f"❌ アーカイブスレッド取得エラー: {e}")
                
            print(f"✅ 合計 {threads_deleted} 件のスレッドを削除しました")
        
        except Exception as e:
            print(f"❌ スレッド削除中にエラー: {e}")
        finally:
            await client.close()
    
    # Botを起動
    try:
        await client.start(token)
    except Exception as e:
        print(f"❌ Bot起動エラー: {e}")
    
    return threads_deleted

# エントリポイントも修正が必要
async def main_async():
    print("🔄 Discordスレッド投稿スクリプトを開始します...")
    channel_id = int(1380200984256450751)
    token = os.environ["DISCORD_BOT_TOKEN"]
    
    # awaitを使用して非同期関数を呼び出す
    await delete_all_threads(
        token=token,
        channel_id=channel_id
    )

def main():
    # asyncio.run を使用して非同期関数を実行
    asyncio.run(main_async())
#                     threads = ait response.json()
#                     print(f"アクティブなスレッ取得しました: {len(threads.get('threads', []))} 件")
#                     print# (threads)
#                   for thread in threads.get('threa# ds', []):
#                         if thread.get('name') == thr# ead_name:
#                           thread_id = tead.# get('id')
#                             print("既存のスレッドを見つけました: {thread_name} (ID: {thre# ad_id})")
#                           break# 
            
#             # アー# カイれたスレッドも確認
#             if n# ot thread_id:
#                 async with session.get(f'{BA_URL}/channels/{channel_id}/threadarchived/public', heads=headers)#  as response:
#                     if response.s# tatus == 200:
#                       threads = ait re# sponse.json()
#                       for thread in threads.get('t# hreads', []):
#                             if thread.get('name') ==#  thread_name:
#                               thread_id = thr# ead.t('id')
#                                 print(f"アーカイブされたッドを見つけました: {thread_name} (ID: {# thread_id})")
#                               break# 
            
#             # スレッドが# 存在しない場合のみ新規作成           if n# ot thread_id:
#                 print(f"スレッド 'hread_name}' が見つかりませんで# した。新規作成します。")
#                 # 親チャンネ# ルに最初のメッセージを送信
#                 asc with # session.post(
#                     f'{BASE_L}/channels/{channel_i# d}/messag',
#                     hea# de=headers,
#                     json={'content': f'競技結果: {t# hread_nam'}
#                 )#  as response:
#                   if response.s# tatus == 0:
#                         message = await response.json()
#          #              
#                       # メ# ッセージからスレッドを作成
#                         async with # seion.post(
#                           f'{BASE_URL}/channels/{channel_id}/message{message["id# "]}/threads',
#                             hea# ders=headers,
#                           json={'name':#  threaname}
#                         ) as thr# ead_respoe:
#                             if thread_response.s# tatus == 201:
#                                hread_data = await thread_re# sponse.json()
#                               thread_id = thread_d# ata.t('id')
#                                 print(新しいスレッドを作成しました: {thread_name} (ID: {# thread_id})")
#                   #         else:
#                                 print(f"スレッド作成エラー: hread_respo# nse.status}")
#                          #        retur            #         else:
#                         print(f"メッセージ送信エラー: {respo# nse.status)
#                         return#            
#             # 2. # スレッドにメッセージを送信
#             # if thread_id:
#               async with # session.post(
#                   f'{BASE_URLchannels/{thread_i# d}/messages',
#                     hea# ders=aders,
#                     json={'conte# nt'content}
#                 )#  asesponse:
#                   if response.s# tatus != 200:
#                       print(f"スレッドへの投稿エラー: {respo# nse.status}")
#                     else:
#                       print(f"メッセージをスレッドに投稿しました: # {thread_id}")
#             else:
#                 int("スレッドIDが取得でき# ませんでした")
    
#     except aiohp.Clie# ntError as e:
#         print(f"HTT# P接続エラー: {e}")
#     exce asyncio.# TimeoutError:
#       print("タイムアウトエラー: Discord APIとの接続# がタイムアウトしました")
#     except # ception as e:
#       print(f"予期しないエラー: {e}")

# ─── メインロジック: スレッド（または既存流用）+ メッセージ送信 ───────────────────────
# ─── メインロジック: スレッド作成（または既存流用）+ メッセージ送信 ─────────────────────────
# async def send_to_thread(token: str, channel_id: int, thread_name: str, content: str):
#     # message_content Intent を有効化
#     intents = discord.Intents.default()
#     intents.message_content = True
#     intents.guilds = True          # スレッド取得にはギルド Intent も必要
#     client = discord.Client(intents=intents)

#     @client.event
#     async def on_ready():
#         # ログインが完了したら実行される
#         print(f"✅ Logged in as {client.user} (id: {client.user.id})")

#         #2) 投稿先チャンネルオブジェクトを取得
#         channel = client.get_channel(channel_id)
#         print(f"▶️ チャンネルID {channel_id} を取得中...")
#         if channel is None:
#             print(f"❌ 指定したチャンネルID {channel_id} が見つかりません。")
#             await client.close()
#             return
        

#         # まずチャンネル履歴にアクセスできるかを確認
#         print("▶️ チャンネル履歴取得テスト開始...")
#         try:
#             recent = [msg async for msg in channel.history(limit=5)]
#             print(f"▶️ 取得メッセージ数: {len(recent)}")
#             for msg in recent:
#                 print(f"  • {msg.author.display_name}: {msg.content}")
#         except Exception as e:
#             print(f"❌ 履歴取得エラー: {e}")
#             await client.close()
#             return

#         # キャッシュ済みのスレッド一覧を見るだけなら await は不要
#         active_threads = channel.threads   # TextChannel.threads プロパティ
#         print(f"▶️ キャッシュ済みスレッド数: {len(active_threads)}")
#         for t in active_threads:
#             print(f"  • [ID:{t.id}] {t.name}")

#         # HTTP でアクティブスレッドを取りに行きたい場合は
#         # fetch_active_threads() を使うと確実です（要権限）。
#         #   resp = await channel.fetch_active_threads()
#         #   active_threads = resp.threads
#         #   print(f"▶️ API取得アクティブスレッド数: {len(active_threads)}")

#         target_thread = None
#         for t in active_threads:
#             print(t.name)
#             if t.name == thread_name:
#                 target_thread = t
#                 break

#         print(" 4) スレッドがなければ、親メッセージを使って新規スレッドを作成する")
#         if target_thread is None:
#             # 親メッセージは「チャンネルに新しく送信したメッセージ」を使う
#             parent_msg = await channel.send(f" **【{thread_name}**速報スレッド】")
#             # auto_archive_duration: 60, 1440, 4320, 10080 のいずれか（分単位）
#             target_thread = await parent_msg.create_thread(
#                 name=thread_name,
#                 auto_archive_duration=1440  # 例：24時間で自動アーカイブ
#             )
#             print(f"🆕 新規スレッド作成: {thread_name}")
#         else:
#             print(f"🔁 既存スレッドを使用: {thread_name}")

#         # 5) 取得または作成したスレッド内にメッセージを送信
#         await target_thread.send(content)
#         print(f"✉️ スレッド「{thread_name}」にメッセージ送信完了")

#         # 6) 投稿し終わったら Bot をログアウトしてスクリプトを終了
#         await client.close()

#     # Botを起動（イベントループを開始）
#     try:
#         await client.start(token)
#     except Exception as e:
#         print(f"❌ Botの起動中にエラー: {e}")

# ─── エントリポイント: asyncio.run で実行 ───────────# ──────────────────────────
def main():
    print("🔄 Discordスレッド投稿スクリプトを開始します...")
    # # 1) 引数を取得
    #args = parse_a# rgs()

    # 2) 環境変数または固定# 値で Bot トー# クンを取得
    #    → 実運用では Secrets や環境# 変数から読み込むことを強く推奨

if __name__ == "__main__":
    channel_id = int(1380200984256450751)
    token = os.environ["DISCORD_BOT_TOKEN"]
    asyncio.run(delete_all_threads(
        token=token,
        channel_id=channel_id
    ))

    main()