import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time
import gspread
import pandas as pd
import altair as alt
from datetime import datetime

# ==========================================
# 🔐 Googleスプレッドシート認証
# ==========================================
creds_dict = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds_dict)
ss_name = "競馬AIシステム_Core"

# セッションメモリの初期化
if 'race_history' not in st.session_state:
    st.session_state.race_history = {}

# ==========================================
# 🧠 独自AIエンジン
# ==========================================
def run_ai_core(df, track_cond):
    if df.empty or '実力順位(RL)' not in df.columns or '適正順位(CL)' not in df.columns:
        return df, False, [], [], [], [], 0, 0, 0, 0, 0.0, "#F8FAFC", "", "エラー", 0.0, 0.0
    
    df = df[df['馬番'] != ""].copy()
    if df['実力順位(RL)'].replace('', pd.NA).isna().all():
        return df, False, [], [], [], [], 0, 0, 0, 0, 0.0, "#F8FAFC", "", "データ待機", 0.0

    df['Odds'] = pd.to_numeric(df['単勝オッズ'], errors='coerce').fillna(0)
    df['RL'] = pd.to_numeric(df['実力順位(RL)'], errors='coerce').fillna(99)
    df['CL'] = pd.to_numeric(df['適正順位(CL)'], errors='coerce').fillna(99)
    
    df['AIスコア'] = (df['RL'] * 0.7) + (df['CL'] * 0.3)
    df_sorted = df.sort_values('AIスコア').reset_index()
    
    df['評価'] = ""
    df['期待値'] = 0.0
    df['判定'] = "見送り"
    max_exp, honmei_exp = 0.0, 0.0
    
    if len(df_sorted) > 0:
        sum_inv = (1.0 / df_sorted['AIスコア']).replace([float('inf')], 0).sum()
        for i, row in df_sorted.iterrows():
            idx = row['index']
            if i == 0: df.at[idx, '評価'] = '◎'
            elif i == 1: df.at[idx, '評価'] = '◯'
            elif i == 2: df.at[idx, '評価'] = '▲'
            elif i < 6: df.at[idx, '評価'] = '△'
            
            score = row['AIスコア']
            if sum_inv > 0 and score > 0:
                win_prob = (1.0 / score) / sum_inv
                exp_val = win_prob * row['Odds']
                if track_cond in ["重", "不良"]: exp_val *= 0.95
                
                df.at[idx, '期待値'] = round(exp_val, 2)
                if exp_val > max_exp: max_exp = round(exp_val, 2)
                if i == 0: honmei_exp = round(exp_val, 2)
                if exp_val >= 1.0: df.at[idx, '判定'] = '買い'
                    
    if honmei_exp >= 1.5: race_rank = "⭐⭐⭐ S (激アツ)"
    elif honmei_exp >= 1.2: race_rank = "⭐⭐ A (勝負)"
    elif honmei_exp >= 1.0: race_rank = "⭐ B (買い)"
    else: race_rank = "見送り"
                    
    honmei = df[df['評価'] == '◎']['馬番'].tolist()
    taikou = df[df['評価'] == '◯']['馬番'].tolist()
    tana = df[df['評価'] == '▲']['馬番'].tolist()
    himo = df[df['評価'] == '△']['馬番'].tolist()
    buy_count = len(df[df['判定'] == '買い'])
    
    for col in ['AI投資額', 'AI払戻金']:
        if col not in df.columns: df[col] = 0
    df['AI投資額'] = pd.to_numeric(df['AI投資額'], errors='coerce').fillna(0)
    df['AI払戻金'] = pd.to_numeric(df['AI払戻金'], errors='coerce').fillna(0)
    ai_invest = df['AI投資額'].sum()
    ai_return = df['AI払戻金'].sum()
    ai_profit = int(ai_return - ai_invest)
    ai_roi = round((ai_return / ai_invest * 100), 1) if ai_invest > 0 else 0.0
    profit_color = "#10B981" if ai_profit > 0 else ("#EF4444" if ai_profit < 0 else "#F8FAFC")
    sign = "+" if ai_profit > 0 else ""
    
    return df, True, honmei, taikou, tana, himo, buy_count, ai_invest, ai_return, ai_profit, ai_roi, profit_color, sign, race_rank, max_exp, honmei_exp

# ==========================================
# 🛠️ ブラウザ起動モジュール (CPU負荷軽減版)
# ==========================================
def get_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--disable-extensions')
    options.page_load_strategy = 'eager'
    
    try:
        from selenium.webdriver.chrome.service import Service
        service = Service('/usr/bin/chromedriver')
        options.binary_location = '/usr/bin/chromium'
        return webdriver.Chrome(service=service, options=options)
    except Exception:
        import chromedriver_autoinstaller
        chromedriver_autoinstaller.install()
        return webdriver.Chrome(options=options)

# ==========================================
# 🛠️ 1レース解析用の共通モジュール
# ==========================================
def fetch_and_analyze_single_race(race_id, driver, analysis_sheet, progress_bar, log_text, is_batch=False):
    domain = "race.netkeiba.com"
    if len(race_id) >= 12 and race_id[4:6].isdigit():
        if int(race_id[4:6]) >= 11:
            domain = "nar.netkeiba.com"

    log_text.write(f"🔍 出馬表と開催会場を解析中...")
    driver.get(f"https://{domain}/race/shutuba.html?race_id={race_id}")
    time.sleep(1.5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    if not soup.find('tr', class_=re.compile(r'HorseList', re.I)):
        domain = "nar.netkeiba.com" if domain == "race.netkeiba.com" else "race.netkeiba.com"
        driver.get(f"https://{domain}/race/shutuba.html?race_id={race_id}")
        time.sleep(1.5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

    place_code = race_id[4:6] if len(race_id) >= 12 else ""
    place_map = {"01":"札幌", "02":"函館", "03":"福島", "04":"新潟", "05":"東京", "06":"中山", "07":"中京", "08":"京都", "09":"阪神", "10":"小倉", "30":"大井", "31":"水沢", "32":"盛岡", "35":"川崎", "36":"船橋", "37":"浦和", "42":"園田", "43":"姫路", "50":"高知", "54":"佐賀", "65":"門別", "21":"名古屋", "22":"笠松", "23":"金沢"}
    place_str = place_map.get(place_code, "競馬場")
    r_num_str = str(int(race_id[10:12])) + "R" if len(race_id) >= 12 else ""

    race_name_element = soup.find(class_='RaceName')
    if race_name_element:
        pure_race_name = re.sub(r'\s+', ' ', race_name_element.text.strip())
        race_name = f"{place_str}{r_num_str} {pure_race_name}"
    else:
        race_name = f"レースID: {race_id}"
    
    race_data = soup.find(class_='RaceData01')
    track_type, distance = "", ""
    if race_data:
        match = re.search(r'(芝|ダ|障).*?(\d+)m', race_data.text)
        if match: track_type, distance = match.group(1), match.group(2)
    
    horse_links = {}
    horse_list = []
    odds_map = {} # 🌟 NEW: オッズの格納庫を先頭に準備
    
    # 【対策1】まずは「出馬表ページ」から直接オッズの取得を試みる
    for tr in soup.find_all('tr', class_=re.compile(r'HorseList', re.I)):
        td_umaban = tr.find(class_=re.compile(r'Umaban', re.I))
        td_horse = tr.find(class_=re.compile(r'HorseInfo', re.I))
        if td_umaban and td_horse:
            u_match = re.search(r'\d+', td_umaban.text)
            a_tag = td_horse.find('a', href=re.compile(r'horse/'))
            if u_match and a_tag:
                u_num = str(int(u_match.group(0)))
                name = a_tag.text.strip().replace(" ", "").replace(" ", "")
                href = a_tag.get('href')
                if name and u_num and [u_num, name] not in horse_list:
                    horse_list.append([u_num, name])
                    horse_links[name] = href
                
                # 出馬表の行の中にある「小数点の数字」をオッズと判定して拾い上げる
                for td in tr.find_all(['td', 'span']):
                    text = td.text.strip()
                    if re.match(r'^[0-9]+\.[0-9]+$', text):
                        odds_map[u_num] = text
                        break
    
    if not horse_list: 
        if domain == "race.netkeiba.com": raise Exception("馬番が未発表です（週末のレースは木・金曜に確定します）")
        else: raise Exception("出馬表の取得に失敗しました。")
    
    horse_list = sorted(horse_list, key=lambda x: int(x[0]))
    
    # 【対策2】出馬表でオッズが取れていなければ、「オッズ専用ページ」へ取りに行く
    if len(odds_map) < len(horse_list) / 2:
        log_text.write("📊 最新オッズを取得中...")
        driver.get(f"https://{domain}/odds/index.html?type=b1&race_id={race_id}")
        time.sleep(1)
        odds_soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for tr in odds_soup.find_all('tr'):
            umaban_td = tr.find(class_=re.compile(r'Umaban', re.I))
            if umaban_td:
                u_match = re.search(r'\d+', umaban_td.text)
                if u_match:
                    u_num = str(int(u_match.group(0)))
                    # 🌟 核心の修正: クラス名(Odds)に頼らず、ハイフンなしの小数点をオッズとして認識
                    for elem in tr.find_all(['td', 'span', 'div']):
                        text = elem.text.strip()
                        if '-' not in text and re.match(r'^[0-9]+\.[0-9]+$', text):
                            odds_map[u_num] = text
                            break
                            
    # 【対策3】それでもダメなら「結果ページ」（レース終了後用）から確定オッズを取る
    if len(odds_map) < len(horse_list) / 2:
        driver.get(f"https://{domain}/race/result.html?race_id={race_id}")
        time.sleep(1)
        res_soup = BeautifulSoup(driver.page_source, 'html.parser')
        result_table = res_soup.find('table', class_='RaceTable01')
        if result_table:
            headers = result_table.find_all('th')
            odds_idx, umaban_idx = -1, -1
            for i, th in enumerate(headers):
                if '単勝' in th.text: odds_idx = i
                if '馬番' in th.text: umaban_idx = i
            if odds_idx != -1 and umaban_idx != -1:
                for tr in result_table.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) > max(odds_idx, umaban_idx):
                        u_match = re.search(r'\d+', tds[umaban_idx].text.strip())
                        o_match = re.search(r'([0-9.]+)', tds[odds_idx].text.strip())
                        if u_match and o_match: odds_map[str(int(u_match.group(0)))] = o_match.group(1)
    
    total_horses = len(horse_list)
    current_idx = 0
    raw_scores = []
    
    for row in horse_list:
        u_num, umamei = row[0], row[1]
        umamei_clean = umamei.replace(" ", "").replace(" ", "")
        current_idx += 1
        
        prefix = f"[{race_name}] " if is_batch else ""
        log_text.write(f"🐎 {prefix}{u_num}番 {umamei} を分析中... ({current_idx}/{total_horses})")
        progress_bar.progress(current_idx / total_horses)
        
        avg_rank, rentai_rate = 99.0, 0.0
        if umamei_clean in horse_links:
            db_url = horse_links[umamei_clean]
            driver.get("https:" + db_url if not db_url.startswith('http') else db_url)
            time.sleep(1.0)
            db_soup = BeautifulSoup(driver.page_source, 'html.parser')
            result_table = db_soup.find('table', class_='db_h_race_results')
            if result_table:
                headers_th = result_table.find_all('th')
                rank_idx, dist_idx = -1, -1
                for idx, th in enumerate(headers_th):
                    if '着順' in th.text: rank_idx = idx
                    if '距離' in th.text: dist_idx = idx
                if rank_idx != -1:
                    rows = result_table.find('tbody').find_all('tr') if result_table.find('tbody') else result_table.find_all('tr')[1:]
                    ranks = []
                    for tr in rows:
                        cols = tr.find_all('td')
                        if len(cols) > rank_idx:
                            match = re.search(r'(\d+)', cols[rank_idx].text.strip())
                            if match:
                                ranks.append(int(match.group(1)))
                                if len(ranks) >= 3: break
                    if ranks: avg_rank = sum(ranks) / len(ranks)
                    if dist_idx != -1 and track_type and distance:
                        t_runs, t_rentai = 0, 0
                        for tr in rows:
                            cols = tr.find_all('td')
                            if len(cols) > max(rank_idx, dist_idx):
                                d_txt, r_txt = cols[dist_idx].text.strip(), cols[rank_idx].text.strip()
                                if track_type in d_txt and distance in d_txt:
                                    t_runs += 1
                                    r_m = re.search(r'(\d+)', r_txt)
                                    if r_m and int(r_m.group(1)) in [1, 2]: t_rentai += 1
                        if t_runs > 0: rentai_rate = round(t_rentai / t_runs, 3)
        
        raw_scores.append({'馬番': u_num, '馬名': umamei, '単勝オッズ': odds_map.get(u_num, "0.0"), 'avg_rank': avg_rank, 'rentai_rate': rentai_rate})
        
    score_df = pd.DataFrame(raw_scores)
    score_df['実力順位(RL)'] = score_df['avg_rank'].rank(method='min', ascending=True).astype(int)
    score_df['適正順位(CL)'] = score_df['rentai_rate'].rank(method='min', ascending=False).astype(int)
    
    final_matrix = []
    for _, r in score_df.iterrows():
        final_matrix.append([r['馬番'], r['馬名'], str(r['単勝オッズ']), str(r['実力順位(RL)']), str(r['適正順位(CL)'])])
        
    df_fresh = pd.DataFrame(final_matrix, columns=['馬番', '馬名', '単勝オッズ', '実力順位(RL)', '適正順位(CL)'])

    try:
        clear_data = [["", "", "", "", ""] for _ in range(24)]
        analysis_sheet.update(range_name='A2:E25', values=clear_data, value_input_option='USER_ENTERED')
        analysis_sheet.update(range_name=f'A2:E{1+len(final_matrix)}', values=final_matrix, value_input_option='USER_ENTERED')
    except Exception as e:
        log_text.write(f"※スプレッドシートへの記録をスキップしました: {str(e)}")
    
    _, _, honmei_list, _, _, _, _, _, _, _, _, _, _, race_rank, _, honmei_exp = run_ai_core(df_fresh, "良")
    
    st.session_state.race_history[race_id] = {
        'race_name': race_name,
        'race_rank': race_rank,
        'honmei': honmei_list,
        'honmei_exp': honmei_exp,
        'ai_decision': '買い' if race_rank != "見送り" else '見送り',
        'df_raw': df_fresh
    }

# ==========================================
# 🎨 ページ設定とカスタムCSS
# ==========================================
st.set_page_config(page_title="Keiba AI Core", page_icon="🐴", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .kpi-card { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #334155; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .kpi-title { color: #94A3B8; font-size: 0.9rem; margin-bottom: 8px; }
    .kpi-value { font-size: 2.2rem; font-weight: 700; margin: 0; }
    .stButton>button { font-weight: 600; transition: all 0.3s ease; }
    .main-header { font-size: 1.8rem; font-weight: 700; margin-bottom: 0; }
    .sub-header { color: #94A3B8; font-size: 0.9rem; margin-bottom: 20px; }
    .ticket-card { background-color: #1E293B; border-left: 4px solid #10B981; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .streamlit-expanderHeader { font-size: 1.1rem; font-weight: 600; background-color: #1E293B; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h2 style='color: white; margin-bottom: 30px;'>🐴 Keiba AI Core</h2>", unsafe_allow_html=True)
    menu = st.radio("", ["ダッシュボード", "レース予測・自動実行"], label_visibility="collapsed")
    st.markdown("<div style='margin-top: 50vh;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='border-top: 1px solid #334155; padding-top: 20px; display: flex; align-items: center;'>
        <div style='background-color: #8B5CF6; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; margin-right: 12px;'>U</div>
        <div>
            <div style='font-weight: bold; font-size: 0.9rem;'>User (Cloud Hosted)</div>
            <div style='color: #10B981; font-size: 0.75rem;'>● システム稼働中</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 📊 メイン画面：ダッシュボード
# ==========================================
if menu == "ダッシュボード":
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("<p class='main-header'>回収率・期待値ダッシュボード</p>", unsafe_allow_html=True)
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        st.markdown(f"<p class='sub-header'>最終更新: {now}</p>", unsafe_allow_html=True)
    with col2:
        if st.button("↻ データ更新", use_container_width=True): st.rerun()
    with col3:
        st.button("🤖 半自動運用 ON", use_container_width=True)

    st.markdown("### 🌦️ 馬場状態のリアルタイム補正")
    track_cond = st.radio("実際の馬場状態を選択すると、荒れ具合を加味して期待値が変動します", ["良", "稍重", "重", "不良"], horizontal=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    st.markdown("### 🏆 本日の勝負レース一覧 (クリックで詳細を展開)")
    if st.session_state.race_history:
        for r_id, r_data in st.session_state.race_history.items():
            df_calc, has_valid_data, honmei, taikou, tana, himo, buy_count, ai_invest, ai_return, ai_profit, ai_roi, profit_color, sign, race_rank, max_exp, honmei_exp = run_ai_core(r_data['df_raw'], track_cond)
            
            honmei_str = f"{honmei[0]}番" if honmei else "なし"
            icon = "🎯" if r_data['ai_decision'] == '買い' else "💤"
            
            expander_title = f"{icon} {r_data['race_name']} ｜ 判定: {r_data['ai_decision']} ｜ {race_rank} ｜ ◎本命: {honmei_str} ｜ 期待値: {honmei_exp:.2f}"
            
            with st.expander(expander_title, expanded=False):
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                with kpi1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">AI判定 (買い指定)</div><div class="kpi-value">{buy_count}<span style="font-size:1.2rem; color:#94A3B8;">頭</span></div></div>', unsafe_allow_html=True)
                with kpi2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">現在の馬場設定</div><div class="kpi-value" style="color:#F59E0B;">{track_cond}</div></div>', unsafe_allow_html=True)
                with kpi3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">AI投資額</div><div class="kpi-value">{int(ai_invest):,}<span style="font-size:1.2rem; color:#94A3B8;">円</span></div></div>', unsafe_allow_html=True)
                with kpi4: st.markdown(f'<div class="kpi-card"><div class="kpi-title">AIシミュレーション利益</div><div class="kpi-value" style="color:{profit_color};">{sign}{ai_profit:,}<span style="font-size:1.2rem; color:#94A3B8;">円</span></div></div>', unsafe_allow_html=True)

                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("#### 🎯 推奨買い目カード")
                if not has_valid_data:
                    st.warning("⚠️ 予測データがありません。")
                elif not honmei:
                    st.info("ℹ️ 現在のデータでは「◎(本命)」が存在しないため、買い目を生成できません。")
                else:
                    h_str = honmei[0]
                    t_str = taikou[0] if taikou else ""
                    tn_str = tana[0] if tana else ""
                    相手_all = [t for t in [t_str, tn_str] + himo if t]
                    相手_str = " - ".join(相手_all)
                    
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1:
                        st.markdown(f"""<div class="ticket-card"><div style="color:#94A3B8; font-size:0.9rem; margin-bottom:5px;">おすすめ券種① (軸)</div><div style="font-size:1.3rem; font-weight:bold;">単勝 / 複勝</div><div style="color:#10B981; font-size:1.5rem; font-weight:bold; margin-top:10px;">{h_str}</div></div>""", unsafe_allow_html=True)
                    with col_t2:
                        st.markdown(f"""<div class="ticket-card"><div style="color:#94A3B8; font-size:0.9rem; margin-bottom:5px;">おすすめ券種② (基本)</div><div style="font-size:1.3rem; font-weight:bold;">馬連 / ワイド流し</div><div style="color:#3B82F6; font-size:1.5rem; font-weight:bold; margin-top:10px;">{h_str} <span style="color:#94A3B8; font-size:1.2rem;">→</span> {相手_str}</div></div>""", unsafe_allow_html=True)
                    with col_t3:
                        st.markdown(f"""<div class="ticket-card"><div style="color:#94A3B8; font-size:0.9rem; margin-bottom:5px;">おすすめ券種③ (三連系)</div><div style="font-size:1.3rem; font-weight:bold;">3連複フォーメーション</div><div style="color:#EF4444; font-size:1.2rem; font-weight:bold; margin-top:10px;">1段目: {h_str}<br>2段目: {t_str} - {tn_str}<br>3段目: {相手_str}</div></div>""", unsafe_allow_html=True)

                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("#### 📋 馬番データ詳細一覧")
                if has_valid_data:
                    display_cols = [c for c in ['馬番', '馬名', '単勝オッズ', '実力順位(RL)', '適正順位(CL)', '評価', '期待値', '判定', 'レース結果', '単勝払戻金'] if c in df_calc.columns]
                    st.dataframe(df_calc[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("まだ解析されたレースがありません。左のメニューから実行してください。")

# ==========================================
# 🔍 メイン画面：レース予測・自動実行
# ==========================================
elif menu == "レース予測・自動実行":
    st.markdown("<p class='main-header'>レース予測 (ステップ3：全レース一括スキャン)</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🚀 指定日付の全レース一括解析", "🎯 1レース指定解析"])
    
    with tab1:
        st.write("netkeibaから指定した日付のレース一覧をスキャンし、連続解析します。過去のレース検証にも使えます。")
        
        target_date = st.date_input("📅 取得する開催日を選択してください", datetime.today())
        date_str = target_date.strftime("%Y%m%d")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            scan_jra = st.checkbox("🟢 中央競馬 (JRA) を取得する", value=False)
            selected_jra_places = []
            if scan_jra:
                selected_jra_places = st.multiselect("取得する会場を選択 (中央)", ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"], default=[])
                
        with col_c2:
            scan_nar = st.checkbox("🟠 地方競馬 (NAR) を取得する", value=False)
            selected_nar_places = []
            if scan_nar:
                selected_nar_places = st.multiselect("取得する会場を選択 (地方)", ["大井", "水沢", "盛岡", "川崎", "船橋", "浦和", "園田", "姫路", "高知", "佐賀", "門別", "名古屋", "笠松", "金沢"], default=[])
            
        if st.button(f"🌅 【自動化】{target_date.strftime('%Y年%m月%d日')}のレースをスキャン開始", use_container_width=True):
            valid_place_codes = []
            place_map_jra = {"01":"札幌", "02":"函館", "03":"福島", "04":"新潟", "05":"東京", "06":"中山", "07":"中京", "08":"京都", "09":"阪神", "10":"小倉"}
            place_map_nar = {"30":"大井", "31":"水沢", "32":"盛岡", "35":"川崎", "36":"船橋", "37":"浦和", "42":"園田", "43":"姫路", "50":"高知", "54":"佐賀", "65":"門別", "21":"名古屋", "22":"笠松", "23":"金沢"}
            
            inv_jra = {v: k for k, v in place_map_jra.items()}
            inv_nar = {v: k for k, v in place_map_nar.items()}
            
            if scan_jra: valid_place_codes.extend([inv_jra[p] for p in selected_jra_places])
            if scan_nar: valid_place_codes.extend([inv_nar[p] for p in selected_nar_places])

            if not scan_jra and not scan_nar:
                st.warning("取得する競馬（中央または地方）にチェックを入れてください。")
            elif not valid_place_codes:
                st.warning("取得する会場を1つ以上選択してください。")
            else:
                with st.status(f"🌐 {target_date.strftime('%Y/%m/%d')}の全レースリストを取得中...", expanded=True) as status:
                    try:
                        driver = get_driver()
                        race_ids = []
                        urls_to_scan = []
                        
                        if scan_jra: 
                            urls_to_scan.append(f"https://race.netkeiba.com/top/race_list.html?kaisai_date={date_str}")
                            urls_to_scan.append(f"https://race.netkeiba.com/top/result_list.html?kaisai_date={date_str}")
                        if scan_nar: 
                            urls_to_scan.append(f"https://nar.netkeiba.com/top/race_list.html?kaisai_date={date_str}")
                            urls_to_scan.append(f"https://nar.netkeiba.com/top/result_list.html?kaisai_date={date_str}")
                        
                        for url in urls_to_scan:
                            driver.get(url)
                            time.sleep(2)
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            for a in soup.find_all('a', href=True):
                                match = re.search(r'race_id=(\d{12})', a['href'])
                                if match:
                                    r_id = match.group(1)
                                    if r_id[4:6] in valid_place_codes:
                                        if r_id not in race_ids: race_ids.append(r_id)
                        
                        race_ids.sort()
                        if not race_ids: 
                            places = ", ".join(selected_jra_places + selected_nar_places)
                            raise Exception(f"{target_date.strftime('%Y年%m月%d日')}に、選択した会場（{places}）でのレース開催が見つかりませんでした。")
                        
                        st.write(f"✅ 条件に一致する {len(race_ids)}件のレースを発見しました。解析を開始します...")
                        
                        ss = gc.open(ss_name)
                        analysis_sheet = ss.worksheet("分析シート")
                        
                        overall_progress = st.progress(0)
                        log_text = st.empty()
                        sub_progress = st.progress(0)
                        
                        for i, r_id in enumerate(race_ids):
                            st.write(f"▶ {i+1}/{len(race_ids)}: レースID {r_id} を解析開始")
                            try:
                                fetch_and_analyze_single_race(r_id, driver, analysis_sheet, sub_progress, log_text, is_batch=True)
                                time.sleep(3)
                            except Exception as e:
                                st.write(f"⚠️ {r_id}はスキップ: {str(e)}")
                            overall_progress.progress((i + 1) / len(race_ids))
                            
                        driver.quit()
                        status.update(label="🎉 選択した全レースの解析が完了しました！ダッシュボードをご確認ください。", state="complete", expanded=False)
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        status.update(label="エラーが発生しました", state="error")
                        st.error(f"詳細: {str(e)}")

    with tab2:
        st.write("特定のレースIDを手動で入力して解析します（過去のレースも可能）。")
        race_id = st.text_input("🎯 分析するレースIDを入力してください", placeholder="例: 202610020811")
        if st.button("🚀 このレースのみを解析"):
            if not race_id:
                st.warning("レースIDを入力してください。")
            else:
                with st.status("🌐 データを高速取得中...", expanded=True) as status:
                    try:
                        driver = get_driver()
                        progress_bar = st.progress(0)
                        log_text = st.empty()
                        fetch_and_analyze_single_race(race_id, driver, gc.open(ss_name).worksheet("分析シート"), progress_bar, log_text, is_batch=False)
                        driver.quit()
                        status.update(label="🎉 解析が完了しました！ダッシュボードをご確認ください。", state="complete", expanded=False)
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        status.update(label="エラーが発生しました", state="error")
                        st.error(f"詳細: {str(e)}")
        
        st.markdown("---")
        st.subheader("【レース後】収支記録")
        if st.button("💰 確定結果＆払戻金を自動取得"):
            if not race_id: st.warning("レースIDを入力してください。")
            else:
                with st.status("レース結果を取得中...", expanded=True) as status:
                    try:
                        driver = get_driver()
                        domain = "race.netkeiba.com"
                        if len(race_id) >= 12 and race_id[4:6].isdigit():
                            if int(race_id[4:6]) >= 11:
                                domain = "nar.netkeiba.com"
                        
                        driver.get(f"https://{domain}/race/result.html?race_id={race_id}")
                        time.sleep(2)
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        
                        if not soup.find('table', class_=re.compile(r'RaceTable', re.I)):
                            domain = "nar.netkeiba.com" if domain == "race.netkeiba.com" else "race.netkeiba.com"
                            driver.get(f"https://{domain}/race/result.html?race_id={race_id}")
                            time.sleep(2)
                            soup = BeautifulSoup(driver.page_source, 'html.parser')

                        driver.quit()
                        
                        result_map = {}
                        for tr in soup.find_all('tr'):
                            rank_elem, umaban_elem = tr.find(class_=re.compile(r'Rank', re.I)), tr.find(class_=re.compile(r'Umaban', re.I))
                            if rank_elem and umaban_elem:
                                r_match, u_match = re.search(r'(\d+)', rank_elem.text.strip()), re.search(r'(\d+)', umaban_elem.text.strip())
                                if r_match and u_match: result_map[u_match.group(1)] = r_match.group(1)
                                
                        tansho_payout = ""
                        for tr in soup.find_all('tr'):
                            if "単勝" in tr.get_text(separator='', strip=True):
                                match = re.search(r'([0-9,]+)円', tr.text)
                                if match: tansho_payout = match.group(1).replace(",", "")
                                break
                                    
                        analysis_sheet = gc.open(ss_name).worksheet("分析シート")
                        existing_horses = analysis_sheet.get('A2:B25')
                        q_data, r_data = [], []
                        for row in existing_horses:
                            if len(row) < 1 or not str(row[0]).strip(): continue
                            umaban = str(row[0]).strip()
                            horse_rank = result_map.get(umaban, "")
                            horse_payout = tansho_payout if horse_rank == "1" else ""
                            q_data.append([horse_rank])
                            r_data.append([horse_payout])
                            
                        end_row = 1 + len(q_data)
                        analysis_sheet.update(range_name=f"Q2:Q{end_row}", values=q_data, value_input_option='USER_ENTERED')
                        analysis_sheet.update(range_name=f"R2:R{end_row}", values=r_data, value_input_option='USER_ENTERED')
                        
                        status.update(label="💰 記録完了！", state="complete", expanded=False)
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        status.update(label="エラーが発生しました", state="error")
                        st.error(f"詳細: {str(e)}")
