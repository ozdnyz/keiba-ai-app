# ==========================================
# 🛠️ 1レース解析用の共通モジュール
# ==========================================
def fetch_and_analyze_single_race(race_id, driver, analysis_sheet, progress_bar, log_text, is_batch=False):
    domain = "race.netkeiba.com"

    def clean_text(text):
        return re.sub(r'\s+', '', text.strip()) if text else ""

    log_text.write(f"🔍 出馬表と開催会場を解析中...")
    driver.get(f"https://{domain}/race/shutuba.html?race_id={race_id}")
    time.sleep(2.0)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    if not soup.find('tr', class_=re.compile(r'HorseList', re.I)):
        driver.get(f"https://{domain}/race/shutuba.html?race_id={race_id}")
        time.sleep(2.0)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

    place_code = race_id[4:6] if len(race_id) >= 12 else ""
    place_map = {"01":"札幌", "02":"函館", "03":"福島", "04":"新潟", "05":"東京", "06":"中山", "07":"中京", "08":"京都", "09":"阪神", "10":"小倉"}
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
    odds_map = {}
    
    for tr in soup.find_all('tr', class_=re.compile(r'HorseList', re.I)):
        td_umaban = tr.find(class_=re.compile(r'Umaban', re.I))
        td_horse = tr.find(class_=re.compile(r'HorseInfo', re.I))
        if td_umaban and td_horse:
            u_match = re.search(r'\d+', td_umaban.text)
            a_tag = td_horse.find('a', href=re.compile(r'horse/'))
            if u_match and a_tag:
                u_num = str(int(u_match.group(0)))
                name = clean_text(a_tag.text)
                href = a_tag.get('href')
                if name and u_num and [u_num, name] not in horse_list:
                    horse_list.append([u_num, name])
                    horse_links[name] = href
                
                odds_td = tr.find(class_=re.compile(r'Odds', re.I))
                if odds_td:
                    o_m = re.search(r'([0-9]+\.[0-9]+)', odds_td.text)
                    if o_m: odds_map[u_num] = o_m.group(1)
    
    if not horse_list: 
        raise Exception("馬番が未発表です（週末のレースは木・金曜に確定します）")
    
    horse_list = sorted(horse_list, key=lambda x: int(x[0]))
    
    if len(odds_map) < len(horse_list) / 2:
        log_text.write("📊 最新オッズを専用ページから取得中...")
        driver.get(f"https://{domain}/odds/index.html?type=b1&race_id={race_id}")
        for _ in range(3):
            time.sleep(1.5)
            odds_soup = BeautifulSoup(driver.page_source, 'html.parser')
            for tr in odds_soup.find_all('tr'):
                umaban_td = tr.find(class_=re.compile(r'(Umaban|Num|Waku)', re.I))
                if umaban_td:
                    u_match = re.search(r'\d+', umaban_td.text)
                    if u_match:
                        u_num = str(int(u_match.group(0)))
                        odds_td = tr.find(class_=re.compile(r'Odds', re.I))
                        if odds_td:
                            text = odds_td.text.strip()
                            if '-' not in text:
                                o_match = re.search(r'([0-9]+\.[0-9]+)', text)
                                if o_match: odds_map[u_num] = o_match.group(1)
            if len(odds_map) >= len(horse_list) / 2: break
                            
    if len(odds_map) < len(horse_list) / 2:
        log_text.write("📊 レース結果から確定オッズを取得中...")
        try:
            req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            res = requests.get(f"https://{domain}/race/result.html?race_id={race_id}", headers=req_headers, timeout=5)
            res_soup = BeautifulSoup(res.content, 'html.parser')
            result_table = res_soup.find('table', class_=re.compile(r'RaceTable', re.I))
            if result_table:
                headers_th = result_table.find_all('th')
                odds_idx, umaban_idx = -1, -1
                for i, th in enumerate(headers_th):
                    if '単勝' in th.text: odds_idx = i
                    if '馬番' in th.text: umaban_idx = i
                if odds_idx != -1 and umaban_idx != -1:
                    for tr in result_table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) > max(odds_idx, umaban_idx):
                            u_match = re.search(r'\d+', tds[umaban_idx].text.strip())
                            o_match = re.search(r'([0-9.]+)', tds[odds_idx].text.strip())
                            if u_match and o_match: odds_map[str(int(u_match.group(0)))] = o_match.group(1)
        except Exception:
            pass
    
    total_horses = len(horse_list)
    current_idx = 0
    raw_scores = []
    
    for row in horse_list:
        u_num, umamei = row[0], row[1]
        umamei_clean = clean_text(umamei)
        current_idx += 1
        
        prefix = f"[{race_name}] " if is_batch else ""
        log_text.write(f"🐎 {prefix}{u_num}番 {umamei} を分析中... ({current_idx}/{total_horses})")
        progress_bar.progress(current_idx / total_horses)
        
        avg_rank, rentai_rate = 99.0, 0.0
        chichi, hahachichi = "", ""
        
        if umamei_clean in horse_links:
            db_url = horse_links[umamei_clean]
            full_db_url = "https:" + db_url if not db_url.startswith('http') else db_url
            
            try:
                req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
                res = requests.get(full_db_url, headers=req_headers, timeout=5)
                db_soup = BeautifulSoup(res.content, 'html.parser')
                
                # 🌟 App側にも「強固な血統表ロジック」を適用
                blood_table = db_soup.find('table', class_='blood_table')
                if blood_table:
                    rows_b = blood_table.find_all('tr')
                    if len(rows_b) > 0:
                        sire_a = rows_b[0].find('a')
                        if sire_a: chichi = clean_text(sire_a.text)
                        
                        mid_idx = len(rows_b) // 2
                        if mid_idx < len(rows_b):
                            mid_tds = rows_b[mid_idx].find_all('td')
                            if len(mid_tds) >= 2:
                                bms_a = mid_tds[1].find('a')
                                if bms_a: hahachichi = clean_text(bms_a.text)

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
            except Exception:
                pass
            
            time.sleep(0.2)
        
        # 🌟 Appのデータフレームにも父と母父の情報を追加して保持
        raw_scores.append({
            '馬番': u_num, '馬名': umamei, '単勝オッズ': odds_map.get(u_num, "0.0"), 
            'avg_rank': avg_rank, 'rentai_rate': rentai_rate,
            '父': chichi, '母父': hahachichi
        })
        
    score_df = pd.DataFrame(raw_scores)
    score_df['実力順位(RL)'] = score_df['avg_rank'].rank(method='min', ascending=True).astype(int)
    score_df['適正順位(CL)'] = score_df['rentai_rate'].rank(method='min', ascending=False).astype(int)
    
    # スプレッドシート（分析シート）への書き込み用マトリックスは既存の5列を維持
    final_matrix = []
    for _, r in score_df.iterrows():
        final_matrix.append([r['馬番'], r['馬名'], str(r['単勝オッズ']), str(r['実力順位(RL)']), str(r['適正順位(CL)'])])
        
    try:
        clear_data = [["", "", "", "", ""] for _ in range(24)]
        analysis_sheet.update(range_name='A2:E25', values=clear_data, value_input_option='USER_ENTERED')
        analysis_sheet.update(range_name=f'A2:E{1+len(final_matrix)}', values=final_matrix, value_input_option='USER_ENTERED')
    except Exception as e:
        log_text.write(f"※スプレッドシートへの記録をスキップしました: {str(e)}")
    
    _, _, honmei_list, _, _, _, _, _, _, _, _, _, _, race_rank, _, honmei_exp = run_ai_core(score_df, "良")
    
    st.session_state.race_history[race_id] = {
        'race_name': race_name,
        'race_rank': race_rank,
        'honmei': honmei_list,
        'honmei_exp': honmei_exp,
        'ai_decision': '買い' if race_rank != "見送り" else '見送り',
        'df_raw': score_df  # 父と母父が含まれた状態のデータをセッションに保存
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
                    display_cols = [c for c in ['馬番', '馬名', '父', '母父', '単勝オッズ', '実力順位(RL)', '適正順位(CL)', 'AIスコア', '評価', '期待値', '判定'] if c in df_calc.columns]
                    st.dataframe(df_calc[display_cols], use_container_width=True, hide_index=True, height=700)
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
        
        scan_jra = st.checkbox("🟢 中央競馬 (JRA) を取得する", value=True)
        selected_jra_places = []
        if scan_jra:
            selected_jra_places = st.multiselect("取得する会場を選択 (中央)", ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"], default=[])
            
        if st.button(f"🌅 【自動化】{target_date.strftime('%Y年%m月%d日')}のレースをスキャン開始", use_container_width=True):
            valid_place_codes = []
            place_map_jra = {"01":"札幌", "02":"函館", "03":"福島", "04":"新潟", "05":"東京", "06":"中山", "07":"中京", "08":"京都", "09":"阪神", "10":"小倉"}
            
            inv_jra = {v: k for k, v in place_map_jra.items()}
            if scan_jra: valid_place_codes.extend([inv_jra[p] for p in selected_jra_places])

            if not scan_jra:
                st.warning("取得する競馬（中央）にチェックを入れてください。")
            elif not valid_place_codes:
                st.warning("取得する会場を1つ以上選択してください。")
            else:
                with st.status(f"🌐 {target_date.strftime('%Y/%m/%d')}の全レースリストを取得中...", expanded=True) as status:
                    try:
                        driver = None
                        try:
                            driver = get_driver()
                            race_ids = []
                            urls_to_scan = []
                            
                            if scan_jra: 
                                urls_to_scan.append(f"https://race.netkeiba.com/top/race_list.html?kaisai_date={date_str}")
                                urls_to_scan.append(f"https://race.netkeiba.com/top/result_list.html?kaisai_date={date_str}")
                            
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
                                places = ", ".join(selected_jra_places)
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
                                except Exception as e:
                                    st.write(f"⚠️ {r_id}はスキップ: {str(e)}")
                                    
                                overall_progress.progress((i + 1) / len(race_ids))
                                time.sleep(random.uniform(2.0, 4.0))
                                
                            save_history_to_sheet(analysis_sheet, st.session_state.race_history)
                            status.update(label="🎉 選択した全レースの解析が完了しました！ダッシュボードをご確認ください。", state="complete", expanded=False)
                            time.sleep(2)
                            st.rerun()
                        finally:
                            if driver:
                                try: driver.quit()
                                except: pass
                    except Exception as e:
                        status.update(label="エラーが発生しました", state="error")
                        st.error(f"詳細: {str(e)}")

    with tab2:
        st.write("指定した日付・競馬場・レース番号から解析します。")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            target_date_single = st.date_input("📅 開催日", datetime.today(), key="single_date")
            date_str_single = target_date_single.strftime("%Y%m%d")
        with col_s2:
            place_map_all = {"01":"札幌", "02":"函館", "03":"福島", "04":"新潟", "05":"東京", "06":"中山", "07":"中京", "08":"京都", "09":"阪神", "10":"小倉"}
            inv_place_map = {v: k for k, v in place_map_all.items()}
            place_single = st.selectbox("🏟️ 競馬場", list(inv_place_map.keys()))
        with col_s3:
            race_num_single = st.selectbox("🏇 レース番号", [f"{i}R" for i in range(1, 13)])
            
        target_place_code = inv_place_map[place_single]
        target_r_num = str(race_num_single).replace("R", "").zfill(2)
        domain_top = "race.netkeiba.com"

        if st.button("🚀 このレースのみを解析"):
            with st.status("🌐 データ取得中...", expanded=True) as status:
                driver = None
                try:
                    driver = get_driver()
                    
                    found_id = None
                    urls = [
                        f"https://{domain_top}/top/race_list.html?kaisai_date={date_str_single}",
                        f"https://{domain_top}/top/result_list.html?kaisai_date={date_str_single}"
                    ]
                    for url in urls:
                        if found_id: break
                        driver.get(url)
                        time.sleep(1.5)
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        for a in soup.find_all('a', href=True):
                            match = re.search(r'race_id=(\d{12})', a['href'])
                            if match:
                                r_id = match.group(1)
                                if r_id[4:6] == target_place_code and r_id[10:12] == target_r_num:
                                    found_id = r_id
                                    break
                                    
                    if not found_id:
                        status.update(label="エラー", state="error")
                        st.error(f"{target_date_single.strftime('%Y年%m月%d日')}の{place_single}{race_num_single}のレースは見つかりませんでした。")
                    else:
                        ss = gc.open(ss_name)
                        analysis_sheet = ss.worksheet("分析シート")
                        progress_bar = st.progress(0)
                        log_text = st.empty()
                        
                        fetch_and_analyze_single_race(found_id, driver, analysis_sheet, progress_bar, log_text, is_batch=False)
                        
                        save_history_to_sheet(analysis_sheet, st.session_state.race_history)
                        
                        status.update(label="🎉 解析完了！ダッシュボードをご確認ください。", state="complete", expanded=False)
                        time.sleep(1.5)
                        st.rerun()
                except Exception as e:
                    status.update(label="エラーが発生しました", state="error")
                    st.error(f"詳細: {str(e)}")
                finally:
                    if driver:
                        try: driver.quit()
                        except: pass
        
        st.markdown("---")
        st.subheader("【レース後】収支記録＆データ蓄積")
        st.write("Colab版の全30項目に完全対応し、結果取得時に不足している馬体重や上がり3Fなどを一括補充してデータベースへ保存します。")
        
        if st.button("💰 確定結果取得＆データベースへ保存"):
            with st.status("レース情報を特定中...", expanded=True) as status:
                driver = None
                try:
                    driver = get_driver()
                    
                    found_id = None
                    urls = [
                        f"https://{domain_top}/top/race_list.html?kaisai_date={date_str_single}",
                        f"https://{domain_top}/top/result_list.html?kaisai_date={date_str_single}"
                    ]
                    for url in urls:
                        if found_id: break
                        driver.get(url)
                        time.sleep(1.5)
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        for a in soup.find_all('a', href=True):
                            match = re.search(r'race_id=(\d{12})', a['href'])
                            if match:
                                r_id = match.group(1)
                                if r_id[4:6] == target_place_code and r_id[10:12] == target_r_num:
                                    found_id = r_id
                                    break

                    if not found_id:
                        status.update(label="エラー", state="error")
                        st.error(f"{target_date_single.strftime('%Y年%m月%d日')}の{place_single}{race_num_single}のレースは見つかりませんでした。")
                    else:
                        status.update(label="結果を取得中...")
                        driver.get(f"https://{domain_top}/race/result.html?race_id={found_id}")
                        time.sleep(2)
                        soup = BeautifulSoup(driver.page_source, 'html.parser')

                        def clean_text(text):
                            return re.sub(r'\s+', '', text.strip()) if text else ""
                            
                        title_elem = soup.find(class_='RaceName')
                        race_title = re.sub(r'\s+', ' ', title_elem.text.strip()) if title_elem else f"レースID:{found_id}"

                        track_type, distance, direction, weather, track_cond = "", "", "", "", ""
                        race_data_elem = soup.find(class_='RaceData01')
                        if race_data_elem:
                            rd_text = race_data_elem.text.replace('\xa0', ' ')
                            m_type = re.search(r'(芝|ダ|障).*?(\d+)m', rd_text)
                            if m_type: 
                                track_type, distance = m_type.group(1), m_type.group(2)
                                # 🌟 回りの自動判定を追加
                                if place_single == "新潟" and distance == "1000":
                                    direction = "直"
                                elif place_single in ["東京", "中京", "新潟"]:
                                    direction = "左"
                                else:
                                    direction = "右"
                                    
                            m_weather = re.search(r'天候\s*:\s*([^\s/]+)', rd_text)
                            if m_weather: weather = clean_text(m_weather.group(1))
                            m_cond = re.search(r'(芝|ダ|障|馬場)\s*:\s*([^\s/]+)', rd_text)
                            if m_cond: track_cond = clean_text(m_cond.group(2))

                        result_table = soup.find('table', class_=re.compile(r'RaceTable', re.I))
                        if not result_table:
                            status.update(label="エラー: 結果テーブルが見つかりません", state="error")
                            st.stop()
                            
                        headers = [th.text.strip().replace('\n', '') for th in result_table.find_all('th')]
                        cols_map = {}
                        for idx, th_text in enumerate(headers):
                            if '着順' in th_text: cols_map['rank'] = idx
                            elif '枠' in th_text: cols_map['waku'] = idx
                            elif '馬番' in th_text: cols_map['umaban'] = idx
                            elif '性齢' in th_text: cols_map['sex_age'] = idx
                            elif '騎手' in th_text: cols_map['jockey'] = idx
                            elif '斤量' in th_text: cols_map['kinryo'] = idx
                            elif 'タイム' == th_text: cols_map['time'] = idx
                            elif '通過' in th_text: cols_map['passing'] = idx
                            elif '後3F' in th_text or '上り' in th_text or '上がり' in th_text: cols_map['f3'] = idx
                            elif '人気' in th_text: cols_map['popularity'] = idx
                            elif '馬体重' in th_text: cols_map['weight'] = idx
                            elif '調教師' in th_text or '厩舎' in th_text: cols_map['trainer'] = idx

                        result_map = {}
                        for tr in result_table.find_all('tr'):
                            tds = tr.find_all('td')
                            if len(tds) > max(cols_map.values(), default=-1):
                                u_m = re.search(r'\d+', tds[cols_map['umaban']].text)
                                if u_m:
                                    u_num = str(int(u_m.group(0)))
                                    result_map[u_num] = {
                                        '着順': re.search(r'(\d+)', tds[cols_map['rank']].text).group(1) if 'rank' in cols_map and re.search(r'(\d+)', tds[cols_map['rank']].text) else "",
                                        '枠番': clean_text(tds[cols_map['waku']].text) if 'waku' in cols_map else "",
                                        '性齢': clean_text(tds[cols_map['sex_age']].text) if 'sex_age' in cols_map else "",
                                        '騎手': clean_text(tds[cols_map['jockey']].text) if 'jockey' in cols_map else "",
                                        '斤量': clean_text(tds[cols_map['kinryo']].text) if 'kinryo' in cols_map else "",
                                        'タイム': clean_text(tds[cols_map['time']].text) if 'time' in cols_map else "",
                                        '上がり3F': clean_text(tds[cols_map['f3']].text) if 'f3' in cols_map else "",
                                        '通過順': clean_text(tds[cols_map['passing']].text) if 'passing' in cols_map else "",
                                        '人気': clean_text(tds[cols_map['popularity']].text) if 'popularity' in cols_map else "",
                                        '馬体重': clean_text(tds[cols_map['weight']].text) if 'weight' in cols_map else "",
                                        '調教師': clean_text(tds[cols_map['trainer']].text) if 'trainer' in cols_map else "",
                                    }

                        tansho_payout = "0"
                        for th in soup.find_all('th'):
                            if '単勝' in th.text:
                                row = th.find_parent('tr')
                                if row:
                                    m_pay = re.search(r'([0-9,]+)円', row.text)
                                    if m_pay: tansho_payout = m_pay.group(1).replace(",", "")
                                    break

                        ss = gc.open(ss_name)
                        
                        analysis_sheet = ss.worksheet("分析シート")
                        existing_horses = analysis_sheet.get('A2:E25')
                        q_data, r_data = [], []
                        for row in existing_horses:
                            if len(row) < 1 or not str(row[0]).strip(): continue
                            umaban = str(row[0]).strip()
                            horse_rank = result_map.get(umaban, {}).get('着順', "")
                            horse_payout = tansho_payout if horse_rank == "1" else ""
                            q_data.append([horse_rank])
                            r_data.append([horse_payout])
                            
                        end_row = 1 + len(q_data)
                        analysis_sheet.update(range_name=f"J2:J{end_row}", values=q_data, value_input_option='USER_ENTERED')
                        analysis_sheet.update(range_name=f"K2:K{end_row}", values=r_data, value_input_option='USER_ENTERED')
                        
                        if found_id in st.session_state.race_history:
                            db_sheet = ss.worksheet("過去データ蓄積")
                            target_race = st.session_state.race_history[found_id]
                            df_calc, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = run_ai_core(target_race['df_raw'], "良")
                            
                            append_rows = []
                            for idx, row in df_calc.iterrows():
                                if pd.isna(row['馬番']) or row['馬番'] == "": continue
                                u_num = str(row['馬番'])
                                r_info = result_map.get(u_num, {})
                                h_rank = r_info.get('着順', "")
                                h_pay = tansho_payout if h_rank == "1" else "0"
                                
                                chichi = row.get('父', '')
                                hahachichi = row.get('母父', '')
                                
                                # 🌟 変更点：「回り」を挿入して全31項目に合わせる
                                append_rows.append([
                                    date_str_single, place_single, race_title, 
                                    track_type, distance, direction, weather, track_cond,
                                    r_info.get('枠番', ''), u_num, row.get('馬名', ''), r_info.get('性齢', ''), 
                                    r_info.get('騎手', ''), r_info.get('斤量', ''), r_info.get('馬体重', ''), r_info.get('調教師', ''), 
                                    chichi, hahachichi, row.get('単勝オッズ', ''), r_info.get('人気', ''), 
                                    row.get('実力順位(RL)', ''), row.get('適正順位(CL)', ''), 
                                    row.get('AIスコア', ''), row.get('評価', ''), 
                                    row.get('期待値', ''), row.get('判定', ''), 
                                    h_rank, r_info.get('タイム', ''), r_info.get('上がり3F', ''), r_info.get('通過順', ''), h_pay
                                ])
                                
                            if append_rows:
                                db_sheet.append_rows(append_rows, value_input_option='USER_ENTERED')
                                status.update(label="💰 記録完了！データベースへの保存も成功しました。", state="complete", expanded=False)
                        else:
                            status.update(label="💰 記録完了！（※画面に解析データがないため、データベース保存はスキップしました）", state="complete", expanded=False)
                            
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    status.update(label="エラーが発生しました", state="error")
                    st.error(f"詳細: {str(e)}")
                finally:
                    if driver:
                        try: driver.quit()
                        except: pass
