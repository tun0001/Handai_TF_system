#!/usr/bin/env python3
"""
DataFrame機能の使用例

scrape_player_results.pyの新しいDataFrame機能の使用方法を示すサンプルコード
"""

import sys
sys.path.append('/workspaces/Handai_TF_system')

from scrape_player_results import scrape_player_results_to_dataframe
import pandas as pd

def main():
    """DataFrame機能を使用したサンプル"""
    
    # 大会URLと選手名を指定
    timetable_url = "http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html"
    player_name = "吉田隼人"
    
    print("🔄 DataFrame機能の使用例")
    print(f"📅 大会URL: {timetable_url}")
    print(f"👤 選手名: {player_name}")
    print()
    
    try:
        # 大会名とDataFrameを取得
        meet_name, df = scrape_player_results_to_dataframe(timetable_url, player_name)
        
        print(f"\n✅ 取得完了!")
        print(f"🏆 大会名: {meet_name}")
        
        if df is not None:
            print(f"\n📊 DataFrameの詳細情報:")
            print(f"   行数: {len(df)}")
            print(f"   列数: {len(df.columns)}")
            print(f"   データサイズ: {df.memory_usage(deep=True).sum()} bytes")
            
            print(f"\n📋 列の詳細:")
            for i, col in enumerate(df.columns, 1):
                dtype = df[col].dtype
                non_null_count = df[col].count()
                print(f"   {i:2d}. {col:20s} ({dtype}, {non_null_count}件)")
            
            print(f"\n🏃‍♂️ データの内容:")
            print(df.to_string(index=False))
            
            # データの統計情報
            print(f"\n📈 統計情報:")
            if 'event_name' in df.columns:
                print(f"   出場種目: {df['event_name'].nunique()}種目")
                print(f"   種目詳細: {', '.join(df['event_name'].unique())}")
            
            if 'record' in df.columns:
                records_with_data = df[df['record'].notna() & (df['record'] != '')]
                print(f"   記録のある競技: {len(records_with_data)}件")
            
            if 'is_dns' in df.columns:
                dns_count = df['is_dns'].sum()
                print(f"   DNS (欠場): {dns_count}件")
            
            # CSVファイルに保存
            csv_filename = f"player_results_{player_name}_{meet_name.replace(' ', '_')}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"\n💾 CSVファイルに保存: {csv_filename}")
            
            # Excelファイルに保存（openpyxlがインストールされている場合）
            try:
                excel_filename = f"player_results_{player_name}_{meet_name.replace(' ', '_')}.xlsx"
                df.to_excel(excel_filename, index=False)
                print(f"💾 Excelファイルに保存: {excel_filename}")
            except ImportError:
                print("⚠️ openpyxlがインストールされていないため、Excelファイルの保存をスキップ")
            
            # データの一部を分析例
            print(f"\n🔍 簡単なデータ分析例:")
            
            # 種目別の記録
            if 'event_name' in df.columns and 'record' in df.columns:
                print(f"   種目別記録:")
                for event in df['event_name'].unique():
                    event_records = df[df['event_name'] == event]['record'].dropna()
                    if len(event_records) > 0:
                        print(f"     {event}: {', '.join(event_records.astype(str))}")
                    else:
                        print(f"     {event}: 記録なし")
            
        else:
            print("❌ データが取得できませんでした")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
