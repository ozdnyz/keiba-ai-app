from datetime import datetime
import html as html_lib
import json
import os
import re
from google.oauth2.service_account import Credentials
import gspread
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ページ基本設定
st.set_page_config(
    page_title="Keiba AI Core",
    page_icon="🐴",
    layout="wide",
    initial_sidebar_state="auto",
)

# ==========================================
# 🎨 カスタムCSS（左右カード完全水平・レジまぐ白枠デザイン対応）
# ==========================================
st.markdown(
    """
<style>
    .stApp {
        background-color: #0B0F19 !important;
        color: #F3F4F6 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
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

    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: transparent !important;
        padding: 10px 12px !important;
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

    /* 🌟 天候切り替えボタン */
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        background-color: #141A29 !important;
        border: 1px solid #2B354F !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
        margin-right: 8px !important;
        cursor: pointer !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        border-color: #6366F1 !important;
        background-color: #1A2238 !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
        background-color: #1E2238 !important;
        border-color: #6366F1 !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.4) !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        color: #FFFFFF !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
    }

    /* 🌟 タブデザイン */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: transparent !important;
        margin-bottom: 8px !important;
        padding: 0 !important;
        height: 38px !important;
        min-height: 38px !important;
        align-items: center !important;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #141A29 !important;
        border: 1px solid #2B354F !important;
        border-radius: 8px !important;
        color: #F3F4F6 !important;
        padding: 6px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        height: 34px !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF !important;
        border-color: #6366F1 !important;
        background-color: #1A2238 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E2238 !important;
        border-color: #6366F1 !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.4) !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 0px !important;
        margin: 0px !important;
    }

    .right-card-header {
        height: 48px !important;
        min-height: 38px !important;
        margin-bottom: 8px !important;
        display: flex !important;
        align-items: center !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        padding: 0 4px !important;
        border-bottom: none !important;
    }

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
    [data-testid="stExpander"] summary p {
        color: #F3F4F6 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    [data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        background-color: #0B0F19 !important;
        padding: 12px 8px !important;
    }

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
    .user-info { display: flex; flex-direction: column; }
    .user-name { font-size: 0.85rem; font-weight: 600; color: #F8FAFC; }
    .user-status { font-size: 0.75rem; color: #10B981; display: flex; align-items: center; gap: 4px; }

    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 4px;
        line-height: 1.25;
    }
    .last-update { font-size: 0.85rem; color: #94A3B8; margin-bottom: 1rem; }

    button[kind="secondary"], button[kind="primary"], [data-testid="stButton"] button {
        background-color: #161D2E !important;
        color: #E2E8F0 !important;
        border: 1px solid #2B354F !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stButton"] button p { color: #E2E8F0 !important; }
    [data-testid="stButton"] button:hover {
        background-color: #1E273D !important;
        border-color: #6366F1 !important;
    }

    div[class*="st-key-help_modal_btn"] button {
        width: 38px !important; height: 38px !important; min-height: 38px !important;
        max-width: 38px !important; border-radius: 50% !important; padding: 0 !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        font-size: 0.95rem !important; margin-left: auto !important;
    }
    div[class*="st-key-refresh_btn"] button {
        height: 38px !important; min-height: 38px !important; padding: 0 16px !important;
        font-size: 0.88rem !important; border-radius: 8px !important; width: auto !important;
        white-space: nowrap !important; display: inline-flex !important; align-items: center !important;
    }

    .stForm [data-testid="stFormSubmitButton"] button, [data-testid="stFormSubmitButton"] button, button[kind="formSubmit"] {
        background-color: #4F46E5 !important;
        border: 1px solid #6366F1 !important;
        border-radius: 8px !important;
        padding: 0.65rem 1.6rem !important;
        font-weight: 700 !important;
        min-height: 48px !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.45) !important;
        width: 100% !important;
    }
    .stForm [data-testid="stFormSubmitButton"] button * { color: #FFFFFF !important; font-weight: 700 !important; font-size: 1.05rem !important; }

    [data-testid="stForm"] {
        background-color: #141A29 !important;
        border: 1px solid #1E273D !important;
        border-radius: 12px !important;
        padding: 1.4rem !important;
    }

    /* 🌟 リッチKPIカード */
    .kpi-rich-card {
        background: #141A29 !important;
        border: 1px solid #1E273D !important;
        border-radius: 14px !important;
        padding: 1.1rem 1.25rem !important;
        margin-bottom: 0.8rem !important;
        height: 165px !important;
        min-height: 165px !important;
        max-height: 165px !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }
    .kpi-bar-indigo { border-left: 4px solid #6366F1 !important; }
    .kpi-bar-green  { border-left: 4px solid #10B981 !important; }
    .kpi-bar-orange { border-left: 4px solid #F59E0B !important; }
    .kpi-bar-blue   { border-left: 4px solid #3B82F6 !important; }

    .kpi-rich-title {
        font-size: 0.88rem;
        color: #E2E8F0;
        font-weight: 700;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .kpi-main-metrics {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin-bottom: 0.6rem;
        border-bottom: 1px solid #1E273D;
        padding-bottom: 0.5rem;
        flex-wrap: wrap;
        gap: 8px;
    }
    .kpi-big-val { font-size: 1.95rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px; }
    .kpi-sub-rate { font-size: 1rem; color: #CBD5E1; font-weight: 700; }
    .kpi-money-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.88rem;
        color: #CBD5E1;
        flex-wrap: wrap;
        gap: 4px;
    }
    .kpi-profit-pos { color: #10B981; font-weight: 700; }
    .kpi-profit-neg { color: #EF4444; font-weight: 700; }

    .race-card {
        background: #141A29;
        border: 1px solid #1E273D;
        border-radius: 12px;
        padding: 1.1rem;
        margin-bottom: 1rem;
    }
    .race-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1E273D;
        padding-bottom: 0.5rem;
        margin-bottom: 0.8rem;
        flex-wrap: wrap;
        gap: 6px;
    }
    .race-name { font-size: 1.05rem; font-weight: 700; color: #FFFFFF; }
    .race-badge {
        background-color: #1E2238;
        color: #6366F1;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #6366F1;
    }

    .status-badge-buy {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10B981;
        color: #10B981;
        font-size: 0.88rem;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .status-badge-skip {
        background: rgba(148, 163, 184, 0.12);
        border: 1px solid #475569;
        color: #CBD5E1;
        font-size: 0.88rem;
        font-weight: 600;
        padding: 6px 12px;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 10px;
    }

    /* 🌟 見送り理由 ＆ 買い転換条件ボックス */
    .status-badge-skip-box {
        background: rgba(20, 26, 41, 0.85) !important;
        border: 1px solid #2B354F !important;
        border-left: 4px solid #64748B !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin-bottom: 10px !important;
    }
    .skip-reason-line {
        color: #CBD5E1 !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
    }
    .skip-buy-condition {
        color: #38BDF8 !important;
        font-size: 0.84rem !important;
        font-weight: 700 !important;
        margin-top: 5px !important;
        padding-top: 5px !important;
        border-top: 1px dashed #2B354F !important;
    }

    /* 🌟 レジまぐ投稿内容（画像完全再現・白角丸ボックス） */
    .rejimagu-sec-title {
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        margin-top: 1.4rem !important;
        margin-bottom: 0.75rem !important;
        letter-spacing: 0.02em !important;
    }
    .rejimagu-white-box {
        background-color: #F4F5F7 !important;
        color: #1F2937 !important;
        border-radius: 12px !important;
        padding: 1.35rem 1.6rem !important;
        font-size: 0.96rem !important;
        line-height: 1.8 !important;
        white-space: pre-wrap !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        margin-bottom: 0.6rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }

    @media screen and (max-width: 768px) {
        .main-title { font-size: 1.35rem !important; margin-bottom: 2px !important; }
        .last-update { font-size: 0.75rem !important; margin-bottom: 0.8rem !important; }
        .kpi-big-val { font-size: 1.5rem !important; }
        .sidebar-user { position: relative !important; bottom: auto !important; left: auto !important; width: 100% !important; margin-top: 2rem !important; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 🔐 スプレッドシート接続処理
# ==========================================
SS_NAME = "競馬AIシステム_Core"


@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
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
            creds = Credentials.from_service_account_file(
                os.path.expanduser("~/key.json"), scopes=scopes
            )
            return gspread.authorize(creds)
    except Exception as e:
        st.sidebar.error(f"認証エラー: {e}")
    return None


@st.cache_data(ttl=60)
def load_sheet_data():
    gc = get_gspread_client()
    if not gc:
        return None, None, None, None, None
    try:
        ss = gc.open(SS_NAME)
        df_target = pd.DataFrame()
        df_skip = pd.DataFrame()

        try:
            ws_target = ss.worksheet("本日勝負レース")
            all_vals = ws_target.get_all_values()
            if all_vals and len(all_vals) > 1:
                target_rows = []
                skip_rows = []
                headers_target = all_vals[0]
                headers_skip = []
                is_skip_section = False

                for r in all_vals[1:]:
                    if not r:
                        continue
                    if "--- 見送り" in r[0]:
                        is_skip_section = True
                        continue
                    if is_skip_section:
                        if not headers_skip:
                            headers_skip = r
                        else:
                            skip_rows.append(r)
                    else:
                        target_rows.append(r)

                if target_rows:
                    df_target = pd.DataFrame(
                        target_rows, columns=headers_target[: len(target_rows[0])]
                    )
                if skip_rows and headers_skip:
                    df_skip = pd.DataFrame(
                        skip_rows, columns=headers_skip[: len(skip_rows[0])]
                    )
        except:
            df_target = pd.DataFrame()
            df_skip = pd.DataFrame()

        try:
            ws_today = ss.worksheet("本日")
            today_vals = ws_today.get_all_records()
            df_today = pd.DataFrame(today_vals)
        except:
            df_today = pd.DataFrame()

        try:
            ws_daily = ss.worksheet("日次収支")
            daily_vals = ws_daily.get_all_records()
            df_daily = pd.DataFrame(daily_vals)
        except:
            df_daily = pd.DataFrame()

        try:
            ws_g1 = ss.worksheet("G1予想")
            all_g1_vals = ws_g1.get_all_values()
            if all_g1_vals and len(all_g1_vals) > 1:
                g1_rows = []
                headers_g1 = all_g1_vals[0]
                for r in all_g1_vals[1:]:
                    if not r or "--- 見送り" in r[0]:
                        break
                    g1_rows.append(r)
                df_g1 = pd.DataFrame(
                    g1_rows, columns=headers_g1[: len(g1_rows[0])]
                )
            else:
                df_g1 = pd.DataFrame()
        except:
            df_g1 = pd.DataFrame()

        return df_target, df_today, df_daily, df_g1, df_skip
    except Exception:
        return None, None, None, None, None


df_target, df_today, df_daily_log, df_g1, df_skip = load_sheet_data()


# ==========================================
# 🌟 運用サイクルのポップアップダイアログ
# ==========================================
@st.dialog("🔄 競馬AI 運用サイクル・フロー")
def show_flow_modal():
    st.markdown(
        """
    <div style="font-size:1rem; color:#FFFFFF; font-weight:700; margin-bottom:14px;">
        「前日・朝の予想配信」と「夕方の結果回収」を分けた理想の運用サイクルです。
    </div>
    <div style="background:#141A29; border:1px solid #2B354F; border-left:5px solid #6366F1; border-radius:10px; padding:14px 16px; margin-bottom:12px;">
        <div style="font-size:1.05rem; font-weight:700; color:#FFFFFF; margin-bottom:8px;">🌅 1. 【前日夜 または 朝 9:00】 予測・出撃フェーズ（run.py）</div>
        <div style="font-size:0.9rem; color:#F3F4F6; line-height:1.7;">
            <span style="color:#818CF8; font-weight:700;">・処理</span>: 全レース自動巡回 ➔ 芝・ダート極選条件合致レースを抽出（👑 ハイブリッド計8点）<br>
            <span style="color:#818CF8; font-weight:700;">・反映先</span>: 「本日」「本日勝負レース」シート ＆ 「📝 レジまぐ投稿内容」タブ<br>
            <span style="color:#818CF8; font-weight:700;">・操作</span>: 「📝 レジまぐ投稿内容」から記事をコピペ投稿 ＆ 馬券購入
        </div>
    </div>
    <div style="background:#141A29; border:1px solid #2B354F; border-left:5px solid #10B981; border-radius:10px; padding:14px 16px; margin-bottom:12px;">
        <div style="font-size:1.05rem; font-weight:700; color:#FFFFFF; margin-bottom:8px;">🌆 2. 【夕方 17:00】 収支確定フェーズ（result.py）</div>
        <div style="font-size:0.9rem; color:#F3F4F6; line-height:1.7;">
            <span style="color:#34D399; font-weight:700;">・処理</span>: 確定着順と配当を自動回収 ➔ AI買い目（計800円）と照合<br>
            <span style="color:#34D399; font-weight:700;">・反映先</span>: 「日次収支」シート（1日1行）<br>
            <span style="color:#34D399; font-weight:700;">・操作</span>: 左メニュー「💰 収支入力・管理」から今日の総購入額と総払戻額を保存
        </div>
    </div>
    <div style="background:#141A29; border:1px solid #2B354F; border-left:5px solid #F59E0B; border-radius:10px; padding:14px 16px;">
        <div style="font-size:1.05rem; font-weight:700; color:#FFFFFF; margin-bottom:8px;">🌙 3. 【夜〜週明け】 データ資産蓄積フェーズ</div>
        <div style="font-size:0.9rem; color:#F3F4F6; line-height:1.7;">
            <span style="color:#FBBF24; font-weight:700;">・処理</span>: 確定データベースから全レース結果・血統・タイム等を安全に回収<br>
            <span style="color:#FBBF24; font-weight:700;">・目的</span>: 将来のモデルチューニングや回収率検証用
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ==========================================
# 🗂️ サイドバー メニュー構築
# ==========================================
with st.sidebar:
    st.markdown(
        """
    <div class="sidebar-logo">
        <span>🐴</span> Keiba AI Core
    </div>
    """,
        unsafe_allow_html=True,
    )

    menu = st.radio(
        "",
        [
            "📊 ダッシュボード",
            "🎯 厳選勝負レース",
            "📝 レジまぐ投稿内容",
            "👑 G1専用予想",
            "🏇 全レース出馬表",
            "💰 収支入力・管理",
            "💻 ターミナル操作マニュアル",
            "🗄️ 過去データ分析",
            "📈 スプレッドシート連携",
        ],
        label_visibility="collapsed",
    )

    st.markdown(
        """
    <div class="sidebar-user">
        <div class="user-avatar">U</div>
        <div class="user-info">
            <div class="user-name">User (Chromebook)</div>
            <div class="user-status">● システム稼働中</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    # ==========================================
# 🚀 画面 1: 📊 ダッシュボード
# ==========================================
if menu == "📊 ダッシュボード":
    col_h_left, col_h_right = st.columns([7, 3])
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    with col_h_left:
        st.markdown(
            f"""
            <div class="main-title">回収率・期待値ダッシュボード</div>
            <div class="last-update">最終更新: {now_str} (自動同期完了)</div>
            """,
            unsafe_allow_html=True,
        )

    with col_h_right:
        c_space, c_help, c_btn = st.columns([1.5, 1, 2.5])
        with c_help:
            if st.button("❓", key="help_modal_btn", help="全体の運用フローを確認"):
                show_flow_modal()
        with c_btn:
            if st.button("🔄 データ更新", key="refresh_btn"):
                st.cache_data.clear()
                st.rerun()

    has_real_ai = False
    has_real_usr = False

    ai_all_inv, ai_all_ret, ai_all_races, ai_all_hits = 0, 0, 0, 0
    ai_turf_inv, ai_turf_ret, ai_turf_races, ai_turf_hits = 0, 0, 0, 0
    ai_dirt_inv, ai_dirt_ret, ai_dirt_races, ai_dirt_hits = 0, 0, 0, 0

    usr_tot_inv, usr_tot_ret, usr_tot_races, usr_tot_hits = 0, 0, 0, 0

    if df_daily_log is not None and not df_daily_log.empty:
        df_daily_calc = df_daily_log.copy()
        for col in df_daily_calc.columns:
            if any(k in col for k in ["投資", "回収", "払戻", "レース", "的中", "R数"]):
                df_daily_calc[col] = pd.to_numeric(
                    df_daily_calc[col].astype(str).str.replace(",", ""), errors="coerce"
                ).fillna(0)

        if "ユーザー投資額" in df_daily_calc.columns:
            usr_tot_inv = int(df_daily_calc["ユーザー投資額"].sum())
            usr_tot_ret = int(df_daily_calc["ユーザー回収額"].sum())
            usr_tot_races = int(
                df_daily_calc.get(
                    "ユーザーレース数", pd.Series([0] * len(df_daily_calc))
                ).sum()
            )
            usr_tot_hits = int(
                df_daily_calc.get(
                    "ユーザー的中数", pd.Series([0] * len(df_daily_calc))
                ).sum()
            )
        elif "投資額" in df_daily_calc.columns:
            usr_tot_inv = int(df_daily_calc["投資額"].sum())
            usr_tot_ret = int(df_daily_calc["払戻額"].sum())
            usr_tot_races = int(
                df_daily_calc.get("レース数", pd.Series([0] * len(df_daily_calc))).sum()
            )
            usr_tot_hits = int(
                df_daily_calc.get("的中数", pd.Series([0] * len(df_daily_calc))).sum()
            )

        if usr_tot_inv > 0 or usr_tot_races > 0:
            has_real_usr = True

        if "AI投資額" in df_daily_calc.columns and df_daily_calc["AI投資額"].sum() > 0:
            ai_all_inv = int(df_daily_calc["AI投資額"].sum())
            ai_all_ret = int(df_daily_calc["AI回収額"].sum())
            ai_all_races = int(
                df_daily_calc.get(
                    "AIレース数", pd.Series([0] * len(df_daily_calc))
                ).sum()
            )
            ai_all_hits = int(
                df_daily_calc.get("AI的中数", pd.Series([0] * len(df_daily_calc))).sum()
            )
            has_real_ai = True
        elif "投資額" in df_daily_calc.columns:
            ai_all_inv = int(df_daily_calc["投資額"].sum())
            ai_all_ret = int(df_daily_calc["払戻額"].sum())
            ai_all_races = int(
                df_daily_calc.get("レース数", pd.Series([0] * len(df_daily_calc))).sum()
            )
            ai_all_hits = int(
                df_daily_calc.get("的中数", pd.Series([0] * len(df_daily_calc))).sum()
            )
            if ai_all_inv > 0 or ai_all_races > 0:
                has_real_ai = True

        if "AI芝投資額" in df_daily_calc.columns:
            ai_turf_inv = int(df_daily_calc["AI芝投資額"].sum())
            ai_turf_ret = int(df_daily_calc["AI芝回収額"].sum())
            ai_turf_races = int(
                df_daily_calc.get(
                    "AI芝レース数", pd.Series([0] * len(df_daily_calc))
                ).sum()
            )
            ai_turf_hits = int(
                df_daily_calc.get(
                    "AI芝的中数", pd.Series([0] * len(df_daily_calc))
                ).sum()
            )

        if "AIダート投資額" in df_daily_calc.columns:
            ai_dirt_inv = int(df_daily_calc["AIダート投資額"].sum())
            ai_dirt_ret = int(df_daily_calc["AIダート回収額"].sum())
            ai_dirt_races = int(
                df_daily_calc.get(
                    "AIダートレース数", pd.Series([0] * len(df_daily_calc))
                ).sum()
            )
            ai_dirt_hits = int(
                df_daily_calc.get(
                    "AIダート的中数", pd.Series([0] * len(df_daily_calc))
                ).sum()
            )

    ai_all_roi = (ai_all_ret / ai_all_inv * 100) if ai_all_inv > 0 else 0.0
    ai_all_hit_rate = (ai_all_hits / ai_all_races * 100) if ai_all_races > 0 else 0.0

    ai_turf_roi = (ai_turf_ret / ai_turf_inv * 100) if ai_turf_inv > 0 else 0.0
    ai_turf_hit_rate = (
        (ai_turf_hits / ai_turf_races * 100) if ai_turf_races > 0 else 0.0
    )

    ai_dirt_roi = (ai_dirt_ret / ai_dirt_inv * 100) if ai_dirt_inv > 0 else 0.0
    ai_dirt_hit_rate = (
        (ai_dirt_hits / ai_dirt_races * 100) if ai_dirt_races > 0 else 0.0
    )

    usr_roi = (usr_tot_ret / usr_tot_inv * 100) if usr_tot_inv > 0 else 0.0
    usr_hit_rate = (usr_tot_hits / usr_tot_races * 100) if usr_tot_races > 0 else 0.0

    today_target_count = 0
    today_race_count = 0
    latest_date_str = ""

    if df_target is not None and not df_target.empty and "日付" in df_target.columns:
        latest_date_str = df_target["日付"].max()
        df_target_latest = df_target[df_target["日付"] == latest_date_str]
        today_target_count = len(
            df_target_latest[["競馬場", "レース名"]].drop_duplicates()
        )

    if df_today is not None and not df_today.empty and "日付" in df_today.columns:
        if not latest_date_str:
            latest_date_str = df_today["日付"].max()
        df_today_latest = df_today[df_today["日付"] == latest_date_str]
        venue_col = (
            "会場"
            if "会場" in df_today_latest.columns
            else ("競馬場" if "競馬場" in df_today_latest.columns else "")
        )
        if venue_col:
            today_race_count = len(
                df_today_latest[[venue_col, "レース名"]].drop_duplicates()
            )
        else:
            today_race_count = len(df_today_latest["レース名"].unique())

    today_investment = today_target_count * 800

    c1, c2 = st.columns(2)

    with c1:
        tab_all, tab_turf, tab_dirt = st.tabs(["🌐 総合", "🟢 芝", "🟤 ダート"])

        with tab_all:
            ai_all_profit = ai_all_ret - ai_all_inv
            p_class = "kpi-profit-pos" if ai_all_profit >= 0 else "kpi-profit-neg"
            p_sign = "+" if ai_all_profit > 0 else ""
            st.markdown(
                f"""
                <div class="kpi-rich-card kpi-bar-indigo">
                    <div class="kpi-rich-title">🌐 AI理論 総合実績 <span style="color:#6366F1; font-weight:600;">(実データ連動)</span></div>
                    <div class="kpi-main-metrics">
                        <div>
                            <span style="font-size:0.8rem; color:#CBD5E1;">通算回収率</span><br>
                            <span class="kpi-big-val">{ai_all_roi:.1f}</span><span style="font-size:1.1rem; color:#CBD5E1;">%</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:0.8rem; color:#CBD5E1;">通算的中率</span><br>
                            <span class="kpi-sub-rate">{ai_all_hit_rate:.1f}%</span> <span style="font-size:0.82rem; color:#CBD5E1;">({ai_all_hits}/{ai_all_races}R)</span>
                        </div>
                    </div>
                    <div class="kpi-money-row">
                        <span>投資: <b>{ai_all_inv:,}円</b> ➔ 払戻: <b>{ai_all_ret:,}円</b></span>
                        <span class="{p_class}">収支: {p_sign}{ai_all_profit:,}円</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab_turf:
            ai_turf_profit = ai_turf_ret - ai_turf_inv
            p_class = "kpi-profit-pos" if ai_turf_profit >= 0 else "kpi-profit-neg"
            p_sign = "+" if ai_turf_profit > 0 else ""
            st.markdown(
                f"""
                <div class="kpi-rich-card kpi-bar-green">
                    <div class="kpi-rich-title">🟢 芝レース実績 <span style="color:#10B981; font-weight:600;">(実データ連動)</span></div>
                    <div class="kpi-main-metrics">
                        <div>
                            <span style="font-size:0.8rem; color:#CBD5E1;">芝 回収率</span><br>
                            <span class="kpi-big-val">{ai_turf_roi:.1f}</span><span style="font-size:1.1rem; color:#CBD5E1;">%</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:0.8rem; color:#CBD5E1;">芝 的中率</span><br>
                            <span class="kpi-sub-rate">{ai_turf_hit_rate:.1f}%</span> <span style="font-size:0.82rem; color:#CBD5E1;">({ai_turf_hits}/{ai_turf_races}R)</span>
                        </div>
                    </div>
                    <div class="kpi-money-row">
                        <span>投資: <b>{ai_turf_inv:,}円</b> ➔ 払戻: <b>{ai_turf_ret:,}円</b></span>
                        <span class="{p_class}">収支: {p_sign}{ai_turf_profit:,}円</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab_dirt:
            ai_dirt_profit = ai_dirt_ret - ai_dirt_inv
            p_class = "kpi-profit-pos" if ai_dirt_profit >= 0 else "kpi-profit-neg"
            p_sign = "+" if ai_dirt_profit > 0 else ""
            st.markdown(
                f"""
                <div class="kpi-rich-card kpi-bar-orange">
                    <div class="kpi-rich-title">🟤 ダートレース実績 <span style="color:#F59E0B; font-weight:600;">(実データ連動)</span></div>
                    <div class="kpi-main-metrics">
                        <div>
                            <span style="font-size:0.8rem; color:#CBD5E1;">ダート 回収率</span><br>
                            <span class="kpi-big-val">{ai_dirt_roi:.1f}</span><span style="font-size:1.1rem; color:#CBD5E1;">%</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:0.8rem; color:#CBD5E1;">ダート 的中率</span><br>
                            <span class="kpi-sub-rate">{ai_dirt_hit_rate:.1f}%</span> <span style="font-size:0.82rem; color:#CBD5E1;">({ai_dirt_hits}/{ai_dirt_races}R)</span>
                        </div>
                    </div>
                    <div class="kpi-money-row">
                        <span>投資: <b>{ai_dirt_inv:,}円</b> ➔ 払戻: <b>{ai_dirt_ret:,}円</b></span>
                        <span class="{p_class}">収支: {p_sign}{ai_dirt_profit:,}円</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c2:
        st.markdown(
            '<div class="right-card-header">👤 あなたの実戦 通算成績 (実投票)</div>',
            unsafe_allow_html=True,
        )

        if has_real_usr and (usr_tot_inv > 0 or usr_tot_races > 0):
            usr_profit = usr_tot_ret - usr_tot_inv
            usr_profit_class = (
                "kpi-profit-pos" if usr_profit >= 0 else "kpi-profit-neg"
            )
            usr_profit_sign = "+" if usr_profit > 0 else ""
            st.markdown(
                f"""
                <div class="kpi-rich-card kpi-bar-green">
                    <div class="kpi-rich-title">👤 実投票 実績 <span style="color:#10B981; font-weight:600;">(日次収支シート連動)</span></div>
                    <div class="kpi-main-metrics">
                        <div>
                            <span style="font-size:0.8rem; color:#CBD5E1;">実回収率</span><br>
                            <span class="kpi-big-val">{usr_roi:.1f}</span><span style="font-size:1.1rem; color:#CBD5E1;">%</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:0.8rem; color:#CBD5E1;">実的中率</span><br>
                            <span class="kpi-sub-rate">{usr_hit_rate:.1f}%</span> <span style="font-size:0.82rem; color:#CBD5E1;">({usr_tot_hits}/{usr_tot_races}R)</span>
                        </div>
                    </div>
                    <div class="kpi-money-row">
                        <span>投資: <b>{usr_tot_inv:,}円</b> ➔ 払戻: <b>{usr_tot_ret:,}円</b></span>
                        <span class="{usr_profit_class}">収支: {usr_profit_sign}{usr_profit:,}円</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="kpi-rich-card kpi-bar-green">
                    <div class="kpi-rich-title">👤 実投票 実績 <span style="color:#10B981; font-weight:600;">(日次収支シート連動)</span></div>
                    <div class="kpi-main-metrics">
                        <div>
                            <span style="font-size:0.8rem; color:#CBD5E1;">実回収率</span><br>
                            <span class="kpi-big-val">-</span><span style="font-size:1.1rem; color:#CBD5E1;">%</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:0.8rem; color:#CBD5E1;">実的中率</span><br>
                            <span class="kpi-sub-rate">-</span>
                        </div>
                    </div>
                    <div class="kpi-money-row">
                        <span>左メニュー「💰 収支入力」から記録可能</span>
                        <span style="color:#94A3B8;">未入力</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(
            f"""
            <div style="background:#141A29; border:1px solid #1E273D; border-radius:10px; padding:0.9rem 1.1rem; margin-bottom:0.6rem;">
                <div style="font-size:0.82rem; color:#CBD5E1;">🎯 最新日 ({latest_date_str}) 勝負レース数</div>
                <div style="font-size:1.4rem; font-weight:700; color:#FFFFFF;">{today_target_count} <span style="font-size:0.85rem; color:#94A3B8; font-weight:400;">R / {today_race_count}R中</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div style="background:#141A29; border:1px solid #1E273D; border-radius:10px; padding:0.9rem 1.1rem; margin-bottom:0.6rem;">
                <div style="font-size:0.82rem; color:#CBD5E1;">💸 最新日 推奨投資額 (計800円)</div>
                <div style="font-size:1.4rem; font-weight:700; color:#FFFFFF;">{today_investment:,} <span style="font-size:0.85rem; color:#94A3B8; font-weight:400;">円</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # 回収率推移グラフ
    col_chart_title, col_chart_select = st.columns([6, 4])
    with col_chart_title:
        st.markdown(
            '<div style="font-size:1.1rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">回収率推移</div>',
            unsafe_allow_html=True,
        )
    with col_chart_select:
        chart_mode = st.selectbox(
            "期間・単位",
            [
                "日毎 (直近10日)",
                "日毎 (直近30日)",
                "月ごと (月別集計)",
                "年ごと (年別集計)",
                "全期間 (累積推移)",
            ],
            label_visibility="collapsed",
        )

    fig = go.Figure()
    max_plot_val = 110.0

    if (
        (has_real_ai or has_real_usr)
        and df_daily_log is not None
        and not df_daily_log.empty
    ):
        df_plot = df_daily_calc.copy()
        df_plot["日付_dt"] = pd.to_datetime(df_plot["日付"], errors="coerce")
        df_plot = (
            df_plot.dropna(subset=["日付_dt"])
            .sort_values("日付_dt")
            .reset_index(drop=True)
        )

        if not df_plot.empty:
            ai_inv_col = (
                "AI投資額"
                if "AI投資額" in df_plot.columns
                else ("投資額" if "投資額" in df_plot.columns else "")
            )
            ai_ret_col = (
                "AI回収額"
                if "AI回収額" in df_plot.columns
                else ("払戻額" if "払戻額" in df_plot.columns else "")
            )
            usr_inv_col = (
                "ユーザー投資額"
                if "ユーザー投資額" in df_plot.columns
                else ("投資額" if "投資額" in df_plot.columns else "")
            )
            usr_ret_col = (
                "ユーザー回収額"
                if "ユーザー回収額" in df_plot.columns
                else ("払戻額" if "払戻額" in df_plot.columns else "")
            )

            if chart_mode == "月ごと (月別集計)":
                df_plot["集計キー"] = df_plot["日付_dt"].dt.strftime("%Y/%m")
                agg_cols = {
                    c: "sum"
                    for c in [ai_inv_col, ai_ret_col, usr_inv_col, usr_ret_col]
                    if c
                }
                sub_df = (
                    df_plot.groupby("集計キー", as_index=False)
                    .agg(agg_cols)
                    .sort_values("集計キー")
                )
                x_vals = sub_df["集計キー"].tolist()

                if ai_inv_col and ai_ret_col and sub_df[ai_inv_col].sum() > 0:
                    ai_vals = np.where(
                        sub_df[ai_inv_col] > 0,
                        (sub_df[ai_ret_col] / sub_df[ai_inv_col]) * 100,
                        0.0,
                    )
                    max_plot_val = max(
                        max_plot_val, float(np.max(ai_vals)) if len(ai_vals) > 0 else 0
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=x_vals,
                            y=ai_vals,
                            name="AI理論 (月別)",
                            mode="lines+markers",
                            line=dict(color="#6366F1", width=2.5),
                            marker=dict(size=7, color="#6366F1"),
                            hovertemplate="%{x}<br>AI月別回収率: %{y:.1f}%<extra></extra>",
                        )
                    )

                if usr_inv_col and usr_ret_col and sub_df[usr_inv_col].sum() > 0:
                    usr_vals = np.where(
                        sub_df[usr_inv_col] > 0,
                        (sub_df[usr_ret_col] / sub_df[usr_inv_col]) * 100,
                        0.0,
                    )
                    max_plot_val = max(
                        max_plot_val, float(np.max(usr_vals)) if len(usr_vals) > 0 else 0
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=x_vals,
                            y=usr_vals,
                            name="あなたの実戦 (月別)",
                            mode="lines+markers",
                            line=dict(color="#10B981", width=2.5),
                            marker=dict(size=7, color="#10B981"),
                            hovertemplate="%{x}<br>実戦月別回収率: %{y:.1f}%<extra></extra>",
                        )
                    )

            elif chart_mode == "年ごと (年別集計)":
                df_plot["集計キー"] = df_plot["日付_dt"].dt.strftime("%Y年")
                agg_cols = {
                    c: "sum"
                    for c in [ai_inv_col, ai_ret_col, usr_inv_col, usr_ret_col]
                    if c
                }
                sub_df = (
                    df_plot.groupby("集計キー", as_index=False)
                    .agg(agg_cols)
                    .sort_values("集計キー")
                )
                x_vals = sub_df["集計キー"].tolist()

                if ai_inv_col and ai_ret_col and sub_df[ai_inv_col].sum() > 0:
                    ai_vals = np.where(
                        sub_df[ai_inv_col] > 0,
                        (sub_df[ai_ret_col] / sub_df[ai_inv_col]) * 100,
                        0.0,
                    )
                    max_plot_val = max(
                        max_plot_val, float(np.max(ai_vals)) if len(ai_vals) > 0 else 0
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=x_vals,
                            y=ai_vals,
                            name="AI理論 (年別)",
                            mode="lines+markers",
                            line=dict(color="#6366F1", width=2.5),
                            marker=dict(size=7, color="#6366F1"),
                            hovertemplate="%{x}<br>AI年別回収率: %{y:.1f}%<extra></extra>",
                        )
                    )

                if usr_inv_col and usr_ret_col and sub_df[usr_inv_col].sum() > 0:
                    usr_vals = np.where(
                        sub_df[usr_inv_col] > 0,
                        (sub_df[usr_ret_col] / sub_df[usr_inv_col]) * 100,
                        0.0,
                    )
                    max_plot_val = max(
                        max_plot_val, float(np.max(usr_vals)) if len(usr_vals) > 0 else 0
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=x_vals,
                            y=usr_vals,
                            name="あなたの実戦 (年別)",
                            mode="lines+markers",
                            line=dict(color="#10B981", width=2.5),
                            marker=dict(size=7, color="#10B981"),
                            hovertemplate="%{x}<br>実戦年別回収率: %{y:.1f}%<extra></extra>",
                        )
                    )

            else:
                if ai_inv_col and ai_ret_col:
                    df_plot["AI_CUM_I"] = df_plot[ai_inv_col].cumsum()
                    df_plot["AI_CUM_R"] = df_plot[ai_ret_col].cumsum()
                    df_plot["AI_ROI"] = np.where(
                        df_plot["AI_CUM_I"] > 0,
                        (df_plot["AI_CUM_R"] / df_plot["AI_CUM_I"]) * 100,
                        0.0,
                    )

                if usr_inv_col and usr_ret_col:
                    df_plot["USR_CUM_I"] = df_plot[usr_inv_col].cumsum()
                    df_plot["USR_CUM_R"] = df_plot[usr_ret_col].cumsum()
                    df_plot["USR_ROI"] = np.where(
                        df_plot["USR_CUM_I"] > 0,
                        (df_plot["USR_CUM_R"] / df_plot["USR_CUM_I"]) * 100,
                        0.0,
                    )

                if chart_mode == "日毎 (直近10日)":
                    sub_df = df_plot.tail(10).copy()
                elif chart_mode == "日毎 (直近30日)":
                    sub_df = df_plot.tail(30).copy()
                else:
                    sub_df = df_plot.copy()

                x_vals = sub_df["日付_dt"].dt.strftime("%m/%d").tolist()

                if (
                    ai_inv_col
                    and ai_ret_col
                    and "AI_ROI" in sub_df.columns
                    and sub_df[ai_inv_col].sum() > 0
                ):
                    ai_vals = sub_df["AI_ROI"].values
                    max_plot_val = max(
                        max_plot_val, float(np.max(ai_vals)) if len(ai_vals) > 0 else 0
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=x_vals,
                            y=ai_vals,
                            name="AI理論 (累積)",
                            mode="lines+markers",
                            line=dict(color="#6366F1", width=2.5, shape="spline"),
                            marker=dict(size=7, color="#6366F1"),
                            hovertemplate="%{x}<br>AI通算: %{y:.1f}%<extra></extra>",
                        )
                    )

                if (
                    usr_inv_col
                    and usr_ret_col
                    and "USR_ROI" in sub_df.columns
                    and sub_df[usr_inv_col].sum() > 0
                ):
                    usr_vals = sub_df["USR_ROI"].values
                    max_plot_val = max(
                        max_plot_val, float(np.max(usr_vals)) if len(usr_vals) > 0 else 0
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=x_vals,
                            y=usr_vals,
                            name="あなたの実戦 (累積)",
                            mode="lines+markers",
                            line=dict(color="#10B981", width=2.5, shape="spline"),
                            marker=dict(size=7, color="#10B981"),
                            hovertemplate="%{x}<br>実戦通算: %{y:.1f}%<extra></extra>",
                        )
                    )

    else:
        dates = [f"9/{i}" for i in range(5, 15)]
        ai_roi_demo = [108.0, 109.5, 115.0, 111.0, 114.5, 120.5, 118.0, 122.5, 124.2, 128.7]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ai_roi_demo,
                name="AI参考基準",
                mode="lines+markers",
                line=dict(color="#6366F1", width=2.5, shape="spline"),
                marker=dict(size=6, color="#6366F1"),
            )
        )

    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="#475569",
        annotation_text="100%",
        annotation_position="bottom right",
        annotation_font_color="#94A3B8",
    )

    y_max = max(120.0, max_plot_val * 1.15)

    fig.update_layout(
        height=300,
        margin=dict(l=5, r=5, t=15, b=10),
        paper_bgcolor="#141A29",
        plot_bgcolor="#141A29",
        font=dict(color="#94A3B8", size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#CBD5E1"),
        ),
        xaxis=dict(showgrid=True, gridcolor="#1E273D", zeroline=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1E273D",
            zeroline=True,
            zerolinecolor="#334155",
            ticksuffix="%",
            range=[-8, y_max],
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ==========================================
# 🎯 画面 2: 厳選勝負レース（見送り監視リストも併設）
# ==========================================
elif menu == "🎯 厳選勝負レース":
    st.markdown(
        '<div class="main-title">厳選勝負レース</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="last-update">スプレッドシート「本日勝負レース」からリアルタイム取得中</div>',
        unsafe_allow_html=True,
    )

    if (
        df_target is not None
        and not df_target.empty
        and "日付" in df_target.columns
    ):
        latest_date_str = df_target["日付"].max()
        df_target_latest = df_target[df_target["日付"] == latest_date_str]

        unique_races = df_target_latest[
            ["日付", "競馬場", "レース名", "条件"]
        ].drop_duplicates()

        for _, r in unique_races.iterrows():
            sub_df = df_target_latest[
                (df_target_latest["競馬場"] == r["競馬場"])
                & (df_target_latest["レース名"] == r["レース名"])
            ]

            first_jiku = (
                str(sub_df["軸馬 (◎)"].iloc[0])
                if "軸馬 (◎)" in sub_df.columns
                else ""
            )
            if "BOX" in first_jiku:
                all_box_nums = set()
                for km in sub_df.get("買い目", []):
                    all_box_nums.update(re.findall(r"\d+", str(km)))
                sorted_box = sorted(list(all_box_nums), key=lambda x: int(x))
                jiku_disp = (
                    f"ワイドBOX選出馬: 【 {'番, '.join(sorted_box)}番 】 (計{len(sub_df)}点)"
                    if sorted_box
                    else "ワイドBOX"
                )
            else:
                jiku_disp = first_jiku

            st.markdown(
                f"""
                <div class="race-card">
                    <div class="race-header">
                        <span class="race-name">📍 [{r['競馬場']}] {r['レース名']} ({r['条件']})</span>
                        <span class="race-badge">👑 勝負レース ({r['日付']})</span>
                    </div>
                    <div style="font-size: 0.95rem; color: #E2E8F0; margin-bottom: 0.8rem;">
                        🎯 <b>選定内容 / 軸馬</b> : <span style="color: #6366F1; font-weight:700;">{jiku_disp}</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            sub_df["_kenshu"] = (
                sub_df["券種"].astype(str).str.strip()
                if "券種" in sub_df.columns
                else ""
            )
            df_wide = sub_df[sub_df["_kenshu"].str.contains("ワイド", na=False)]
            df_umatan = sub_df[
                sub_df["_kenshu"].str.contains("馬単", na=False)
                | sub_df["買い目"].astype(str).str.contains("➔", na=False)
            ]
            df_other = sub_df[
                ~sub_df.index.isin(df_wide.index)
                & ~sub_df.index.isin(df_umatan.index)
            ]

            if not df_wide.empty:
                w_label = (
                    "🛡️ ワイド / ワイドBOX"
                    if "BOX" in first_jiku
                    else "🛡️ 【守り】ワイド5点（各100円・計500円）"
                )
                st.markdown(
                    f'<div style="font-size:0.85rem; font-weight:700; color:#10B981; margin-bottom:6px;">{w_label}</div>',
                    unsafe_allow_html=True,
                )
                w_cols = st.columns(min(len(df_wide), 6))
                for w_i, (_, row_w) in enumerate(df_wide.head(6).iterrows()):
                    with w_cols[w_i]:
                        k_name = row_w.get("券種", "ワイド")
                        st.markdown(
                            f"""
                            <div style="background:#1B2338; padding:8px 10px; border-radius:8px; border-left:3px solid #10B981; margin-bottom:6px;">
                                <b style="font-size:0.95rem; color:#FFFFFF;">{k_name} {row_w['買い目']}</b><br>
                                <span style="font-size:0.78rem; color:#CBD5E1;">相手: {row_w.get('相手馬', '')}<br>想定: {row_w.get('想定オッズ', '')}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            if not df_umatan.empty:
                st.markdown(
                    '<div style="font-size:0.85rem; font-weight:700; color:#F59E0B; margin-top:6px; margin-bottom:6px;">🚀 【攻め】馬単1着固定3点（各100円・計300円）</div>',
                    unsafe_allow_html=True,
                )
                u_cols = st.columns(min(len(df_umatan), 3))
                for u_i, (_, row_u) in enumerate(df_umatan.head(3).iterrows()):
                    with u_cols[u_i]:
                        st.markdown(
                            f"""
                            <div style="background:#1B2338; padding:8px 10px; border-radius:8px; border-left:3px solid #F59E0B; margin-bottom:6px;">
                                <b style="font-size:0.95rem; color:#FFFFFF;">馬単 {row_u['買い目']}</b><br>
                                <span style="font-size:0.78rem; color:#CBD5E1;">相手: {row_u.get('相手馬', '')}<br>想定: {row_u.get('想定オッズ', '')}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            if not df_other.empty:
                st.markdown(
                    '<div style="font-size:0.85rem; font-weight:700; color:#3B82F6; margin-bottom:6px;">🎯 推奨買い目一覧</div>',
                    unsafe_allow_html=True,
                )
                o_cols = st.columns(min(len(df_other), 5))
                for o_i, (_, row_o) in enumerate(df_other.head(5).iterrows()):
                    with o_cols[o_i]:
                        t_name = row_o.get("券種", "買い目")
                        border_color = "#6366F1" if "単" in t_name else "#3B82F6"
                        st.markdown(
                            f"""
                            <div style="background:#1B2338; padding:8px 10px; border-radius:8px; border-left:3px solid {border_color}; margin-bottom:6px;">
                                <b style="font-size:0.95rem; color:#FFFFFF;">{t_name} {row_o['買い目']}</b><br>
                                <span style="font-size:0.78rem; color:#CBD5E1;">相手: {row_o.get('相手馬', '')} ｜ 想定: {row_o.get('想定オッズ', '')}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            with st.expander("📋 このレースの全買い目・詳細オッズデータを確認"):
                disp_cols = [
                    c
                    for c in [
                        "券種",
                        "買い目",
                        "相手馬",
                        "想定オッズ",
                        "推奨金額(円)",
                        "期待値",
                        "判断",
                    ]
                    if c in sub_df.columns
                ]
                st.dataframe(
                    sub_df[disp_cols], use_container_width=True, hide_index=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

    if df_skip is not None and not df_skip.empty:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        with st.expander("✋ 見送りレース一覧（判定理由チェック）", expanded=False):
            skip_disp_cols = [
                c
                for c in [
                    "日付",
                    "競馬場",
                    "レース名",
                    "判定",
                    "見送り理由",
                    "備考（固定判定）",
                    "こうなれば買い（直前のオッズ変動等）",
                ]
                if c in df_skip.columns
            ]
            if skip_disp_cols:
                st.dataframe(
                    df_skip[skip_disp_cols],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.dataframe(df_skip, use_container_width=True, hide_index=True)
    elif df_target is None or df_target.empty:
        st.info("スプレッドシートに最新の勝負レースデータがありません。")

# ==========================================
# 📝 画面 3: レジまぐ投稿内容（白枠デザイン・自動日付＆レース連動）
# ==========================================
elif menu == "📝 レジまぐ投稿内容":
    col_r_left, col_r_right = st.columns([8, 2])
    with col_r_left:
        st.markdown(
            '<div class="main-title">📝 レジまぐ投稿内容（自動生成）</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="last-update">run.py（当日実行・前日先行実行）の最新結果に合わせて、日付・対象レース・買い目が自動更新されます</div>',
            unsafe_allow_html=True,
        )
    with col_r_right:
        if st.button("🔄 最新データ反映", key="rejimagu_refresh"):
            st.cache_data.clear()
            st.rerun()

    # 最新の日付と勝負レース一覧を取得
    post_date_str = datetime.now().strftime("%Y/%m/%d")
    race_list_lines = []
    paid_area_blocks = []
    race_count = 0

    if (
        df_target is not None
        and not df_target.empty
        and "日付" in df_target.columns
    ):
        post_date_str = str(df_target["日付"].max())
        df_t_latest = df_target[df_target["日付"] == post_date_str]
        u_races = df_t_latest[
            ["日付", "競馬場", "レース名", "条件"]
        ].drop_duplicates()
        race_count = len(u_races)

        for idx_r, (_, r_info) in enumerate(u_races.iterrows(), start=1):
            v_name = str(r_info["競馬場"])
            r_name = str(r_info["レース名"])
            r_cond = str(r_info["条件"])

            # 無料エリアのレース一覧行（ご指定フォーマット: ・[東京] 3R 2歳新馬）
            race_list_lines.append(f"・[{v_name}] {r_name}")

            # 有料エリアの詳細買い目構築
            sub_t = df_t_latest[
                (df_t_latest["競馬場"] == v_name)
                & (df_t_latest["レース名"] == r_name)
            ]
            jiku_str = (
                str(sub_t["軸馬 (◎)"].iloc[0])
                if "軸馬 (◎)" in sub_t.columns and len(sub_t) > 0
                else ""
            )

            sub_t["_kenshu"] = (
                sub_t["券種"].astype(str).str.strip()
                if "券種" in sub_t.columns
                else ""
            )
            w_df = sub_t[sub_t["_kenshu"].str.contains("ワイド", na=False)]
            u_df = sub_t[
                sub_t["_kenshu"].str.contains("馬単", na=False)
                | sub_t["買い目"].astype(str).str.contains("➔", na=False)
            ]
            o_df = sub_t[
                ~sub_t.index.isin(w_df.index) & ~sub_t.index.isin(u_df.index)
            ]

            block_lines = [
                f"==================================================",
                f"■ 勝負第{idx_r}鞍：[{v_name}] {r_name}（{r_cond}）",
                f"==================================================",
                f"【軸馬】 {jiku_str}",
            ]

            # 相手馬一覧の抽出
            aite_names = []
            for _, a_row in sub_t.iterrows():
                a_txt = str(a_row.get("相手馬", "")).strip()
                if a_txt and a_txt not in aite_names and "固定" not in a_txt and "防衛" not in a_txt:
                    aite_names.append(a_txt)
            if aite_names:
                block_lines.append(f"【相手】 {' / '.join(aite_names[:5])}")

            block_lines.append("")

            if not w_df.empty:
                w_kaime = " , ".join(
                    [f"{row_w['買い目']}" for _, row_w in w_df.iterrows()]
                )
                block_lines.append(f"◆ 守り（ワイド {len(w_df)}点 / 各100円）")
                block_lines.append(f"  {w_kaime}")

            if not u_df.empty:
                u_kaime = " , ".join(
                    [f"{row_u['買い目']}" for _, row_u in u_df.iterrows()]
                )
                block_lines.append(f"◆ 攻め（馬単1着固定 {len(u_df)}点 / 各100円）")
                block_lines.append(f"  {u_kaime}")

            if not o_df.empty:
                for _, row_o in o_df.iterrows():
                    block_lines.append(
                        f"◆ 推奨（{row_o.get('券種', '買い目')}）：{row_o['買い目']} （{row_o.get('相手馬', '')}）"
                    )

            block_lines.append(f"\n推奨投資：計{len(sub_t)}点（{len(sub_t)*100:,}円）")
            paid_area_blocks.append("\n".join(block_lines))

    elif df_today is not None and not df_today.empty and "日付" in df_today.columns:
        post_date_str = str(df_today["日付"].max())

    race_list_text = (
        "\n".join(race_list_lines)
        if race_list_lines
        else "・現在、本日の対象勝負レースはありません（run.pyを実行してください）"
    )

    # ① 記事タイトル本文
    title_text = f"【{post_date_str}】競馬AI-Core 厳選勝負レースパック（全{race_count}鞍）"

    # ② 無料エリア本文（ご指定の文面・構成に完全準拠）
    free_text = f"""【競馬AI-Core 厳選勝負レースパック】
開催日：{post_date_str}
提供鞍数：全{race_count}鞍

■ 運用ポリシー・コンセプト
・独自AI指数（実力RL 70%：適性CL 30%）による厳格な期待値判定
・荒れ傾向・大混戦・低配当レースを完全排除した「厳選勝負レース」のみを配信
・守り（ワイド）× 攻め（馬単）の黄金ハイブリッド投資法

■ 本日の配信対象レース一覧
{race_list_text}

■ 注意事項
※勝馬投票券の購入は自己責任でお願いいたします。
※直前のオッズ変動に伴い、回収期待値のバランスが変動する場合があります。
--------------------------------------------------
【⚠️ 直前のオッズ低下に関する重要ルール】

当AIは「オッズの歪み（期待値）」を狙う投資モデルです。

発走5〜10分前の段階で、本線【◎-◯】の馬連オッズが「4.5倍未満」まで急落していた場合、市場の期待値が完全に消滅したと判定し、【購入見送り（ケン）】を強く推奨します。

※安すぎる馬券に無理に突っ込まないことが、長期回収率をプラスに保つ鉄則です。

よろしくお願いいたします🙇
--------------------------------------------------"""

    # ③ 有料エリア本文
    if paid_area_blocks:
        paid_races_str = "\n\n".join(paid_area_blocks)
        paid_text = f"""ご購読ありがとうございます！
本日（{post_date_str}）の厳選勝負レース・最終買い目一覧です（全{race_count}鞍）。

{paid_races_str}

--------------------------------------------------
※本線【◎-◯】の馬連オッズが発走直前に「4.5倍未満」まで急落した場合は、期待値確保のため見送り（ケン）を推奨いたします。
本日の健闘を祈ります！🏇✨"""
    else:
        paid_text = "現在、抽出された勝負レースがありません。ターミナルで run.py を実行後、「🔄 最新データ反映」ボタンを押してください。"

    # 画像通りの白枠ボックス表示 ＆ ワンクリックコピー機能
    st.markdown(
        '<div class="rejimagu-sec-title">① 記事タイトル</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="rejimagu-white-box">{html_lib.escape(title_text)}</div>',
        unsafe_allow_html=True,
    )
    with st.expander("📋 ① 記事タイトルをワンクリックコピー"):
        st.code(title_text, language="text")

    st.markdown(
        '<div class="rejimagu-sec-title">② 無料エリア本文</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="rejimagu-white-box">{html_lib.escape(free_text)}</div>',
        unsafe_allow_html=True,
    )
    with st.expander("📋 ② 無料エリア本文をワンクリックコピー"):
        st.code(free_text, language="text")

    st.markdown(
        '<div class="rejimagu-sec-title">③ 有料エリア本文</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="rejimagu-white-box">{html_lib.escape(paid_text)}</div>',
        unsafe_allow_html=True,
    )
    with st.expander("📋 ③ 有料エリア本文をワンクリックコピー"):
        st.code(paid_text, language="text")
            # ==========================================
# 👑 画面 4: G1専用予想（馬場切り替えボタン対応）
# ==========================================
elif menu == "👑 G1専用予想":
    st.markdown(
        '<div class="main-title">👑 G1専用 特化予想</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="last-update">スプレッドシート「G1予想」から最新のG1解析結果を取得中（馬場状態を切り替えて各馬場の最適買い目をシミュレーションできます）</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size:0.95rem; font-weight:700; color:#FFFFFF; margin-bottom:6px;">⛅ 馬場状態の切り替えシミュレーション</div>',
        unsafe_allow_html=True,
    )
    sel_baba_g1 = st.radio(
        "",
        ["☀️ 良", "⛅ 稍重", "☂️ 重", "🌀 不良"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_g1_baba",
    )
    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    b_val_g1 = (
        sel_baba_g1.replace("☀️ ", "")
        .replace("⛅ ", "")
        .replace("☂️ ", "")
        .replace("🌀 ", "")
    )

    if df_g1 is not None and not df_g1.empty and "日付" in df_g1.columns:
        latest_g1_date = df_g1["日付"].max()
        df_g1_latest = df_g1[df_g1["日付"] == latest_g1_date]

        if "馬場" in df_g1_latest.columns and (df_g1_latest["馬場"] == b_val_g1).any():
            df_g1_disp = df_g1_latest[df_g1_latest["馬場"] == b_val_g1]
        else:
            df_g1_disp = df_g1_latest

        unique_g1_races = df_g1_disp[
            ["日付", "競馬場", "レース名", "条件"]
        ].drop_duplicates()

        for _, r in unique_g1_races.iterrows():
            sub_df = df_g1_disp[
                (df_g1_disp["競馬場"] == r["競馬場"])
                & (df_g1_disp["レース名"] == r["レース名"])
            ]

            judge_str = (
                str(sub_df["判断"].iloc[0])
                if "判断" in sub_df.columns and len(sub_df) > 0
                else ""
            )
            is_buy = "買い" in judge_str
            badge_html = (
                f'<span class="status-badge-buy" style="margin-bottom:0; padding:4px 10px;">🎯 AI判定：買い勝負（{b_val_g1}）</span>'
                if is_buy
                else f'<span class="status-badge-skip" style="margin-bottom:0; padding:4px 10px;">✋ AI判定：見送り (参考買い目・{b_val_g1})</span>'
            )

            first_jiku = (
                str(sub_df["軸馬 (◎)"].iloc[0])
                if "軸馬 (◎)" in sub_df.columns
                else ""
            )
            if "BOX" in first_jiku:
                all_box_nums = set()
                for km in sub_df.get("買い目", []):
                    all_box_nums.update(re.findall(r"\d+", str(km)))
                sorted_box = sorted(list(all_box_nums), key=lambda x: int(x))
                jiku_disp = (
                    f"ワイドBOX選出馬: 【 {'番, '.join(sorted_box)}番 】 (計{len(sub_df)}点)"
                    if sorted_box
                    else "ワイドBOX"
                )
            else:
                jiku_disp = first_jiku

            st.markdown(
                f"""
                <div class="race-card" style="border: 1px solid #6366F1; margin-bottom: 1.5rem;">
                    <div class="race-header">
                        <span class="race-name" style="color:#A5B4FC;">🏆 [{r['競馬場']}] {r['レース名']} ({r['条件']} / {b_val_g1})</span>
                        {badge_html}
                    </div>
                    <div style="font-size: 0.95rem; color: #E2E8F0; margin-bottom: 0.8rem;">
                        🎯 <b>選定内容 / 軸馬</b> : <span style="color: #6366F1; font-weight:700;">{jiku_disp}</span>
                        <span style="font-size:0.82rem; color:#94A3B8; margin-left:12px;">（※見送り判定の場合はAI通算回収率に計算されません）</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            cols_grid = st.columns(min(len(sub_df), 6))
            for b_i, (_, row_b) in enumerate(sub_df.head(6).iterrows()):
                with cols_grid[b_i]:
                    k_name = row_b.get("券種", "買い目")
                    border_c = (
                        "#6366F1"
                        if "単" in k_name
                        else ("#10B981" if "ワイド" in k_name else "#F59E0B")
                    )
                    st.markdown(
                        f"""
                        <div style="background:#1B2338; padding:8px 10px; border-radius:8px; border-left:3px solid {border_c}; margin-bottom:6px;">
                            <b style="font-size:0.92rem; color:#FFFFFF;">{k_name} {row_b['買い目']}</b><br>
                            <span style="font-size:0.75rem; color:#CBD5E1;">相手: {row_b.get('相手馬', '')}<br>想定: {row_b.get('想定オッズ', '')}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with st.expander(f"📋 このG1レースの全買い目・詳細データを確認（{b_val_g1}）"):
                disp_cols = [
                    c
                    for c in ["馬場", "券種", "買い目", "相手馬", "想定オッズ", "推奨金額(円)", "判断"]
                    if c in sub_df.columns
                ]
                st.dataframe(
                    sub_df[disp_cols], use_container_width=True, hide_index=True
                )

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info(
            "スプレッドシート「G1予想」に最新のG1データがありません。土曜日にターミナルで `g1.py` を実行するか、`run.py` の実行をお待ちください。"
        )

# ==========================================
# 🏇 画面 5: 全レース出馬表
# ==========================================
elif menu == "🏇 全レース出馬表":
    st.markdown(
        '<div class="main-title">全レース出馬表 ＆ AI評価印</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="last-update">馬場状態を切り替えて、レースの買い/見送り判定と各頭の印をシミュレーションできます</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size:0.95rem; font-weight:700; color:#FFFFFF; margin-bottom:6px;">⛅ 馬場状態の切り替えシミュレーション</div>',
        unsafe_allow_html=True,
    )
    sel_baba = st.radio(
        "",
        ["☀️ 良", "⛅ 稍重", "☂️ 重", "🌀 不良"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    b_val = (
        sel_baba.replace("☀️ ", "")
        .replace("⛅ ", "")
        .replace("☂️ ", "")
        .replace("🌀 ", "")
    )

    if df_today is not None and not df_today.empty and "日付" in df_today.columns:
        latest_date_str = df_today["日付"].max()
        df_today_latest = df_today[df_today["日付"] == latest_date_str]

        if "馬場" in df_today_latest.columns and (df_today_latest["馬場"] == b_val).any():
            df_today_disp = df_today_latest[df_today_latest["馬場"] == b_val]
        else:
            df_today_disp = df_today_latest

        venues = df_today_disp["会場"].unique()
        tabs = st.tabs([f"📍 {v}" for v in venues])

        def extract_r_num(x):
            m = re.search(r"^(\d+)R", x)
            return int(m.group(1)) if m else 99

        for i, venue in enumerate(venues):
            with tabs[i]:
                venue_df = df_today_disp[df_today_disp["会場"] == venue]
                race_names = sorted(venue_df["レース名"].unique(), key=extract_r_num)

                for rname in race_names:
                    sub_df = venue_df[venue_df["レース名"] == rname].copy()
                    cond = (
                        str(sub_df.iloc[0]["芝・ダ・障"])
                        + str(sub_df.iloc[0]["距離"])
                        + "m"
                    )

                    with st.expander(f"🏁 {venue} {rname} （{cond}）"):
                        if "レース判定" in sub_df.columns:
                            r_judge = str(sub_df.iloc[0]["レース判定"])
                            r_detail = str(sub_df.iloc[0].get("レース判定詳細", ""))

                            if "買い" in r_judge:
                                st.markdown(
                                    f'<div class="status-badge-buy">🎯 {r_judge} ｜ {r_detail}</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    f'<div class="status-badge-skip">✋ {r_judge} ｜ 理由: {r_detail}</div>',
                                    unsafe_allow_html=True,
                                )

                        disp_cols = [
                            "馬番",
                            "印",
                            "馬名",
                            "単勝オッズ",
                            "人気",
                            "RL",
                            "CL",
                            "AIスコア",
                            "AI判定",
                        ]
                        if "評価" in sub_df.columns:
                            sub_df = sub_df.rename(columns={"評価": "印"})

                        actual_cols = [c for c in disp_cols if c in sub_df.columns]
                        display_df = sub_df[actual_cols].copy()
                        display_df["馬番"] = pd.to_numeric(
                            display_df["馬番"], errors="coerce"
                        )
                        display_df = display_df.sort_values("馬番")

                        html_table = """
                        <div style="overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 8px; border: 1px solid #1E273D;">
                        <table style="width:100%; border-collapse: collapse; text-align: center; color: #F3F4F6; background-color: #141A29; min-width: 520px;">
                            <thead>
                                <tr style="background-color: #0E1322; color: #94A3B8; border-bottom: 2px solid #1E273D;">
                        """
                        for col in actual_cols:
                            html_table += f"<th style='padding: 10px 6px; font-weight: 600; white-space: nowrap;'>{col}</th>"
                        html_table += "</tr></thead><tbody>"

                        for _, row in display_df.iterrows():
                            html_table += "<tr style='border-bottom: 1px solid #1E273D;'>"
                            for col in actual_cols:
                                val = row[col]
                                if col == "印":
                                    if val == "◎":
                                        val = "<span style='color: #EF4444; font-weight: 900; font-size: 1.1rem;'>◎</span>"
                                    elif val == "◯":
                                        val = "<span style='color: #3B82F6; font-weight: 900; font-size: 1.1rem;'>◯</span>"
                                    elif val == "▲":
                                        val = "<span style='color: #10B981; font-weight: 900; font-size: 1.1rem;'>▲</span>"
                                    elif "△" in str(val):
                                        val = f"<span style='color: #F59E0B; font-weight: 900; font-size: 1.05rem;'>{val}</span>"

                                if pd.notna(val) and val != "":
                                    try:
                                        if col == "単勝オッズ":
                                            val = f"{float(val):.1f}"
                                        elif col == "AIスコア":
                                            val = f"{float(val):.2f}"
                                        elif col in ["RL", "CL", "人気", "馬番"]:
                                            val = f"{int(float(val))}"
                                    except:
                                        pass
                                else:
                                    val = "-"

                                align = "left" if col == "馬名" else "center"
                                nowrap = "white-space: nowrap;" if col != "馬名" else ""
                                html_table += f"<td style='padding: 8px 6px; text-align: {align}; {nowrap}'>{val}</td>"
                            html_table += "</tr>"
                        html_table += "</tbody></table></div>"

                        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("スプレッドシートに最新の全頭データがありません。")

# ==========================================
# 💰 画面 6: 収支入力・管理
# ==========================================
elif menu == "💰 収支入力・管理":
    st.markdown(
        '<div class="main-title">日次実収支の記録</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="last-update">一日の終わりに、今日の購入実績（金額・レース数・的中数）を入力して保存してください</div>',
        unsafe_allow_html=True,
    )

    with st.form("shushi_form"):
        st.markdown(
            '<div style="font-size:0.95rem; font-weight:700; color:#FFFFFF; margin-bottom:6px;">🗓️ 競馬開催日</div>',
            unsafe_allow_html=True,
        )
        target_date = st.date_input(
            "開催日", datetime.now(), label_visibility="collapsed"
        )

        st.markdown(
            '<div style="font-size:0.9rem; font-weight:700; color:#818CF8; margin-top:14px; margin-bottom:8px;">【収支金額】</div>',
            unsafe_allow_html=True,
        )
        c_in1, c_in2 = st.columns(2)
        with c_in1:
            st.markdown(
                '<div style="font-size:0.9rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">💸 今日の総購入額 (円)</div>',
                unsafe_allow_html=True,
            )
            usr_inv = st.number_input(
                "総購入額", min_value=0, value=0, step=100, label_visibility="collapsed"
            )
        with c_in2:
            st.markdown(
                '<div style="font-size:0.9rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">💰 今日の総払戻額 (円)</div>',
                unsafe_allow_html=True,
            )
            usr_ret = st.number_input(
                "総払戻額", min_value=0, value=0, step=100, label_visibility="collapsed"
            )

        st.markdown(
            '<div style="font-size:0.9rem; font-weight:700; color:#34D399; margin-top:14px; margin-bottom:8px;">【的中率カウント】</div>',
            unsafe_allow_html=True,
        )
        c_in3, c_in4 = st.columns(2)
        with c_in3:
            st.markdown(
                '<div style="font-size:0.9rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">🏇 実際に購入したレース数</div>',
                unsafe_allow_html=True,
            )
            usr_races = st.number_input(
                "購入レース数", min_value=0, value=0, step=1, label_visibility="collapsed"
            )
        with c_in4:
            st.markdown(
                '<div style="font-size:0.9rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">🎯 的中したレース数</div>',
                unsafe_allow_html=True,
            )
            usr_hits = st.number_input(
                "的中レース数", min_value=0, value=0, step=1, label_visibility="collapsed"
            )

        st.write("")
        submit = st.form_submit_button("💾 スプレッドシートに保存")

        if submit:
            gc = get_gspread_client()
            if gc:
                date_str = target_date.strftime("%Y/%m/%d")
                try:
                    ss = gc.open(SS_NAME)
                    try:
                        ws = ss.worksheet("日次収支")
                    except:
                        ws = ss.add_worksheet(title="日次収支", rows="500", cols="10")
                        ws.append_row([
                            "日付",
                            "AI投資額",
                            "AI回収額",
                            "ユーザー投資額",
                            "ユーザー回収額",
                            "AIレース数",
                            "AI的中数",
                            "ユーザーレース数",
                            "ユーザー的中数",
                        ])

                    cur_h = ws.row_values(1)
                    if len(cur_h) < 9:
                        std_h = [
                            "日付",
                            "AI投資額",
                            "AI回収額",
                            "ユーザー投資額",
                            "ユーザー回収額",
                            "AIレース数",
                            "AI的中数",
                            "ユーザーレース数",
                            "ユーザー的中数",
                        ]
                        for idx_h, h_val in enumerate(std_h, start=1):
                            ws.update_cell(1, idx_h, h_val)

                    records = ws.get_all_values()
                    found_row = -1
                    for i, row in enumerate(records):
                        if len(row) > 0 and row[0] == date_str:
                            found_row = i + 1
                            break

                    headers = ws.row_values(1)

                    def get_col(name, default_idx):
                        return headers.index(name) + 1 if name in headers else default_idx

                    col_u_inv = get_col("ユーザー投資額", 8)
                    col_u_ret = get_col("ユーザー回収額", 9)
                    col_u_races = get_col("ユーザーレース数", 16)
                    col_u_hits = get_col("ユーザー的中数", 17)

                    if found_row != -1:
                        ws.update_cell(found_row, col_u_inv, usr_inv)
                        ws.update_cell(found_row, col_u_ret, usr_ret)
                        ws.update_cell(found_row, col_u_races, usr_races)
                        ws.update_cell(found_row, col_u_hits, usr_hits)
                        st.success(
                            f"✅ {date_str} の実戦記録を更新しました！（投資: {usr_inv:,}円 / 回収: {usr_ret:,}円 / 的中: {usr_hits}/{usr_races}R）"
                        )
                    else:
                        new_row = [date_str] + [0] * max(0, len(headers) - 1)
                        if len(new_row) >= col_u_inv:
                            new_row[col_u_inv - 1] = usr_inv
                        if len(new_row) >= col_u_ret:
                            new_row[col_u_ret - 1] = usr_ret
                        if len(new_row) >= col_u_races:
                            new_row[col_u_races - 1] = usr_races
                        if len(new_row) >= col_u_hits:
                            new_row[col_u_hits - 1] = usr_hits
                        ws.append_row(new_row)
                        st.success(
                            f"✅ {date_str} の実戦記録を新規保存しました！（投資: {usr_inv:,}円 / 回収: {usr_ret:,}円 / 的中: {usr_hits}/{usr_races}R）"
                        )

                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"保存エラー: {e}")
            else:
                st.error("🚨 スプレッドシートの認証に失敗しました。")

# ==========================================
# 💻 画面 7: ターミナル操作マニュアル（前日予想コマンド搭載）
# ==========================================
elif menu == "💻 ターミナル操作マニュアル":
    st.markdown(
        '<div class="main-title">ターミナル操作マニュアル</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="last-update">各枠右上のコピーボタンを押してターミナルに貼り付けてください</div>',
        unsafe_allow_html=True,
    )

    # 🌟 新設：前日に翌日（次の日）の予想を行うコマンド
    st.markdown(
        """
    <div style="background:#141A29; border:1px solid #10B981; border-left:5px solid #10B981; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1.05rem;">🌙 0. 【前日夜・先行予想】前日に「次の日（明日）」の全レース予想を実行する</h4>
        <div style="font-size:0.88rem; color:#E2E8F0; margin-bottom:0.6rem; line-height:1.6;">
            金曜夜や土曜夜など、<b>前日のうちに出馬表から翌日の予想を一括作成</b>します。<br>
            下のコマンドは<b>自動的に「明日（翌日）」の日付を計算</b>するため、日付の書き換え不要でそのままコピペ実行できます。<br>
            ※実行完了後、左メニュー<b>「📝 レジまぐ投稿内容」</b>に翌日の日付と勝負レースが自動反映されます。
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.code(
        'cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 run.py $(date -d "tomorrow" +%Y%m%d)',
        language="bash",
    )
    st.markdown(
        """
        <div style="font-size:0.85rem; color:#CBD5E1; margin-top:0.6rem; margin-bottom:0.3rem;">
            <b>▼ 日付を直接指定して前日予想する場合（例：2026年10月18日分を予想）</b>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(
        "cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 run.py 20261018",
        language="bash",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1rem;">⚡ 1. 当日朝の予想実行（本日分の全レース巡回 ＆ ハイブリッド買い目選定）</h4>
    """,
        unsafe_allow_html=True,
    )
    st.code(
        "cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 run.py",
        language="bash",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1rem;">🎯 2. 【1レースピンポイント分析】URL不要（当日・翌日対応）</h4>
    """,
        unsafe_allow_html=True,
    )
    st.code(
        "cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 check.py 東京 11",
        language="bash",
    )
    st.markdown(
        '<div style="font-size:0.85rem; color:#CBD5E1; margin-top:0.4rem; margin-bottom:0.2rem;">▼ 前日に翌日（明日）の1レースだけをピンポイント分析する場合</div>',
        unsafe_allow_html=True,
    )
    st.code(
        'cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 check.py 東京 11 $(date -d "tomorrow" +%Y%m%d)',
        language="bash",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div style="background:#141A29; border:1px solid #6366F1; border-left:5px solid #6366F1; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1.05rem;">👑 3. G1専用 4馬場シミュレーション単体実行</h4>
        <div style="font-size:0.88rem; color:#E2E8F0; margin-bottom:0.8rem; line-height:1.6;">
            枠順確定後（金曜夕方〜土曜）、全4馬場（良・稍重・重・不良）の最適買い目を算出し「👑 G1専用予想」へ保存します。
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.code(
        "cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 g1.py 20261018 京都 11",
        language="bash",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1rem;">🏁 4. 【手動結果回収】ハイブリッド的中照合 ＆ 日次収支自動集計</h4>
    """,
        unsafe_allow_html=True,
    )
    st.code(
        "cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 result.py",
        language="bash",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1rem;">⏰ 5. 自動タイマーの実行ログ確認</h4>
    """,
        unsafe_allow_html=True,
    )
    st.code("cat /home/ozdnyzww1/keiba_cron.log", language="bash")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1rem;">🧹 6. メモリ解放 ＆ 停止コマンド（緊急用）</h4>
    """,
        unsafe_allow_html=True,
    )
    st.code(
        "killall -9 chromium chromium-driver chromedriver chrome 2>/dev/null",
        language="bash",
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🗄️ 画面 8: 過去データ分析（最新ハイブリッド確定実績）
# ==========================================
elif menu == "🗄️ 過去データ分析":
    st.markdown(
        '<div class="main-title">過去データバックテスト分析（2022〜2026年・5年間検証）</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="last-update">新馬戦完全除外 ＆ 芝・ダート極選ゾーンに絞り込んだ【確定】運用実績</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="overflow-x: auto; border-radius: 8px; border: 1px solid #1E273D; margin-top: 1rem;">
        <table style="width:100%; border-collapse: collapse; color: #F3F4F6; background-color: #141A29; font-size: 0.95rem;">
            <thead>
                <tr style="background-color: #0E1322; color: #94A3B8; border-bottom: 2px solid #1E273D; text-align: left;">
                    <th style="padding: 12px 14px; font-weight: 600;">モデル / 対象</th>
                    <th style="padding: 12px 14px; font-weight: 600;">厳選勝負ルール</th>
                    <th style="padding: 12px 14px; font-weight: 600;">推奨買い目</th>
                    <th style="padding: 12px 14px; font-weight: 600;">期待値・バックテスト実績</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #1E273D; vertical-align: top;">
                    <td style="padding: 14px; font-weight: 700; white-space: nowrap;">🟢 芝コース</td>
                    <td style="padding: 14px; line-height: 1.6;"><b>先行力（前走4角5番手以内）＋ 前走上がり3F上位</b><br><span style="font-weight:700;">※同型激突（先行4頭以上）・新馬戦除外</span></td>
                    <td style="padding: 14px; line-height: 1.6;">👑 ハイブリッド（計800円）<br><span style="color: #94A3B8;">ワイド5点 (500円) ＋ 馬単3点 (300円)</span></td>
                    <td style="padding: 14px; line-height: 1.6;">好位抜け出し・速い上がりを持つ実力馬を厳選</td>
                </tr>
                <tr style="border-bottom: 1px solid #1E273D; vertical-align: top;">
                    <td style="padding: 14px; font-weight: 700; white-space: nowrap;">🟤 ダートコース</td>
                    <td style="padding: 14px; line-height: 1.6;"><b>特注血統（米国系）× 外枠40%以上 × 先行力</b><br>（砂被りリスクを排除した外枠先行馬）</td>
                    <td style="padding: 14px; line-height: 1.6;">👑 ハイブリッド（計800円）<br><span style="color: #94A3B8;">ワイド5点 (500円) ＋ 馬単3点 (300円)</span></td>
                    <td style="padding: 14px; line-height: 1.6;">物理的に有利な外枠×ダート血統で高回収を実現</td>
                </tr>
                <tr style="vertical-align: top;">
                    <td style="padding: 14px; font-weight: 700; white-space: nowrap;">🌐 モデルB・極選総合</td>
                    <td style="padding: 14px; font-weight: 700; line-height: 1.6;">上記物理バイアス ＋ スコアギャップ3.2pt以上（1強厳選）</td>
                    <td style="padding: 14px; font-weight: 700; line-height: 1.6;">👑 ハイブリッド投資<br>（ワイド5点＋馬単3点 / 計800円）</td>
                    <td style="padding: 14px; font-weight: 700; line-height: 1.6;">5年通算回収率 <span style="color:#6366F1; font-size:1.15rem; font-weight:800;">127.5%</span> ｜ 的中率 38.7%<br><span style="color: #10B981; font-weight:800;">5年連続年間プラス収支 (+584,539円)</span>（1日平均5.4鞍）</td>
                </tr>
            </tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# 📈 画面 9: スプレッドシート連携
# ==========================================
elif menu == "📈 スプレッドシート連携":
    st.markdown(
        '<div class="main-title">Google スプレッドシート連携ステータス</div>',
        unsafe_allow_html=True,
    )
    gc = get_gspread_client()
    if gc:
        st.success(
            f"🔐 連携成功: 「{SS_NAME}」と正常にリアルタイム同期しています。"
        )
        if df_target is not None and not df_target.empty:
            st.write("▼ 最新の取得データ一覧（本日勝負レース）")
            st.dataframe(df_target, use_container_width=True)
    else:
        st.error("🚨 スプレッドシートに接続できませんでした。")
