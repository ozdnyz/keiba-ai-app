import os
import sys
import re
from datetime import datetime
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ページ設定
st.set_page_config(page_title="競馬AI 投資支援システム", page_icon="🏇", layout="wide")

# key.json のパス解決（実行ディレクトリに依存しない設定）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, "key.json")
if not os.path.exists(KEY_FILE) and os.path.exists("key.json"):
    KEY_FILE = "key.json"

SS_NAME = "競馬AIシステム_Core"

# 馬連想定倍率の計算関数
def calc_umaren_odds(o1, o2):
    if o1 <= 0 or o2 <= 0:
        return 1.5
    raw = (o1 * o2) ** 0.72 * 0.95
    return max(1.5, round(raw, 1))

# スプレッドシート接続関数
def get_gspread_client():
    if not os.path.exists(KEY_FILE):
        raise FileNotFoundError(f"'{KEY_FILE}' が見つかりません。スクリプトと同じフォルダに配置してください。")
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return gspread.authorize(creds)

# UIヘッダー
st.title("🏇 競馬AI 投資支援システム")
st.caption("検証済み黄金条件：芝主要4場 × 1500m以上 × 混戦除外 × ◎1〜2人気（回収率128.7% / 的中率34.1%）")
st.markdown("---")

col_btn, col_status = st.columns([2, 5])
with col_btn:
    exec_btn = st.button("🚀 本日の勝負レースを自動取得＆分析", use_container_width=True, type="primary")

if exec_btn:
    with st.spinner("スプレッドシートからデータを取得し、AIスコアと黄金条件を照合中..."):
        try:
            gc = get_gspread_client()
            ss = gc.open(SS_NAME)

            # データシートの読み込み
            all_dfs = []
            for ws in ss.worksheets():
                if ws.title in ["本日勝負レース", "AI予想配信"]:
                    continue
                if any(k in ws.title for k in ["本日", "当日", "最新", "データ", "202"]):
                    recs = ws.get_all_records()
                    if recs:
                        all_dfs.append(pd.DataFrame(recs))

            if not all_dfs:
                st.error("スプレッドシート内に出走データが見つかりませんでした。")
                st.stop()

            df = pd.concat(all_dfs, ignore_index=True)

            # クレンジング
            df['単勝オッズ'] = pd.to_numeric(df.get('単勝オッズ', 0), errors='coerce').fillna(0.0)
            df['人気'] = pd.to_numeric(df.get('人気', 99), errors='coerce').fillna(99)
            df['馬番'] = df.get('馬番', '').astype(str).str.strip()
            df['馬名'] = df.get('馬名', '').astype(str).str.strip()
            df['評価'] = df.get('評価', '').astype(str).str.strip()
            df['芝・ダ・障'] = df.get('芝・ダ・障', '').astype(str).str.strip()
            df['会場'] = df.get('会場', '').astype(str).str.strip()
            df['レース名'] = df.get('レース名', '').astype(str)
            df['日付'] = df.get('日付', '').astype(str).str.strip()

            # 距離抽出
            dist_col = next((c for c in df.columns if '距離' in c), None)
            if dist_col:
                df['dist_num'] = pd.to_numeric(df[dist_col].astype(str).str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
            else:
                df['dist_num'] = pd.to_numeric(df['レース名'].str.extract(r'(\d{3,4})m?')[0], errors='coerce').fillna(0)

            # 本日の日付判定（本日データがなければ最新開催日を採用）
            now = datetime.now()
            today_formats = [now.strftime("%Y/%m/%d"), f"{now.year}/{now.month}/{now.day}", now.strftime("%Y-%m-%d")]
            df_today = df[df['日付'].isin(today_formats)].copy()

            if len(df_today) > 0:
                target_date = today_formats[0]
                day_df = df_today
                st.info(f"📅 本日【 {target_date} 】の出走データを検出しました。")
            else:
                dates = sorted([d for d in df['日付'].unique() if d != "" and d != "不明"])
                target_date = dates[-1] if dates else "最新"
                day_df = df[df['日付'] == target_date].copy()
                st.warning(f"⚠️ 本日の出馬表が未投入のため、直近開催日【 {target_date} 】のデータを分析対象としています。")

            day_df['race_key'] = day_df['会場'] + "_" + day_df['レース名']

            # 主要4場判定
            major_tracks = ["東京", "中山", "阪神", "京都"]
            day_df['is_major'] = day_df['会場'].apply(lambda x: any(m in x for m in major_tracks))

            # 1番人気オッズ特定
            race_pop1 = day_df[day_df['人気'] == 1].groupby('race_key')['単勝オッズ'].min().to_dict()
            day_df['pop1_odds'] = day_df['race_key'].map(race_pop1).fillna(99.0)

            target_races = []
            sheet_target_rows = []
            sheet_skip_rows = []

            for r_key, grp in day_df.groupby('race_key'):
                venue = grp.iloc[0]['会場']
                r_name = grp.iloc[0]['レース名']
                surface = grp.iloc[0]['芝・ダ・障']
                dist = int(grp.iloc[0]['dist_num'])
                is_maj = grp.iloc[0]['is_major']
                p1_odds = grp.iloc[0]['pop1_odds']

                # フィルター判定
                if not is_maj:
                    sheet_skip_rows.append([target_date, venue, r_name, "見送り", "主要4場外（ローカル場）"])
                    continue
                if surface != '芝':
                    sheet_skip_rows.append([target_date, venue, r_name, "見送り", "ダート/障害コース"])
                    continue
                if dist < 1500:
                    sheet_skip_rows.append([target_date, venue, r_name, "見送り", "短距離（1500m未満）"])
                    continue
                if p1_odds >= 3.5:
                    sheet_skip_rows.append([target_date, venue, r_name, "見送り", f"大混戦（1人気 {p1_odds}倍）"])
                    continue

                h = grp[grp['評価'] == '◎']
                t = grp[grp['評価'] == '◯']
                d = grp[grp['評価'] == '△']

                if len(h) == 0:
                    sheet_skip_rows.append([target_date, venue, r_name, "見送り", "本命(◎)未設定"])
                    continue

                h_row = h.iloc[0]
                h_pop = int(h_row['人気'])

                # 軸馬条件（1〜2番人気限定）
                if h_pop not in [1, 2]:
                    sheet_skip_rows.append([target_date, venue, r_name, "見送り", f"◎が{h_pop}番人気（鉄板軸外）"])
                    continue

                if len(t) == 0 or len(d) == 0:
                    sheet_skip_rows.append([target_date, venue, r_name, "見送り", "相手馬(◯または△)不足"])
                    continue

                t_row = t.iloc[0]
                d1_row = d.iloc[0]

                u_t = calc_umaren_odds(float(h_row['単勝オッズ']), float(t_row['単勝オッズ']))
                u_d = calc_umaren_odds(float(h_row['単勝オッズ']), float(d1_row['単勝オッズ']))

                target_races.append({
                    'venue': venue,
                    'r_name': r_name,
                    'cond': f"{surface}{dist}m",
                    'h_info': f"[{h_row['馬番']}] {h_row['馬名']} ({h_row['人気']}人気 / {h_row['単勝オッズ']}倍)",
                    't_bet': f"馬連 {h_row['馬番']} - {t_row['馬番']}",
                    't_target': f"◯ [{t_row['馬番']}] {t_row['馬名']} ({t_row['人気']}人気 / {t_row['単勝オッズ']}倍)",
                    't_odds': u_t,
                    'd_bet': f"馬連 {h_row['馬番']} - {d1_row['馬番']}",
                    'd_target': f"△1 [{d1_row['馬番']}] {d1_row['馬名']} ({d1_row['人気']}人気 / {d1_row['単勝オッズ']}倍)",
                    'd_odds': u_d,
                })

                sheet_target_rows.append([target_date, venue, r_name, f"{surface}{dist}m", f"◎ [{h_row['馬番']}] {h_row['馬名']}", "馬連", f"{h_row['馬番']} - {t_row['馬番']}", f"◯ [{t_row['馬番']}] {t_row['馬名']}", f"約 {u_t} 倍", 100])
                sheet_target_rows.append([target_date, venue, r_name, f"{surface}{dist}m", f"◎ [{h_row['馬番']}] {h_row['馬名']}", "馬連", f"{h_row['馬番']} - {d1_row['馬番']}", f"△1 [{d1_row['馬番']}] {d1_row['馬名']}", f"約 {u_d} 倍", 100])

            # スプレッドシート自動書き込み
            try:
                out_ws = ss.worksheet("本日勝負レース")
                out_ws.clear()
            except gspread.exceptions.WorksheetNotFound:
                out_ws = ss.add_worksheet(title="本日勝負レース", rows=100, cols=12)

            headers = ["日付", "競馬場", "レース名", "条件", "軸馬 (◎)", "券種", "買い目", "相手馬", "想定オッズ", "推奨金額(円)"]
            out_data = [headers] + sheet_target_rows + [[]] + [["--- 見送りレース一覧 ---", "", "", "", ""]] + [["日付", "競馬場", "レース名", "判定", "見送り理由"]] + sheet_skip_rows
            out_ws.update(range_name="A1", values=out_data)

            st.success(f"✅ 分析完了！ 対象日：{target_date} ｜ スプレッドシート [本日勝負レース] に自動保存しました。")

            # 画面カード表示
            st.subheader(f"🎯 厳選勝負レース：全 {len(target_races)} レース（計 {len(target_races)*2} 点）")
            st.metric(label="総投資額（1点100円均等買い）", value=f"{len(target_races) * 200:,} 円")

            if len(target_races) == 0:
                st.info("条件に合致するレースはありませんでした。本日は完全見送り推奨です。")
            else:
                for idx, r in enumerate(target_races, 1):
                    with st.container():
                        st.markdown(f"### 【勝負 {idx}】 {r['venue']} {r['r_name']} （{r['cond']}）")
                        st.markdown(f"**軸馬 (◎)**：`{r['h_info']}`")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.info(f"**買い目①（本線）：{r['t_bet']}**\n\n相手: {r['t_target']}\n\n想定配当: **約 {r['t_odds']} 倍** ｜ 推奨: **100円**")
                        with c2:
                            st.warning(f"**買い目②（高回収△1）：{r['d_bet']}**\n\n相手: {r['d_target']}\n\n想定配当: **約 {r['d_odds']} 倍** ｜ 推奨: **100円**")
                        st.markdown("---")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
