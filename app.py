import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json
import os
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
# 🎨 カスタムCSS（タブ崩れ修正・完全ダークテーマ）
# ==========================================
st.markdown("""
<style>
    /* 全体背景とフォント */
    .stApp {
        background-color: #0B0F19 !important;
        color: #F3F4F6 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* サイドバーの背景 */
    [data-testid="stSidebar"] {
        background-color: #0E1322 !important;
        border-right: 1px solid #1E2640 !important;
    }
    
    /* サイドバーのロゴ */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF !important;
        padding: 0.5rem 0.5rem 1.5rem 0.5rem;
    }

    /* 🌟 サイドバーメニューのテキストが見えなくなる問題を修正 */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: transparent !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        margin-bottom: 4px !important;
        cursor: pointer !important;
        border: none !important;
    }
    /* テキストの文字色を明示的に指定 */
    [data-testid="stSidebar"] div[role="radiogroup"] > label p {
        color: #94A3B8 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }
    /* 選択時のスタイル */
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background-color: #1E2238 !important;
        border-left: 3px solid #6366F1 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] p,
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    /* ホバー時のスタイル */
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: #161C2E !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover p {
        color: #E2E8F0 !important;
    }

    /* システム稼働中バッジを「画面左下」に完全固定 */
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

    /* ボタンの白抜き防止 */
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
        # 本日勝負レースシート
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

        # 本日全頭シート
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
# 🗂️ サイドバー
# ==========================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <span>🐴</span> Keiba AI Core
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "",
        ["📊 ダッシュボード", "📑 本日のレース予測", "🗄️ 過去データ分析", "📈 スプレッドシート連携"],
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
    # ヘッダー構成（「半自動運用」ボタンを削除してスッキリ2カラムに）
    col_h_left, col_h_right = st.columns([8, 2])
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    with col_h_left:
        st.markdown(f"""
        <div class="main-title">回収率・期待値ダッシュボード</div>
        <div class="last-update">最終更新: {now_str} (自動同期完了)</div>
        """, unsafe_allow_html=True)

    with col_h_right:
        st.markdown('<div class="btn-update">', unsafe_allow_html=True)
        if st.button("🔄 データ更新", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    # 🌟 最新日付のみを抽出してカウントするロジック（12/10R問題の修正）
    today_target_count = 0
    today_race_count = 0
    latest_date_str = ""

    if df_target is not None and not df_target.empty and '日付' in df_target.columns:
        latest_date_str = df_target['日付'].max() # 記録されている一番新しい日付
        df_target_latest = df_target[df_target['日付'] == latest_date_str]
        # その日付のユニークなレース名数をカウント
        today_target_count = len(df_target_latest[['競馬場', 'レース名']].drop_duplicates())

    if df_today is not None and not df_today.empty and '日付' in df_today.columns:
        if not latest_date_str:
            latest_date_str = df_today['日付'].max()
        df_today_latest = df_today[df_today['日付'] == latest_date_str]
        today_race_count = len(df_today_latest['レース名'].unique())
    
    # 投資額は最新日の勝負レース数 × 200円
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

    # 回収率推移グラフ
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
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#CBD5E1")
        ),
        xaxis=dict(showgrid=True, gridcolor="#1E273D", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#1E273D", zeroline=False, ticksuffix="%", range=[105, 135]),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 📑 画面 2: 本日のレース予測
# ==========================================
elif menu == "📑 本日のレース予測":
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
# 🗄️ 画面 3: 過去データ分析
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
# 📈 画面 4: スプレッドシート連携
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
