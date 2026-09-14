import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ページ基本設定
st.set_page_config(
    page_title="Keiba AI Core",
    page_icon="🐴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🎨 画像デザイン完全再現用カスタムCSS
# ==========================================
st.markdown("""
<style>
    /* 全体背景とフォント */
    .stApp {
        background-color: #0B0F19;
        color: #F3F4F6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* サイドバーのスタイル */
    [data-testid="stSidebar"] {
        background-color: #0E1322 !important;
        border-right: 1px solid #1E2640;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    /* サイドバーのロゴ */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF;
        padding: 0 0.5rem 1.5rem 0.5rem;
    }
    .sidebar-logo span {
        font-size: 1.6rem;
    }

    /* サイドバーのナビゲーションアイテム */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        border-radius: 8px;
        color: #94A3B8;
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 4px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .nav-item.active {
        background-color: #1E2238;
        color: #FFFFFF;
        font-weight: 600;
        border-left: 3px solid #6366F1;
    }
    .nav-item:hover {
        background-color: #161C2E;
        color: #E2E8F0;
    }

    /* ユーザープロファイル（左下） */
    .sidebar-user {
        position: fixed;
        bottom: 20px;
        left: 16px;
        width: 250px;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        background-color: transparent;
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
        font-size: 0.9rem;
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
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1.8rem;
    }
    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .last-update {
        font-size: 0.85rem;
        color: #94A3B8;
    }

    /* KPIカード共通スタイル（グラデーション装飾付き） */
    .kpi-card {
        background: #141A29;
        border: 1px solid #1E273D;
        border-radius: 16px;
        padding: 1.4rem 1.5rem;
        position: relative;
        overflow: hidden;
        min-height: 130px;
    }
    /* カード右上の丸い発光グラデーション */
    .kpi-card::after {
        content: "";
        position: absolute;
        top: -30px;
        right: -30px;
        width: 90px;
        height: 90px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(20, 26, 41, 0) 70%);
        border-radius: 50%;
    }
    .kpi-title {
        font-size: 0.82rem;
        color: #94A3B8;
        font-weight: 500;
        margin-bottom: 0.6rem;
    }
    .kpi-value-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .kpi-value {
        font-size: 1.95rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.5px;
    }
    .kpi-sub {
        font-size: 1.05rem;
        color: #94A3B8;
        font-weight: 500;
    }
    .kpi-diff-green {
        font-size: 0.85rem;
        color: #10B981;
        font-weight: 600;
    }
    .kpi-diff-red {
        font-size: 0.85rem;
        color: #EF4444;
        font-weight: 600;
    }

    /* チャートコンテナ */
    .chart-container {
        background: #141A29;
        border: 1px solid #1E273D;
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1.5rem;
    }
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .chart-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF;
    }

    /* ボタンカスタマイズ */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.55rem 1.1rem;
        transition: all 0.2s;
    }
    /* データ更新ボタン */
    .btn-update > div.stButton > button {
        background-color: #161D2E;
        color: #E2E8F0;
        border: 1px solid #2B354F;
    }
    .btn-update > div.stButton > button:hover {
        background-color: #1E273D;
        border-color: #475569;
        color: #FFFFFF;
    }
    /* 半自動運用ボタン */
    .btn-auto > div.stButton > button {
        background-color: #4F46E5;
        color: #FFFFFF;
        border: none;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
    }
    .btn-auto > div.stButton > button:hover {
        background-color: #4338CA;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🗂️ サイドバー（左メニュー）
# ==========================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <span>🐴</span> Keiba AI Core
    </div>
    <div class="nav-item active">📊 ダッシュボード</div>
    <div class="nav-item">📑 本日のレース予測</div>
    <div class="nav-item">🗄️ 過去データ分析</div>
    <div class="nav-item">🎛️ AIモデル設定(RL/CL)</div>
    <div class="nav-item">📈 スプレッドシート連携</div>
    """, unsafe_allow_html=True)

    # Chromebookステータスバッジ
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
# 🚀 メインコンテンツ
# ==========================================

# 1. ヘッダーエリア
col_h_left, col_h_right1, col_h_right2 = st.columns([6, 1.3, 1.6])

with col_h_left:
    st.markdown("""
    <div class="main-title">回収率・期待値ダッシュボード</div>
    <div class="last-update">最終更新: 2026年9月14日 22:30 (自動取得完了)</div>
    """, unsafe_allow_html=True)

with col_h_right1:
    st.markdown('<div class="btn-update">', unsafe_allow_html=True)
    if st.button("🔄 データ更新", use_container_width=True):
        st.toast("スプレッドシートから最新データを同期しました！")
    st.markdown('</div>', unsafe_allow_html=True)

with col_h_right2:
    st.markdown('<div class="btn-auto">', unsafe_allow_html=True)
    if st.button("🤖 半自動運用 ON", use_container_width=True):
        st.toast("週末の自動予想・配信モードが有効です。")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")  # 余白調整

# 2. 4枚のKPIカード
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-title">AI全買い 回収率 (今月)</div>
        <div class="kpi-value-row">
            <span class="kpi-value">115.4</span><span class="kpi-sub">%</span>
            <span class="kpi-diff-green">↑ +5.2%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-title">実際の購入 回収率 (今月)</div>
        <div class="kpi-value-row">
            <span class="kpi-value">92.8</span><span class="kpi-sub">%</span>
            <span class="kpi-diff-red">↓ -2.1%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-title">本日 期待値1.0超え (発見数)</div>
        <div class="kpi-value-row">
            <span class="kpi-value">8</span><span class="kpi-sub">頭 / 36R中</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-title">AIシミュレーション利益</div>
        <div class="kpi-value-row">
            <span class="kpi-value">+18,500</span><span class="kpi-sub">円</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 3. 回収率推移チャート（Plotlyで完全再現）
col_chart_title, col_chart_select = st.columns([7, 2])
with col_chart_title:
    st.markdown('<div class="chart-title">回収率推移（実績 vs AI予測）</div>', unsafe_allow_html=True)
with col_chart_select:
    period = st.selectbox("", ["直近10日間", "直近30日間", "今年度全期間"], label_visibility="collapsed")

# グラフデータ（画像の曲線とポイントを忠実に再現）
dates = [f"9/{i}" for i in range(5, 15)]
ai_roi = [108.0, 109.5, 115.0, 111.0, 114.5, 120.5, 118.0, 122.5, 115.4, 128.7]
actual_roi = [95.0, 94.0, 98.5, 96.0, 95.0, 97.5, 94.0, 96.5, 92.8, 98.2]

fig = go.Figure()

# AI全買いの曲線（パープルのグラデーションと滑らかなスプライン）
fig.add_trace(go.Scatter(
    x=dates,
    y=ai_roi,
    name="AI判定通り全買い (期待値1.0超)",
    mode="lines+markers",
    line=dict(color="#6366F1", width=3, shape="spline"),
    marker=dict(size=7, color="#6366F1", line=dict(color="#FFFFFF", width=1.5)),
    hoverinfo="x+y"
))

# 実際の購入の曲線（必要に応じてトグル表示）
fig.add_trace(go.Scatter(
    x=dates,
    y=actual_roi,
    name="自分の実際の購入",
    mode="lines+markers",
    line=dict(color="#94A3B8", width=2, dash="dot", shape="spline"),
    marker=dict(size=5, color="#94A3B8"),
    visible="legendonly"  # デフォルトは非表示（凡例クリックで表示可能）
))

# グラフレイアウト（完全ダークネイビー仕様）
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
    xaxis=dict(
        showgrid=True,
        gridcolor="#1E273D",
        zeroline=False,
        showline=False
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#1E273D",
        zeroline=False,
        ticksuffix="%",
        range=[105, 135]
    ),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
