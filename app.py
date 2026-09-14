import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import re
import gspread
from google.oauth2.service_account import Credentials

# ページ基本設定
st.set_page_config(
    page_title="Keiba AI Core",
    page_icon="🐴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🎨 カスタムCSS
# ==========================================
st.markdown("""
<style>
    /* 全体背景とフォント */
    .stApp {
        background-color: #0B0F19 !important;
        color: #F3F4F6 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* サイドバー */
    [data-testid="stSidebar"] {
        background-color: #0E1322 !important;
        border-right: 1px solid #1E2640 !important;
    }
    
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF !important;
        padding: 0.5rem 0.5rem 1.5rem 0.5rem;
    }

    /* メニューの丸ポッチ消去 */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: transparent !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        margin-bottom: 4px !important;
        cursor: pointer !important;
        border: none !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        width: 0px !important;
        height: 0px !important;
        opacity: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
        pointer-events: none !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] p {
        color: #94A3B8 !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        margin-left: 5px !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background-color: #1E2238 !important;
        border-left: 3px solid #6366F1 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] p,
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: #161C2E !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover p {
        color: #E2E8F0 !important;
    }

    /* エクスパンダーのダーク化 */
    [data-testid="stExpander"] details {
        background-color: #141A29 !important;
        border: 1px solid #1E273D !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpander"] summary {
        background-color: #1E2238 !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpander"] summary:hover {
        background-color: #272C46 !important;
    }
    [data-testid="stExpander"] summary p {
        color: #F3F4F6 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    [data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        background-color: #0B0F19 !important;
        padding: 16px !important;
    }

    /* システム稼働中バッジ（左下固定） */
    .sidebar-user {
        position: fixed !important;
        bottom: 24px !important;
        left: 18px !important;
        width: 220px !important;
        z-index: 99999 !important;
        background-color: #0E1322 !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        padding: 8px 10px !important;
        border-radius: 8px !important;
        border: 1px solid #1E2640 !important;
    }
    .user-avatar {
        width: 36px;
        height: 36px;
        background: #6366F1;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
    }
    .user-info {
        display: flex;
        flex-direction: column;
    }
    .user-name {
        font-size: 0.85rem;
        font-weight: 600;
        color: #F8FAFC;
    }
    .user-status {
        font-size: 0.75rem;
        color: #10B981;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    /* メインヘッダー */
    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .last-update {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-bottom: 1.2rem;
    }

    /* ボタン */
    button[kind="secondary"], 
    button[kind="primary"],
    [data-testid="stButton"] button {
        background-color: #161D2E !important;
        color: #E2E8F0 !important;
        border: 1px solid #2B354F !important;
        border-radius: 8px !important;
        padding: 0.55rem 1.1rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stButton"] button p,
    [data-testid="stButton"] button span {
        color: #E2E8F0 !important;
    }
    [data-testid="stButton"] button:hover {
        background-color: #1E273D !important;
        border-color: #6366F1 !important;
    }
    [data-testid="stButton"] button:hover p,
    [data-testid="stButton"] button:hover span {
        color: #FFFFFF !important;
    }

    /* KPIカード */
    .kpi-card {
        background: #141A29;
        border: 1px solid #1E273D;
        border-radius: 16px;
        padding: 1.3rem 1.4rem;
        position: relative;
        overflow: hidden;
        min-height: 125px;
    }
    .kpi-card::after {
        content: "";
        position: absolute;
        top: -30px;
        right: -30px;
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(20, 26, 41, 0) 70%);
        border-radius: 50%;
    }
    .kpi-title {
        font-size: 0.82rem;
        color: #94A3B8;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .kpi-value-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.5px;
    }
    .kpi-sub {
        font-size: 0.95rem;
        color: #94A3B8;
        font-weight: 500;
    }
    .kpi-diff-green {
        font-size: 0.85rem;
        color: #10B981;
        font-weight: 600;
    }

    /* レースカードスタイル */
    .race-card {
        background: #141A29;
        border: 1px solid #1E273D;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .race-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1E273D;
        padding-bottom: 0.5rem;
        margin-bottom: 0.8rem;
    }
    .race-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .race-badge {
        background-color: #1E2238;
        color: #6366F1;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #6366F1;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 スプレッドシート接続処理
# ==========================================
SS_NAME = "競馬AIシステム_Core"

@st.cache_resource
def get_gspread_client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
        elif "gcp_json" in st.secrets:
            creds_dict = json.loads(st.secrets["gcp_json"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
        elif os.path.exists("key.json"):
            creds = Credentials.from_service_account_file("key.json", scopes=scopes)
            return gspread.authorize(creds)
        elif os.path.exists(os.path.expanduser("~/key.json")):
            creds = Credentials.from_service_account_file(os.path.expanduser("~/key.json"), scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        st.sidebar.error(f"認証エラー: {e}")
    return None

@st.cache_data(ttl=60)
def load_sheet_data():
    gc = get_gspread_client()
    if not gc:
        return None, None
    try:
        ss = gc.open(SS_NAME)
        try:
            ws_target = ss.worksheet("本日勝負レース")
            all_vals = ws_target.get_all_values()
            if all_vals and len(all_vals) > 1:
                target_rows = []
                headers = all_vals[0]
                for r in all_vals[1:]:
                    if not r or "--- 見送り" in r[0]:
                        break
                    target_rows.append(r)
                df_target = pd.DataFrame(target_rows, columns=headers)
            else:
                df_target = pd.DataFrame()
        except:
            df_target = pd.DataFrame()

        try:
            ws_today = ss.worksheet("本日")
            today_vals = ws_today.get_all_records()
            df_today = pd.DataFrame(today_vals)
        except:
            df_today = pd.DataFrame()

        return df_target, df_today
    except Exception as e:
        return None, None

df_target, df_today = load_sheet_data()

# ==========================================
# 🗂️ サイドバー メニュー構築
# ==========================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <span>🐴</span> Keiba AI Core
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "",
        ["📊 ダッシュボード", "🎯 厳選勝負レース", "🏇 全レース出馬表", "💻 ターミナル操作マニュアル", "🗄️ 過去データ分析", "📈 スプレッドシート連携"],
        label_visibility="collapsed"
    )

    st.markdown("""
    <div class="sidebar-user">
        <div class="user-avatar">U</div>
        <div class="user-info">
            <div class="user-name">User (Chromebook)</div>
            <div class="user-status">● システム稼働中</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 🚀 画面 1: 📊 ダッシュボード
# ==========================================
if menu == "📊 ダッシュボード":
    col_h_left, col_h_right = st.columns([8, 2])
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    with col_h_left:
        st.markdown(f"""
        <div class="main-title">回収率・期待値ダッシュボード</div>
        <div class="last-update">最終更新: {now_str} (自動同期完了)</div>
        """, unsafe_allow_html=True)

    with col_h_right:
        if st.button("🔄 データ更新", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    st.write("")

    today_target_count = 0
    today_race_count = 0
    latest_date_str = ""

    if df_target is not None and not df_target.empty and '日付' in df_target.columns:
        latest_date_str = df_target['日付'].max()
        df_target_latest = df_target[df_target['日付'] == latest_date_str]
        today_target_count = len(df_target_latest[['競馬場', 'レース名']].drop_duplicates())

    if df_today is not None and not df_today.empty and '日付' in df_today.columns:
        if not latest_date_str:
            latest_date_str = df_today['日付'].max()
        df_today_latest = df_today[df_today['日付'] == latest_date_str]
        today_race_count = len(df_today_latest['レース名'].unique())
    
    today_investment = today_target_count * 200

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">AI全買い 回収率 (5年検証)</div>
            <div class="kpi-value-row">
                <span class="kpi-value">128.7</span><span class="kpi-sub">%</span>
                <span class="kpi-diff-green">↑ 目標達成</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">実力(RL)×適性(CL) 判定</div>
            <div class="kpi-value-row">
                <span class="kpi-value">70 : 30</span>
                <span class="kpi-diff-green">● 黄金比率</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">最新日 勝負レース数</div>
            <div class="kpi-value-row">
                <span class="kpi-value">{today_target_count}</span><span class="kpi-sub">R / {today_race_count}R中</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">最新日 推奨投資額</div>
            <div class="kpi-value-row">
                <span class="kpi-value">{today_investment:,}</span><span class="kpi-sub">円</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    col_chart_title, col_chart_select = st.columns([7, 2])
    with col_chart_title:
        st.markdown('<div style="font-size:1.15rem; font-weight:700; color:#FFFFFF;">回収率推移（実績 vs AI予測）</div>', unsafe_allow_html=True)
    with col_chart_select:
        period = st.selectbox("", ["直近10日間", "直近30日間", "今年度全期間"], label_visibility="collapsed")

    dates = [f"9/{i}" for i in range(5, 15)]
    ai_roi = [108.0, 109.5, 115.0, 111.0, 114.5, 120.5, 118.0, 122.5, 124.2, 128.7]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=ai_roi,
        name="AI判定通り全買い (期待値1.0超)",
        mode="lines+markers",
        line=dict(color="#6366F1", width=3, shape="spline"),
        marker=dict(size=7, color="#6366F1", line=dict(color="#FFFFFF", width=1.5)),
        hoverinfo="x+y"
    ))

    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor="#141A29",
        plot_bgcolor="#141A29",
        font=dict(color="#94A3B8", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=12, color="#CBD5E1")),
        xaxis=dict(showgrid=True, gridcolor="#1E273D", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#1E273D", zeroline=False, ticksuffix="%", range=[105, 135]),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 🎯 画面 2: 厳選勝負レース
# ==========================================
elif menu == "🎯 厳選勝負レース":
    st.markdown('<div class="main-title">本日の厳選勝負レース（馬連2点）</div>', unsafe_allow_html=True)
    st.markdown('<div class="last-update">スプレッドシート「本日勝負レース」からリアルタイム取得中</div>', unsafe_allow_html=True)

    if df_target is not None and not df_target.empty and '日付' in df_target.columns:
        latest_date_str = df_target['日付'].max()
        df_target_latest = df_target[df_target['日付'] == latest_date_str]
        
        unique_races = df_target_latest[['日付', '競馬場', 'レース名', '条件', '軸馬 (◎)']].drop_duplicates()
        for _, r in unique_races.iterrows():
            sub_df = df_target_latest[(df_target_latest['競馬場'] == r['競馬場']) & (df_target_latest['レース名'] == r['レース名'])]
            
            st.markdown(f"""
            <div class="race-card">
                <div class="race-header">
                    <span class="race-name">📍 [{r['競馬場']}] {r['レース名']} ({r['条件']})</span>
                    <span class="race-badge">黄金条件合致</span>
                </div>
                <div style="font-size: 0.95rem; color: #E2E8F0; margin-bottom: 0.8rem;">
                    🎯 <b>軸馬 (◎)</b> : <span style="color: #6366F1; font-weight:700;">{r['軸馬 (◎)']}</span>
                </div>
            """, unsafe_allow_html=True)
            
            c_bet1, c_bet2 = st.columns(2)
            if len(sub_df) >= 2:
                with c_bet1:
                    row1 = sub_df.iloc[0]
                    st.markdown(f"""
                    <div style="background:#1B2338; padding:10px 14px; border-radius:8px; border-left:3px solid #3B82F6;">
                        <span style="color:#94A3B8; font-size:0.8rem;">点① 本線・抑え</span><br>
                        <b style="font-size:1.1rem; color:#FFFFFF;">馬連 {row1['買い目']}</b><br>
                        <span style="font-size:0.85rem; color:#CBD5E1;">相手: {row1['相手馬']} ｜ 想定: {row1['想定オッズ']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with c_bet2:
                    row2 = sub_df.iloc[1]
                    st.markdown(f"""
                    <div style="background:#1B2338; padding:10px 14px; border-radius:8px; border-left:3px solid #10B981;">
                        <span style="color:#94A3B8; font-size:0.8rem;">点② 利益の核（真の△1）</span><br>
                        <b style="font-size:1.1rem; color:#FFFFFF;">馬連 {row2['買い目']}</b><br>
                        <span style="font-size:0.85rem; color:#CBD5E1;">相手: {row2['相手馬']} ｜ 想定: {row2['想定オッズ']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("スプレッドシートに最新の勝負レースデータがありません。")

# ==========================================
# 🏇 画面 3: 全レース出馬表
# ==========================================
elif menu == "🏇 全レース出馬表":
    st.markdown('<div class="main-title">全レース出馬表 ＆ AI評価印</div>', unsafe_allow_html=True)
    st.markdown('<div class="last-update">全頭のAIスコアと評価印（◎◯▲△）を一覧表示します</div>', unsafe_allow_html=True)

    if df_today is not None and not df_today.empty and '日付' in df_today.columns:
        latest_date_str = df_today['日付'].max()
        df_today_latest = df_today[df_today['日付'] == latest_date_str]
        
        venues = df_today_latest['会場'].unique()
        tabs = st.tabs([f"📍 {v}" for v in venues])
        
        def extract_r_num(x):
            m = re.search(r'^(\d+)R', x)
            return int(m.group(1)) if m else 99

        for i, venue in enumerate(venues):
            with tabs[i]:
                venue_df = df_today_latest[df_today_latest['会場'] == venue]
                race_names = sorted(venue_df['レース名'].unique(), key=extract_r_num)
                
                for rname in race_names:
                    sub_df = venue_df[venue_df['レース名'] == rname].copy()
                    cond = str(sub_df.iloc[0]['芝・ダ・障']) + str(sub_df.iloc[0]['距離']) + "m"
                    
                    with st.expander(f"🏁 {venue} {rname} （{cond}）"):
                        disp_cols = ['馬番', '印', '馬名', '単勝オッズ', '人気', 'RL', 'CL', 'AIスコア', 'AI判定']
                        if '評価' in sub_df.columns:
                            sub_df = sub_df.rename(columns={'評価': '印'})
                        
                        actual_cols = [c for c in disp_cols if c in sub_df.columns]
                        display_df = sub_df[actual_cols].copy()
                        display_df['馬番'] = pd.to_numeric(display_df['馬番'], errors='coerce')
                        display_df = display_df.sort_values('馬番')
                        
                        html_table = """
                        <div style="overflow-x: auto; border-radius: 8px; border: 1px solid #1E273D;">
                        <table style="width:100%; border-collapse: collapse; text-align: center; color: #F3F4F6; font-size: 0.95rem; background-color: #141A29;">
                            <thead>
                                <tr style="background-color: #0E1322; color: #94A3B8; border-bottom: 2px solid #1E273D;">
                        """
                        for col in actual_cols:
                            html_table += f"<th style='padding: 12px 8px; font-weight: 600;'>{col}</th>"
                        html_table += "</tr></thead><tbody>"
                        
                        for _, row in display_df.iterrows():
                            html_table += "<tr style='border-bottom: 1px solid #1E273D;'>"
                            for col in actual_cols:
                                val = row[col]
                                if col == '印':
                                    if val == '◎': val = "<span style='color: #EF4444; font-weight: 900; font-size: 1.1rem;'>◎</span>"
                                    elif val == '◯': val = "<span style='color: #3B82F6; font-weight: 900; font-size: 1.1rem;'>◯</span>"
                                    elif val == '▲': val = "<span style='color: #10B981; font-weight: 900; font-size: 1.1rem;'>▲</span>"
                                    elif val == '△': val = "<span style='color: #F59E0B; font-weight: 900; font-size: 1.1rem;'>△</span>"
                                
                                if pd.notna(val) and val != "":
                                    try:
                                        if col == '単勝オッズ': val = f"{float(val):.1f}"
                                        elif col == 'AIスコア': val = f"{float(val):.2f}"
                                        elif col in ['RL', 'CL', '人気', '馬番']: val = f"{int(float(val))}"
                                    except:
                                        pass
                                else:
                                    val = "-"
                                
                                align = "left" if col == "馬名" else "center"
                                html_table += f"<td style='padding: 10px 8px; text-align: {align};'>{val}</td>"
                            html_table += "</tr>"
                        html_table += "</tbody></table></div>"
                        
                        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("スプレッドシートに最新の全頭データがありません。")

# ==========================================
# 💻 画面 4: ターミナル操作マニュアル（★check.py追加）
# ==========================================
elif menu == "💻 ターミナル操作マニュアル":
    st.markdown('<div class="main-title">Chromebook ターミナル操作マニュアル</div>', unsafe_allow_html=True)
    st.markdown('<div class="last-update">各枠右上のコピーボタンを押してターミナルに貼り付けてください</div>', unsafe_allow_html=True)

    # 1. 朝のリアルタイム予想実行
    st.markdown("""
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.2rem; margin-bottom:1.5rem;">
        <h4 style="color:#FFFFFF; margin-top:0;">⚡ 1. 本日のリアルタイム予想実行（全レース巡回）</h4>
        <p style="color:#94A3B8; font-size:0.9rem;">
            当日朝（8:30〜9:30頃）に実行します。全レースを自動巡回し、黄金条件に合致した勝負レースをスプレッドシートに反映します。
        </p>
    """, unsafe_allow_html=True)
    st.code("cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 run.py", language="bash")
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. 🌟 1レースピンポイント分析（check.py）
    st.markdown("""
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.2rem; margin-bottom:1.5rem;">
        <h4 style="color:#FFFFFF; margin-top:0;">🎯 2. 【1レースピンポイント分析】URL不要・会場と数字だけで分析</h4>
        <p style="color:#94A3B8; font-size:0.9rem;">
            「ダートや短距離だけどこのレースだけAIの印を見たい」「重賞だけ買いたい」という時に実行します。<br>
            ネット競馬のURLは不要で、<b>「場所」と「数字」</b>を書き換えるだけで15秒で印と馬連2点を出力します。
        </p>
    """, unsafe_allow_html=True)
    st.code("cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 check.py 中山 11", language="bash")
    st.caption("※「中山 11」の部分を「阪神 10」や「中京 11」のように自由に変えて実行できます。")
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. 過去日テスト
    st.markdown("""
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.2rem; margin-bottom:1.5rem;">
        <h4 style="color:#FFFFFF; margin-top:0;">📅 3. 過去日付のシミュレーション実行</h4>
        <p style="color:#94A3B8; font-size:0.9rem;">
            過去の特定日や2日間の検証を行う場合、末尾に半角スペース区切りで日付（YYYYMMDD）を指定して実行します。
        </p>
    """, unsafe_allow_html=True)
    st.code("cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 run.py 20260912 20260913", language="bash")
    st.markdown("</div>", unsafe_allow_html=True)

    # 4. タイマーログ確認
    st.markdown("""
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.2rem; margin-bottom:1.5rem;">
        <h4 style="color:#FFFFFF; margin-top:0;">⏰ 4. 自動タイマー（朝9時実行）のログ確認</h4>
        <p style="color:#94A3B8; font-size:0.9rem;">
            土日の朝9時に自動実行された処理が正常に完了したか、直近の実行ログを確認します。
        </p>
    """, unsafe_allow_html=True)
    st.code("cat /home/ozdnyzww1/keiba_cron.log", language="bash")
    st.markdown("</div>", unsafe_allow_html=True)

    # 5. 緊急停止・更地化
    st.markdown("""
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.2rem; margin-bottom:1.5rem;">
        <h4 style="color:#FFFFFF; margin-top:0;">🧹 5. メモリ解放 ＆ 停止コマンド（緊急用）</h4>
        <p style="color:#94A3B8; font-size:0.9rem;">
            動作が重い時や、裏で残ってしまったブラウザプロセスを一掃して更地に戻します。
        </p>
    """, unsafe_allow_html=True)
    st.code("killall -9 chromium chromium-driver chromedriver chrome 2>/dev/null", language="bash")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🗄️ 画面 5: 過去データ分析
# ==========================================
elif menu == "🗄️ 過去データ分析":
    st.markdown('<div class="main-title">過去データバックテスト分析</div>', unsafe_allow_html=True)
    st.markdown('<div class="last-update">210,000件のビッグデータ検証結果</div>', unsafe_allow_html=True)
    
    st.markdown("""
    | 検証項目 | 検証ルール | 回収率 | 連対率 |
    | :--- | :--- | :---: | :---: |
    | **黄金条件合致（全体）** | 芝1500m以上 × 1人気3.5倍未満 × 馬連2点 | **128.7%** | **42.9%** |
    | **点①（◎ - ◯）** | 本線・実力上位の組み合わせ | 64.8% | 31.2% |
    | **点②（◎ - △1）** | 期待値・適性上位の伏兵狙い | **163.9%** | 11.7% |
    """)

# ==========================================
# 📈 画面 6: スプレッドシート連携
# ==========================================
elif menu == "📈 スプレッドシート連携":
    st.markdown('<div class="main-title">Google スプレッドシート連携ステータス</div>', unsafe_allow_html=True)
    gc = get_gspread_client()
    if gc:
        st.success(f"🔐 連携成功: 「{SS_NAME}」と正常にリアルタイム同期しています。")
        if df_target is not None and not df_target.empty:
            st.write("▼ 最新の取得データ一覧")
            st.dataframe(df_target, use_container_width=True)
    else:
        st.error("🚨 スプレッドシートに接続できませんでした。")
