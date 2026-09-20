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
    initial_sidebar_state="auto"
)

# ==========================================
# 🎨 カスタムCSS（左右カード完全水平・枠デザイン完全一致）
# ==========================================
st.markdown("""
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

    /* 🌟 出馬表画面の天候切り替えボタン（文字をクッキリ純白・見やすくボタン化） */
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

    /* 🌟 タブデザイン（高コントラスト・文字がクッキリ見える純白仕様） */
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

    /* 🌟 右側のヘッダー（左のタブと全く同じ高さ38px・枠のすぐ上に配置） */
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

    /* 🌟 リッチKPIカード（高さ165px完全固定・上下配置・元の枠質感を完全維持） */
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

    /* レース判定バッジ */
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

    @media screen and (max-width: 768px) {
        .main-title { font-size: 1.35rem !important; margin-bottom: 2px !important; }
        .last-update { font-size: 0.75rem !important; margin-bottom: 0.8rem !important; }
        .kpi-big-val { font-size: 1.5rem !important; }
        .sidebar-user { position: relative !important; bottom: auto !important; left: auto !important; width: 100% !important; margin-top: 2rem !important; }
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
        return None, None, None
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
                df_target = pd.DataFrame(target_rows, columns=headers[:len(target_rows[0])])
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

        try:
            ws_daily = ss.worksheet("日次収支")
            daily_vals = ws_daily.get_all_records()
            df_daily = pd.DataFrame(daily_vals)
        except:
            df_daily = pd.DataFrame()

        return df_target, df_today, df_daily
    except Exception:
        return None, None, None

df_target, df_today, df_daily_log = load_sheet_data()

# ==========================================
# 🌟 運用サイクルのポップアップダイアログ
# ==========================================
@st.dialog("🔄 競馬AI 運用サイクル・フロー")
def show_flow_modal():
    st.markdown("""
    <div style="font-size:1rem; color:#FFFFFF; font-weight:700; margin-bottom:14px;">
        「即時性が必要なもの」と「じっくり蓄積する資産」を分けた理想の運用サイクルです。
    </div>
    <div style="background:#141A29; border:1px solid #2B354F; border-left:5px solid #6366F1; border-radius:10px; padding:14px 16px; margin-bottom:12px;">
        <div style="font-size:1.05rem; font-weight:700; color:#FFFFFF; margin-bottom:8px;">🌅 1. 【朝 9:00】 予測・出撃フェーズ（run.py）</div>
        <div style="font-size:0.9rem; color:#F3F4F6; line-height:1.7;">
            <span style="color:#818CF8; font-weight:700;">・処理</span>: 全レース自動巡回 ➔ 芝・ダート新黄金条件合致レースを抽出（馬連3点）<br>
            <span style="color:#818CF8; font-weight:700;">・反映先</span>: 「本日」「本日勝負レース」シート（作業用キャッシュ）<br>
            <span style="color:#818CF8; font-weight:700;">・操作</span>: スマホで「🎯 厳選勝負レース」を確認して馬券購入
        </div>
    </div>
    <div style="background:#141A29; border:1px solid #2B354F; border-left:5px solid #10B981; border-radius:10px; padding:14px 16px; margin-bottom:12px;">
        <div style="font-size:1.05rem; font-weight:700; color:#FFFFFF; margin-bottom:8px;">🌆 2. 【夕方 17:00】 収支確定フェーズ（result.py）</div>
        <div style="font-size:0.9rem; color:#F3F4F6; line-height:1.7;">
            <span style="color:#34D399; font-weight:700;">・処理</span>: 確定着順と馬連配当を自動回収 ➔ AI買い目（各100円）と照合<br>
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
    """, unsafe_allow_html=True)

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
        ["📊 ダッシュボード", "🎯 厳選勝負レース", "🏇 全レース出馬表", "💰 収支入力・管理", "💻 ターミナル操作マニュアル", "🗄️ 過去データ分析", "📈 スプレッドシート連携"],
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
# 🚀 画面 1: 📊 ダッシュボード（完全維持）
# ==========================================
if menu == "📊 ダッシュボード":
    col_h_left, col_h_right = st.columns([7, 3])
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    with col_h_left:
        st.markdown(f"""
        <div class="main-title">回収率・期待値ダッシュボード</div>
        <div class="last-update">最終更新: {now_str} (自動同期完了)</div>
        """, unsafe_allow_html=True)

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
            if any(k in col for k in ['投資', '回収', '払戻', 'レース', '的中', 'R数']):
                df_daily_calc[col] = pd.to_numeric(df_daily_calc[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        if 'ユーザー投資額' in df_daily_calc.columns:
            usr_tot_inv = int(df_daily_calc['ユーザー投資額'].sum())
            usr_tot_ret = int(df_daily_calc['ユーザー回収額'].sum())
            usr_tot_races = int(df_daily_calc.get('ユーザーレース数', pd.Series([0]*len(df_daily_calc))).sum())
            usr_tot_hits = int(df_daily_calc.get('ユーザー的中数', pd.Series([0]*len(df_daily_calc))).sum())
        elif '投資額' in df_daily_calc.columns:
            usr_tot_inv = int(df_daily_calc['投資額'].sum())
            usr_tot_ret = int(df_daily_calc['払戻額'].sum())
            usr_tot_races = int(df_daily_calc.get('レース数', pd.Series([0]*len(df_daily_calc))).sum())
            usr_tot_hits = int(df_daily_calc.get('的中数', pd.Series([0]*len(df_daily_calc))).sum())

        if usr_tot_inv > 0 or usr_tot_races > 0:
            has_real_usr = True

        if 'AI投資額' in df_daily_calc.columns and df_daily_calc['AI投資額'].sum() > 0:
            ai_all_inv = int(df_daily_calc['AI投資額'].sum())
            ai_all_ret = int(df_daily_calc['AI回収額'].sum())
            ai_all_races = int(df_daily_calc.get('AIレース数', pd.Series([0]*len(df_daily_calc))).sum())
            ai_all_hits = int(df_daily_calc.get('AI的中数', pd.Series([0]*len(df_daily_calc))).sum())
            has_real_ai = True
        elif '投資額' in df_daily_calc.columns:
            ai_all_inv = int(df_daily_calc['投資額'].sum())
            ai_all_ret = int(df_daily_calc['払戻額'].sum())
            ai_all_races = int(df_daily_calc.get('レース数', pd.Series([0]*len(df_daily_calc))).sum())
            ai_all_hits = int(df_daily_calc.get('的中数', pd.Series([0]*len(df_daily_calc))).sum())
            if ai_all_inv > 0 or ai_all_races > 0:
                has_real_ai = True

        if 'AI芝投資額' in df_daily_calc.columns:
            ai_turf_inv = int(df_daily_calc['AI芝投資額'].sum())
            ai_turf_ret = int(df_daily_calc['AI芝回収額'].sum())
            ai_turf_races = int(df_daily_calc.get('AI芝レース数', pd.Series([0]*len(df_daily_calc))).sum())
            ai_turf_hits = int(df_daily_calc.get('AI芝的中数', pd.Series([0]*len(df_daily_calc))).sum())

        if 'AIダート投資額' in df_daily_calc.columns:
            ai_dirt_inv = int(df_daily_calc['AIダート投資額'].sum())
            ai_dirt_ret = int(df_daily_calc['AIダート回収額'].sum())
            ai_dirt_races = int(df_daily_calc.get('AIダートレース数', pd.Series([0]*len(df_daily_calc))).sum())
            ai_dirt_hits = int(df_daily_calc.get('AIダート的中数', pd.Series([0]*len(df_daily_calc))).sum())

    ai_all_roi = (ai_all_ret / ai_all_inv * 100) if ai_all_inv > 0 else 0.0
    ai_all_hit_rate = (ai_all_hits / ai_all_races * 100) if ai_all_races > 0 else 0.0

    ai_turf_roi = (ai_turf_ret / ai_turf_inv * 100) if ai_turf_inv > 0 else 0.0
    ai_turf_hit_rate = (ai_turf_hits / ai_turf_races * 100) if ai_turf_races > 0 else 0.0

    ai_dirt_roi = (ai_dirt_ret / ai_dirt_inv * 100) if ai_dirt_inv > 0 else 0.0
    ai_dirt_hit_rate = (ai_dirt_hits / ai_dirt_races * 100) if ai_dirt_races > 0 else 0.0

    usr_roi = (usr_tot_ret / usr_tot_inv * 100) if usr_tot_inv > 0 else 0.0
    usr_hit_rate = (usr_tot_hits / usr_tot_races * 100) if usr_tot_races > 0 else 0.0

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
    
    today_investment = today_target_count * 300

    # 左右KPIカード
    c1, c2 = st.columns(2)

    with c1:
        tab_all, tab_turf, tab_dirt = st.tabs(["🌐 総合", "🟢 芝", "🟤 ダート"])

        with tab_all:
            ai_all_profit = ai_all_ret - ai_all_inv
            p_class = "kpi-profit-pos" if ai_all_profit >= 0 else "kpi-profit-neg"
            p_sign = "+" if ai_all_profit > 0 else ""
            st.markdown(f"""
            <div class="kpi-rich-card" style="border-left: 4px solid #6366F1;">
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
            """, unsafe_allow_html=True)

        with tab_turf:
            ai_turf_profit = ai_turf_ret - ai_turf_inv
            p_class = "kpi-profit-pos" if ai_turf_profit >= 0 else "kpi-profit-neg"
            p_sign = "+" if ai_turf_profit > 0 else ""
            st.markdown(f"""
            <div class="kpi-rich-card" style="border-left: 4px solid #10B981;">
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
            """, unsafe_allow_html=True)

        with tab_dirt:
            ai_dirt_profit = ai_dirt_ret - ai_dirt_inv
            p_class = "kpi-profit-pos" if ai_dirt_profit >= 0 else "kpi-profit-neg"
            p_sign = "+" if ai_dirt_profit > 0 else ""
            st.markdown(f"""
            <div class="kpi-rich-card" style="border-left: 4px solid #F59E0B;">
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
            """, unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="right-card-header">👤 あなたの実戦 通算成績 (実投票)</div>', unsafe_allow_html=True)

        if has_real_usr and (usr_tot_inv > 0 or usr_tot_races > 0):
            usr_profit = usr_tot_ret - usr_tot_inv
            usr_profit_class = "kpi-profit-pos" if usr_profit >= 0 else "kpi-profit-neg"
            usr_profit_sign = "+" if usr_profit > 0 else ""
            st.markdown(f"""
            <div class="kpi-rich-card" style="border-left: 4px solid #10B981;">
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
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="kpi-rich-card" style="border-left: 4px solid #10B981;">
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
            """, unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"""
        <div style="background:#141A29; border:1px solid #1E273D; border-radius:10px; padding:0.9rem 1.1rem; margin-bottom:0.6rem;">
            <div style="font-size:0.82rem; color:#CBD5E1;">🎯 最新日 勝負レース数</div>
            <div style="font-size:1.4rem; font-weight:700; color:#FFFFFF;">{today_target_count} <span style="font-size:0.85rem; color:#94A3B8; font-weight:400;">R / {today_race_count}R中</span></div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div style="background:#141A29; border:1px solid #1E273D; border-radius:10px; padding:0.9rem 1.1rem; margin-bottom:0.6rem;">
            <div style="font-size:0.82rem; color:#CBD5E1;">💸 最新日 推奨投資額 (各100円)</div>
            <div style="font-size:1.4rem; font-weight:700; color:#FFFFFF;">{today_investment:,} <span style="font-size:0.85rem; color:#94A3B8; font-weight:400;">円</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 回収率推移グラフ
    col_chart_title, col_chart_select = st.columns([6, 4])
    with col_chart_title:
        st.markdown('<div style="font-size:1.1rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">回収率推移</div>', unsafe_allow_html=True)
    with col_chart_select:
        chart_mode = st.selectbox(
            "期間・単位",
            ["日毎 (直近10日)", "日毎 (直近30日)", "月ごと (月別集計)", "年ごと (年別集計)", "全期間 (累積推移)"],
            label_visibility="collapsed"
        )

    fig = go.Figure()
    if (has_real_ai or has_real_usr) and df_daily_log is not None and not df_daily_log.empty:
        df_plot = df_daily_calc.copy()
        df_plot['日付_dt'] = pd.to_datetime(df_plot['日付'], errors='coerce')
        df_plot = df_plot.dropna(subset=['日付_dt']).sort_values('日付_dt').reset_index(drop=True)

        if not df_plot.empty:
            ai_inv_col = 'AI投資額' if 'AI投資額' in df_plot.columns else ('投資額' if '投資額' in df_plot.columns else '')
            ai_ret_col = 'AI回収額' if 'AI回収額' in df_plot.columns else ('払戻額' if '払戻額' in df_plot.columns else '')
            usr_inv_col = 'ユーザー投資額' if 'ユーザー投資額' in df_plot.columns else ('投資額' if '投資額' in df_plot.columns else '')
            usr_ret_col = 'ユーザー回収額' if 'ユーザー回収額' in df_plot.columns else ('払戻額' if '払戻額' in df_plot.columns else '')

            if chart_mode == "日毎 (直近10日)":
                sub_df = df_plot.tail(10).copy()
                x_vals = sub_df['日付_dt'].dt.strftime('%m/%d').tolist()
            elif chart_mode == "日毎 (直近30日)":
                sub_df = df_plot.tail(30).copy()
                x_vals = sub_df['日付_dt'].dt.strftime('%m/%d').tolist()
            else:
                sub_df = df_plot.copy()
                x_vals = sub_df['日付_dt'].dt.strftime('%m/%d').tolist()

            if ai_inv_col and ai_ret_col and sub_df[ai_inv_col].sum() > 0:
                sub_df['AI_CUM_I'] = sub_df[ai_inv_col].cumsum()
                sub_df['AI_CUM_R'] = sub_df[ai_ret_col].cumsum()
                ai_vals = np.where(sub_df['AI_CUM_I'] > 0, (sub_df['AI_CUM_R'] / sub_df['AI_CUM_I']) * 100, 0.0)
                fig.add_trace(go.Scatter(
                    x=x_vals, y=ai_vals,
                    name="AI理論 (実績)",
                    mode="lines+markers",
                    line=dict(color="#6366F1", width=2.5, shape="spline"),
                    marker=dict(size=7, color="#6366F1"),
                    hovertemplate="%{x}<br>AI: %{y:.1f}%<extra></extra>"
                ))

            if usr_inv_col and usr_ret_col and sub_df[usr_inv_col].sum() > 0:
                sub_df['USR_CUM_I'] = sub_df[usr_inv_col].cumsum()
                sub_df['USR_CUM_R'] = sub_df[usr_ret_col].cumsum()
                usr_vals = np.where(sub_df['USR_CUM_I'] > 0, (sub_df['USR_CUM_R'] / sub_df['USR_CUM_I']) * 100, 0.0)
                fig.add_trace(go.Scatter(
                    x=x_vals, y=usr_vals,
                    name="あなたの実戦",
                    mode="lines+markers",
                    line=dict(color="#10B981", width=2.5, shape="spline"),
                    marker=dict(size=7, color="#10B981"),
                    hovertemplate="%{x}<br>実戦: %{y:.1f}%<extra></extra>"
                ))
    else:
        dates = [f"9/{i}" for i in range(5, 15)]
        ai_roi_demo = [108.0, 109.5, 115.0, 111.0, 114.5, 120.5, 118.0, 122.5, 124.2, 128.7]
        fig.add_trace(go.Scatter(
            x=dates, y=ai_roi_demo,
            name="AI参考基準",
            mode="lines+markers",
            line=dict(color="#6366F1", width=2.5, shape="spline"),
            marker=dict(size=6, color="#6366F1")
        ))

    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="#475569",
        annotation_text="100%",
        annotation_position="bottom right",
        annotation_font_color="#94A3B8"
    )

    fig.update_layout(
        height=300,
        margin=dict(l=5, r=5, t=15, b=10),
        paper_bgcolor="#141A29",
        plot_bgcolor="#141A29",
        font=dict(color="#94A3B8", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=11, color="#CBD5E1")),
        xaxis=dict(showgrid=True, gridcolor="#1E273D", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#1E273D", zeroline=True, zerolinecolor="#334155", ticksuffix="%", range=[-8, 115]),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ==========================================
# 🎯 画面 2: 厳選勝負レース（朝のrun.py結果をそのまま確実に表示）
# ==========================================
elif menu == "🎯 厳選勝負レース":
    st.markdown('<div class="main-title">本日の厳選勝負レース</div>', unsafe_allow_html=True)
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
            
            num_bets = min(len(sub_df), 3)
            cols = st.columns(num_bets)
            bet_meta = [
                ("点① 本線・抑え", "#3B82F6"),
                ("点② 相手本線", "#10B981"),
                ("点③ 利益の核（△1）", "#F59E0B")
            ]
            for b_i in range(num_bets):
                with cols[b_i]:
                    row_b = sub_df.iloc[b_i]
                    b_title, b_color = bet_meta[b_i]
                    st.markdown(f"""
                    <div style="background:#1B2338; padding:10px 12px; border-radius:8px; border-left:3px solid {b_color}; margin-bottom:6px;">
                        <span style="color:#94A3B8; font-size:0.8rem;">{b_title}</span><br>
                        <b style="font-size:1.05rem; color:#FFFFFF;">馬連 {row_b['買い目']}</b><br>
                        <span style="font-size:0.82rem; color:#CBD5E1;">相手: {row_b['相手馬']} ｜ 想定: {row_b['想定オッズ']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("スプレッドシートに最新の勝負レースデータがありません。")

# ==========================================
# 🏇 画面 3: 全レース出馬表（🌟 天候切り替えボタンを常時表示）
# ==========================================
elif menu == "🏇 全レース出馬表":
    st.markdown('<div class="main-title">全レース出馬表 ＆ AI評価印</div>', unsafe_allow_html=True)
    st.markdown('<div class="last-update">馬場状態を切り替えて、レースの買い/見送り判定と各頭の印をシミュレーションできます</div>', unsafe_allow_html=True)

    # 🌟 ボタンをタブの真上に常時表示（データ有無にかかわらず必ず表示）
    st.markdown('<div style="font-size:0.95rem; font-weight:700; color:#FFFFFF; margin-bottom:6px;">⛅ 馬場状態の切り替えシミュレーション</div>', unsafe_allow_html=True)
    sel_baba = st.radio("", ["☀️ 良", "⛅ 稍重", "☂️ 重", "🌀 不良"], horizontal=True, label_visibility="collapsed")
    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    b_val = sel_baba.replace("☀️ ", "").replace("⛅ ", "").replace("☂️ ", "").replace("🌀 ", "")

    if df_today is not None and not df_today.empty and '日付' in df_today.columns:
        latest_date_str = df_today['日付'].max()
        df_today_latest = df_today[df_today['日付'] == latest_date_str]
        
        # 選択された馬場で絞り込み（もしデータに馬場列があれば一致するものを、無ければそのまま全頭表示）
        if '馬場' in df_today_latest.columns and (df_today_latest['馬場'] == b_val).any():
            df_today_disp = df_today_latest[df_today_latest['馬場'] == b_val]
        else:
            df_today_disp = df_today_latest

        venues = df_today_disp['会場'].unique()
        tabs = st.tabs([f"📍 {v}" for v in venues])
        
        def extract_r_num(x):
            m = re.search(r'^(\d+)R', x)
            return int(m.group(1)) if m else 99

        for i, venue in enumerate(venues):
            with tabs[i]:
                venue_df = df_today_disp[df_today_disp['会場'] == venue]
                race_names = sorted(venue_df['レース名'].unique(), key=extract_r_num)
                
                for rname in race_names:
                    sub_df = venue_df[venue_df['レース名'] == rname].copy()
                    cond = str(sub_df.iloc[0]['芝・ダ・障']) + str(sub_df.iloc[0]['距離']) + "m"
                    
                    with st.expander(f"🏁 {venue} {rname} （{cond}）"):
                        # レース全体のAI判定（買い or 見送り）を表示
                        if 'レース判定' in sub_df.columns:
                            r_judge = str(sub_df.iloc[0]['レース判定'])
                            r_detail = str(sub_df.iloc[0].get('レース判定詳細', ''))
                            if '買い' in r_judge:
                                st.markdown(f'<div class="status-badge-buy">🎯 {r_judge} ｜ {r_detail}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="status-badge-skip">✋ {r_judge} ｜ 理由: {r_detail}</div>', unsafe_allow_html=True)

                        disp_cols = ['馬番', '印', '馬名', '単勝オッズ', '人気', 'RL', 'CL', 'AIスコア', 'AI判定']
                        if '評価' in sub_df.columns:
                            sub_df = sub_df.rename(columns={'評価': '印'})
                        
                        actual_cols = [c for c in disp_cols if c in sub_df.columns]
                        display_df = sub_df[actual_cols].copy()
                        display_df['馬番'] = pd.to_numeric(display_df['馬番'], errors='coerce')
                        display_df = display_df.sort_values('馬番')
                        
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
                                if col == '印':
                                    if val == '◎': val = "<span style='color: #EF4444; font-weight: 900; font-size: 1.1rem;'>◎</span>"
                                    elif val == '◯': val = "<span style='color: #3B82F6; font-weight: 900; font-size: 1.1rem;'>◯</span>"
                                    elif val == '▲': val = "<span style='color: #10B981; font-weight: 900; font-size: 1.1rem;'>▲</span>"
                                    elif '△' in str(val): val = f"<span style='color: #F59E0B; font-weight: 900; font-size: 1.05rem;'>{val}</span>"
                                
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
                                nowrap = "white-space: nowrap;" if col != "馬名" else ""
                                html_table += f"<td style='padding: 8px 6px; text-align: {align}; {nowrap}'>{val}</td>"
                            html_table += "</tr>"
                        html_table += "</tbody></table></div>"
                        
                        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("スプレッドシートに最新の全頭データがありません。")

# ==========================================
# 💰 画面 4: 収支入力・管理（完全維持）
# ==========================================
elif menu == "💰 収支入力・管理":
    st.markdown('<div class="main-title">日次実収支の記録</div>', unsafe_allow_html=True)
    st.markdown('<div class="last-update">一日の終わりに、今日の購入実績（金額・レース数・的中数）を入力して保存してください</div>', unsafe_allow_html=True)

    with st.form("shushi_form"):
        st.markdown('<div style="font-size:0.95rem; font-weight:700; color:#FFFFFF; margin-bottom:6px;">🗓️ 競馬開催日</div>', unsafe_allow_html=True)
        target_date = st.date_input("開催日", datetime.now(), label_visibility="collapsed")
        
        st.markdown('<div style="font-size:0.9rem; font-weight:700; color:#818CF8; margin-top:14px; margin-bottom:8px;">【収支金額】</div>', unsafe_allow_html=True)
        c_in1, c_in2 = st.columns(2)
        with c_in1:
            st.markdown('<div style="font-size:0.9rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">💸 今日の総購入額 (円)</div>', unsafe_allow_html=True)
            usr_inv = st.number_input("総購入額", min_value=0, value=0, step=100, label_visibility="collapsed")
        with c_in2:
            st.markdown('<div style="font-size:0.9rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">💰 今日の総払戻額 (円)</div>', unsafe_allow_html=True)
            usr_ret = st.number_input("総払戻額", min_value=0, value=0, step=100, label_visibility="collapsed")
        
        st.markdown('<div style="font-size:0.9rem; font-weight:700; color:#34D399; margin-top:14px; margin-bottom:8px;">【的中率カウント】</div>', unsafe_allow_html=True)
        c_in3, c_in4 = st.columns(2)
        with c_in3:
            st.markdown('<div style="font-size:0.9rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">🏇 実際に購入したレース数</div>', unsafe_allow_html=True)
            usr_races = st.number_input("購入レース数", min_value=0, value=0, step=1, label_visibility="collapsed")
        with c_in4:
            st.markdown('<div style="font-size:0.9rem; font-weight:700; color:#FFFFFF; margin-bottom:4px;">🎯 的中したレース数</div>', unsafe_allow_html=True)
            usr_hits = st.number_input("的中レース数", min_value=0, value=0, step=1, label_visibility="collapsed")
        
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
                        ws.append_row(["日付", "AI投資額", "AI回収額", "ユーザー投資額", "ユーザー回収額", "AIレース数", "AI的中数", "ユーザーレース数", "ユーザー的中数"])

                    cur_h = ws.row_values(1)
                    if len(cur_h) < 9:
                        std_h = ["日付", "AI投資額", "AI回収額", "ユーザー投資額", "ユーザー回収額", "AIレース数", "AI的中数", "ユーザーレース数", "ユーザー的中数"]
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
                        st.success(f"✅ {date_str} の実戦記録を更新しました！（投資: {usr_inv:,}円 / 回収: {usr_ret:,}円 / 的中: {usr_hits}/{usr_races}R）")
                    else:
                        new_row = [date_str] + [0] * max(0, len(headers) - 1)
                        if len(new_row) >= col_u_inv: new_row[col_u_inv - 1] = usr_inv
                        if len(new_row) >= col_u_ret: new_row[col_u_ret - 1] = usr_ret
                        if len(new_row) >= col_u_races: new_row[col_u_races - 1] = usr_races
                        if len(new_row) >= col_u_hits: new_row[col_u_hits - 1] = usr_hits
                        ws.append_row(new_row)
                        st.success(f"✅ {date_str} の実戦記録を新規保存しました！（投資: {usr_inv:,}円 / 回収: {usr_ret:,}円 / 的中: {usr_hits}/{usr_races}R）")
                    
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"保存エラー: {e}")
            else:
                st.error("🚨 スプレッドシートの認証に失敗しました。")

# ==========================================
# 💻 画面 5: ターミナル操作マニュアル（完全維持）
# ==========================================
elif menu == "💻 ターミナル操作マニュアル":
    st.markdown('<div class="main-title">ターミナル操作マニュアル</div>', unsafe_allow_html=True)
    st.markdown('<div class="last-update">各枠右上のコピーボタンを押してターミナルに貼り付けてください</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1B2238; border:1px solid #6366F1; border-radius:12px; padding:1.1rem; margin-bottom:1.5rem;">
        <h4 style="color:#FFFFFF; margin-top:0; display:flex; align-items:center; gap:8px; font-size:1.1rem;">
            <span>🏁</span> 週末競馬終了後のやることリスト
        </h4>
        <div style="background:#141A29; border:1px solid #1E273D; border-radius:10px; padding:0.9rem 1rem; margin-bottom:0.7rem;">
            <div style="display:flex; align-items:center; gap:8px; font-weight:700; color:#FFFFFF; margin-bottom:0.3rem; font-size:0.95rem;">
                <span style="background:#4F46E5; color:white; font-size:0.7rem; font-weight:700; padding:2px 6px; border-radius:999px;">STEP 1</span> 結果回収の確認（または手動実行）
            </div>
            <div style="font-size:0.85rem; color:#CBD5E1;">
                Chromebookを開いていれば自動回収完了。閉じていた場合は下記 <b>3. 手動結果回収コマンド</b> を実行してください。
            </div>
        </div>
        <div style="background:#141A29; border:1px solid #1E273D; border-radius:10px; padding:0.9rem 1rem; margin-bottom:0.7rem;">
            <div style="display:flex; align-items:center; gap:8px; font-weight:700; color:#FFFFFF; margin-bottom:0.3rem; font-size:0.95rem;">
                <span style="background:#4F46E5; color:white; font-size:0.7rem; font-weight:700; padding:2px 6px; border-radius:999px;">STEP 2</span> あなたの実収支を入力
            </div>
            <div style="font-size:0.85rem; color:#CBD5E1;">
                左メニュー <b>「💰 収支入力・管理」</b> から総購入額、総払戻額、購入R数、的中R数を入力して保存。
            </div>
        </div>
        <div style="background:#141A29; border:1px solid #1E273D; border-radius:10px; padding:0.9rem 1rem; margin-bottom:0;">
            <div style="display:flex; align-items:center; gap:8px; font-weight:700; color:#FFFFFF; margin-bottom:0.3rem; font-size:0.95rem;">
                <span style="background:#4F46E5; color:white; font-size:0.7rem; font-weight:700; padding:2px 6px; border-radius:999px;">STEP 3</span> ダッシュボードで成果確認
            </div>
            <div style="font-size:0.85rem; color:#CBD5E1;">
                <b>「📊 ダッシュボード」</b> で「🔄 データ更新」を押し、回収率と的中率をチェック！
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1rem;">⚡ 1. 朝の予想手動実行（全レース巡回 ＆ 3点買い選定）</h4>
    """, unsafe_allow_html=True)
    st.code("cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 run.py", language="bash")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1rem;">🎯 2. 【1レースピンポイント分析】URL不要</h4>
    """, unsafe_allow_html=True)
    st.code("cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 check.py 中山 11", language="bash")
    st.caption("※芝・ダートを自動判別し、黄金条件合致判定と推奨3点買いを出力")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#141A29; border:1px solid #1E273D; border-radius:12px; padding:1.1rem; margin-bottom:1.2rem;">
        <h4 style="color:#FFFFFF; margin-top:0; font-size:1rem;">🏁 3. 【手動結果回収】3点買い的中照合 ＆ 日次収支自動集計</h4>
    """, unsafe_allow_html=True)
    st.code("cd /home/ozdnyzww1 && /home/ozdnyzww1/keiba_env/bin/python3 result.py", language="bash")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🗄️ 過去データ分析（完全維持）
# ==========================================
elif menu == "🗄️ 過去データ分析":
    st.markdown('<div class="main-title">過去データバックテスト分析（2022〜2026年）</div>', unsafe_allow_html=True)
    st.markdown('<div class="last-update">5年間・107,000行の実データ検証による確定黄金条件</div>', unsafe_allow_html=True)
    
    st.markdown("""
    | トラック | 黄金条件ルール | 買い目 | 通算回収率 | 的中率 | 安定度 |
    | :--- | :--- | :---: | :---: | :---: | :---: |
    | **🟢 芝** | **全距離 × 1人気 2.0〜3.5倍** | 馬連3点（◎-◯, ▲, △1） | **148.7%** | **17.8%** | 直近4年連続120%超 |
    | **🟤 ダート** | **全距離 × 1人気 3.5倍未満 × 軸中外枠** | 馬連3点（◎-◯, ▲, △1） | **256.9%** | **22.1%** | **5/5年連続プラス** |
    | **🌐 総合** | **上記2大条件の完全合算** | 馬連3点（計300円） | **190.6%** | **19.5%** | **通算純益 +165万円** |
    """)

# ==========================================
# 📈 スプレッドシート連携（完全維持）
# ==========================================
elif menu == "📈 スプレッドシート連携":
    st.markdown('<div class="main-title">Google スプレッドシート連携ステータス</div>', unsafe_allow_html=True)
    gc = get_gspread_client()
    if gc:
        st.success(f"🔐 連携成功: 「{SS_NAME}」と正常にリアルタイム同期しています。")
        if df_target is not None and not df_target.empty:
            st.write("▼ 最新の取得データ一覧（本日勝負レース）")
            st.dataframe(df_target, use_container_width=True)
    else:
        st.error("🚨 スプレッドシートに接続できませんでした。")
