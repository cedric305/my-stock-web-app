import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# 1. 核心功能：直接呼叫 Yahoo API
# ==========================================
@st.cache_data(ttl=60)
def fetch_stock_data_direct(symbol, range_str="6mo", interval="1d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"range": range_str, "interval": interval, "includePrePost": "false"}
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
            return None
            
        result = data["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        timestamps = result["timestamp"]
        
        df = pd.DataFrame({
            "Date": pd.to_datetime(timestamps, unit='s'),
            "Open": quote.get("open", []),
            "High": quote.get("high", []),
            "Low": quote.get("low", []),
            "Close": quote.get("close", []),
            "Volume": quote.get("volume", [])
        })
        
        df.set_index("Date", inplace=True)
        df.dropna(subset=["Close"], inplace=True)
        
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Taipei')
        else:
            df.index = df.index.tz_convert('Asia/Taipei')
            
        return df
    except Exception as e:
        print(f"❌ {symbol} 抓取失敗: {e}")
        return None

def get_latest_quote_and_change(symbol):
    df = fetch_stock_data_direct(symbol, range_str="5d")
    if df is not None and len(df) >= 2:
        latest = df.iloc[-1]['Close']
        prev = df.iloc[-2]['Close']
        change_amount = latest - prev
        change_pct = (change_amount / prev) * 100
        return latest, change_pct
    elif df is not None and len(df) == 1:
        return df.iloc[-1]['Close'], 0.0
    return None, None

# ==========================================
# 2. 資料庫與 CRUD 操作 (資料庫 V17 - 資訊服務與銅箔基板新增版)
# ==========================================

# 初始化族群資料
if 'MOCK_GROUPS' not in st.session_state:
    st.session_state.MOCK_GROUPS = [
        {"id": 1, "name": "記憶體", "note": ""},
        {"id": 2, "name": "IC載板", "note": ""},
        {"id": 3, "name": "矽光子", "note": ""},
        {"id": 4, "name": "電子通路", "note": ""},
        {"id": 5, "name": "太陽能", "note": ""},
        {"id": 6, "name": "低軌衛星", "note": ""},
        {"id": 7, "name": "半導體測試", "note": ""},
        {"id": 8, "name": "面板", "note": ""},
        {"id": 9, "name": "散熱", "note": ""},
        {"id": 10, "name": "高階玻纖布", "note": ""},
        {"id": 11, "name": "被動元件", "note": ""},
        {"id": 12, "name": "半導體設備", "note": ""},
        {"id": 13, "name": "電子五哥", "note": ""},
        {"id": 14, "name": "CCL", "note": ""},
        {"id": 15, "name": "重電", "note": ""},
        {"id": 16, "name": "資訊服務", "note": ""},
        {"id": 17, "name": "銅箔基板", "note": ""},
    ]

# 初始化個股資料
if 'MOCK_STOCKS' not in st.session_state:
    st.session_state.MOCK_STOCKS = [
        # Group 1: 記憶體
        {"id": 101, "symbol": "2344.TW", "name": "華邦電", "group_id": 1, "ma_settings": "5,10,20", "note": ""},
        {"id": 102, "symbol": "3006.TW", "name": "晶豪科", "group_id": 1, "ma_settings": "5,10,20", "note": ""},
        {"id": 103, "symbol": "8299.TWO", "name": "群聯", "group_id": 1, "ma_settings": "5,10,20", "note": ""},
        {"id": 104, "symbol": "2408.TW", "name": "南亞科", "group_id": 1, "ma_settings": "5,10,20", "note": ""},
        {"id": 105, "symbol": "4967.TW", "name": "十銓", "group_id": 1, "ma_settings": "5,10,20", "note": ""},
        {"id": 106, "symbol": "2337.TW", "name": "旺宏", "group_id": 1, "ma_settings": "5,10,20", "note": ""},
        {"id": 107, "symbol": "3260.TWO", "name": "威剛", "group_id": 1, "ma_settings": "5,10,20", "note": ""},
        {"id": 108, "symbol": "3135.TWO", "name": "凌航", "group_id": 1, "ma_settings": "5,10,20", "note": ""},

        # Group 2: IC載板
        {"id": 201, "symbol": "3037.TW", "name": "欣興", "group_id": 2, "ma_settings": "5,10,20", "note": "ABF"},
        {"id": 202, "symbol": "3189.TW", "name": "景碩", "group_id": 2, "ma_settings": "5,10,20", "note": "ABF/BT"},
        {"id": 203, "symbol": "8046.TW", "name": "南電", "group_id": 2, "ma_settings": "5,10,20", "note": "ABF"},
        {"id": 204, "symbol": "4958.TW", "name": "臻鼎-KY", "group_id": 2, "ma_settings": "5,10,20", "note": "PCB"},
        {"id": 205, "symbol": "2383.TW", "name": "台光電", "group_id": 2, "ma_settings": "5,10,20", "note": "CCL"},

        # Group 3: 矽光子
        {"id": 301, "symbol": "6451.TW", "name": "訊芯-KY", "group_id": 3, "ma_settings": "5,10,20", "note": ""},
        {"id": 302, "symbol": "3363.TWO", "name": "上詮", "group_id": 3, "ma_settings": "5,10,20", "note": ""},
        {"id": 303, "symbol": "3163.TWO", "name": "波若威", "group_id": 3, "ma_settings": "5,10,20", "note": ""},
        {"id": 304, "symbol": "6442.TW", "name": "光聖", "group_id": 3, "ma_settings": "5,10,20", "note": ""},
        {"id": 305, "symbol": "4979.TWO", "name": "華星光", "group_id": 3, "ma_settings": "5,10,20", "note": ""},
        {"id": 306, "symbol": "2345.TW", "name": "智邦", "group_id": 3, "ma_settings": "5,10,20", "note": ""},
        {"id": 307, "symbol": "2455.TW", "name": "全新", "group_id": 3, "ma_settings": "5,10,20", "note": ""},
        {"id": 308, "symbol": "6588.TWO", "name": "東典光電", "group_id": 3, "ma_settings": "5,10,20", "note": "濾光片"},
        {"id": 309, "symbol": "6426.TWO", "name": "統新", "group_id": 3, "ma_settings": "5,10,20", "note": "濾光片"},
        {"id": 310, "symbol": "7728.TWO", "name": "光矩科", "group_id": 3, "ma_settings": "5,10,20", "note": "LPO透鏡/興櫃"},

        # Group 4: 電子通路
        {"id": 401, "symbol": "8096.TWO", "name": "擎亞", "group_id": 4, "ma_settings": "5,10,20", "note": "IC通路"},
        {"id": 402, "symbol": "3028.TW", "name": "增你強", "group_id": 4, "ma_settings": "5,10,20", "note": "IC通路"},

        # Group 5: 太陽能
        {"id": 501, "symbol": "3576.TW", "name": "聯合再生", "group_id": 5, "ma_settings": "5,10,20", "note": ""},
        {"id": 502, "symbol": "6244.TWO", "name": "茂迪", "group_id": 5, "ma_settings": "5,10,20", "note": ""},
        {"id": 503, "symbol": "6443.TW", "name": "元晶", "group_id": 5, "ma_settings": "5,10,20", "note": ""},
        {"id": 504, "symbol": "2406.TW", "name": "國碩", "group_id": 5, "ma_settings": "5,10,20", "note": "太陽能材料"},

        # Group 6: 低軌衛星
        {"id": 601, "symbol": "2313.TW", "name": "華通", "group_id": 6, "ma_settings": "5,10,20", "note": ""},
        {"id": 602, "symbol": "2367.TW", "name": "燿華", "group_id": 6, "ma_settings": "5,10,20", "note": ""},
        {"id": 603, "symbol": "2312.TW", "name": "金寶", "group_id": 6, "ma_settings": "5,10,20", "note": ""},
        {"id": 604, "symbol": "2485.TW", "name": "兆赫", "group_id": 6, "ma_settings": "5,10,20", "note": ""},
        {"id": 605, "symbol": "6285.TW", "name": "啟碁", "group_id": 6, "ma_settings": "5,10,20", "note": "網通"},

        # Group 7: 半導體測試
        {"id": 701, "symbol": "6510.TW", "name": "精測", "group_id": 7, "ma_settings": "5,10,20", "note": "測試卡"},
        {"id": 702, "symbol": "6223.TW", "name": "旺矽", "group_id": 7, "ma_settings": "5,10,20", "note": "探針卡"},
        {"id": 703, "symbol": "6515.TW", "name": "穎崴", "group_id": 7, "ma_settings": "5,10,20", "note": "測試座"},
        {"id": 704, "symbol": "6217.TW", "name": "中探針", "group_id": 7, "ma_settings": "5,10,20", "note": "探針"},

        # Group 8: 面板
        {"id": 801, "symbol": "3481.TW", "name": "群創", "group_id": 8, "ma_settings": "5,10,20", "note": ""},
        {"id": 802, "symbol": "2409.TW", "name": "友達", "group_id": 8, "ma_settings": "5,10,20", "note": ""},
        {"id": 803, "symbol": "6116.TW", "name": "彩晶", "group_id": 8, "ma_settings": "5,10,20", "note": ""},

        # Group 9: 散熱
        {"id": 901, "symbol": "3017.TW", "name": "奇鋐", "group_id": 9, "ma_settings": "5,10,20", "note": "散熱模組"},
        {"id": 902, "symbol": "3324.TW", "name": "雙鴻", "group_id": 9, "ma_settings": "5,10,20", "note": "液冷散熱"},
        {"id": 903, "symbol": "3653.TW", "name": "健策", "group_id": 9, "ma_settings": "5,10,20", "note": "均熱片"},
        {"id": 904, "symbol": "2486.TW", "name": "一詮", "group_id": 9, "ma_settings": "5,10,20", "note": "導線架/散熱"},

        # Group 10: 高階玻纖布
        {"id": 1001, "symbol": "1802.TW", "name": "台玻", "group_id": 10, "ma_settings": "5,10,20", "note": "低介電玻纖布"},
        {"id": 1002, "symbol": "1815.TWO", "name": "富喬", "group_id": 10, "ma_settings": "5,10,20", "note": "玻纖紗/布"},
        {"id": 1003, "symbol": "5475.TWO", "name": "德宏", "group_id": 10, "ma_settings": "5,10,20", "note": "玻纖布"},

        # Group 11: 被動元件
        {"id": 1101, "symbol": "2327.TW", "name": "國巨", "group_id": 11, "ma_settings": "5,10,20", "note": "龍頭"},
        {"id": 1102, "symbol": "2492.TW", "name": "華新科", "group_id": 11, "ma_settings": "5,10,20", "note": ""},
        {"id": 1103, "symbol": "2375.TW", "name": "凱美", "group_id": 11, "ma_settings": "5,10,20", "note": ""},
        {"id": 1104, "symbol": "8042.TW", "name": "金山電", "group_id": 11, "ma_settings": "5,10,20", "note": ""},
        {"id": 1105, "symbol": "8043.TWO", "name": "蜜望實", "group_id": 11, "ma_settings": "5,10,20", "note": ""},
        {"id": 1106, "symbol": "6173.TWO", "name": "信昌電", "group_id": 11, "ma_settings": "5,10,20", "note": ""},
        {"id": 1107, "symbol": "2478.TW", "name": "大毅", "group_id": 11, "ma_settings": "5,10,20", "note": ""},
        {"id": 1108, "symbol": "5328.TWO", "name": "華容", "group_id": 11, "ma_settings": "5,10,20", "note": "薄膜電容"},

        # Group 12: 半導體設備
        {"id": 1201, "symbol": "1560.TW", "name": "中砂", "group_id": 12, "ma_settings": "5,10,20", "note": "鑽石碟/再生晶圓"},
        {"id": 1202, "symbol": "2360.TW", "name": "致茂", "group_id": 12, "ma_settings": "5,10,20", "note": "量測設備"},

        # Group 13: 電子五哥
        {"id": 1301, "symbol": "2317.TW", "name": "鴻海", "group_id": 13, "ma_settings": "5,10,20", "note": "EMS龍頭/AI"},
        {"id": 1302, "symbol": "2382.TW", "name": "廣達", "group_id": 13, "ma_settings": "5,10,20", "note": "AI伺服器"},
        {"id": 1303, "symbol": "3231.TW", "name": "緯創", "group_id": 13, "ma_settings": "5,10,20", "note": "AI伺服器"},
        {"id": 1304, "symbol": "6669.TW", "name": "緯穎", "group_id": 13, "ma_settings": "5,10,20", "note": "AI伺服器"},
        {"id": 1305, "symbol": "2356.TW", "name": "英業達", "group_id": 13, "ma_settings": "5,10,20", "note": "伺服器代工"},

        # Group 14: CCL
        {"id": 1401, "symbol": "6213.TW", "name": "聯茂", "group_id": 14, "ma_settings": "5,10,20", "note": "銅箔基板"},

        # Group 15: 重電
        {"id": 1501, "symbol": "1519.TW", "name": "華城", "group_id": 15, "ma_settings": "5,10,20", "note": "變壓器"},
        {"id": 1502, "symbol": "1514.TW", "name": "亞力", "group_id": 15, "ma_settings": "5,10,20", "note": "配電盤"},
        {"id": 1503, "symbol": "1513.TW", "name": "中興電", "group_id": 15, "ma_settings": "5,10,20", "note": "GIS設備"},
        {"id": 1504, "symbol": "1511.TWO", "name": "沛波", "group_id": 15, "ma_settings": "5,10,20", "note": "鋼筋加工"},

        # Group 16: 資訊服務 - NEW
        {"id": 1601, "symbol": "6112.TW", "name": "邁達特", "group_id": 16, "ma_settings": "5,10,20", "note": "資服軟體"},
        {"id": 1602, "symbol": "6689.TW", "name": "伊雲谷", "group_id": 16, "ma_settings": "5,10,20", "note": "雲端服務"},

        # Group 17: 銅箔基板 - NEW
        {"id": 1701, "symbol": "8039.TW", "name": "台虹", "group_id": 17, "ma_settings": "5,10,20", "note": "軟性銅箔基板"},
        {"id": 1702, "symbol": "4939.TWO", "name": "亞電", "group_id": 17, "ma_settings": "5,10,20", "note": "軟性銅箔基板"},
        {"id": 1703, "symbol": "2367.TW", "name": "燿華", "group_id": 17, "ma_settings": "5,10,20", "note": "PCB/軟硬結合板"},
    ]

def get_next_id(item_list):
    if not item_list: return 1
    return max(item['id'] for item in item_list) + 1

def add_group(name):
    new_id = get_next_id(st.session_state.MOCK_GROUPS)
    st.session_state.MOCK_GROUPS.append({"id": new_id, "name": name, "note": ""})

def delete_group(group_id):
    st.session_state.MOCK_GROUPS = [g for g in st.session_state.MOCK_GROUPS if g['id'] != group_id]
    st.session_state.MOCK_STOCKS = [s for s in st.session_state.MOCK_STOCKS if s['group_id'] != group_id]

def update_group_name(group_id, new_name):
    for g in st.session_state.MOCK_GROUPS:
        if g['id'] == group_id:
            g['name'] = new_name
            break

def add_stock(group_id, symbol, name):
    new_id = get_next_id(st.session_state.MOCK_STOCKS)
    st.session_state.MOCK_STOCKS.append({
        "id": new_id, 
        "symbol": symbol.upper(), 
        "name": name, 
        "group_id": group_id, 
        "ma_settings": "5,10,20", 
        "note": ""
    })

def delete_stock(stock_id):
    st.session_state.MOCK_STOCKS = [s for s in st.session_state.MOCK_STOCKS if s['id'] != stock_id]

def update_stock_info(stock_id, new_symbol, new_name):
    for s in st.session_state.MOCK_STOCKS:
        if s['id'] == stock_id:
            s['symbol'] = new_symbol.upper()
            s['name'] = new_name
            break

def update_note(item_type, item_id, new_note):
    target_list = st.session_state.MOCK_GROUPS if item_type == 'group' else st.session_state.MOCK_STOCKS
    for item in target_list:
        if item['id'] == item_id:
            item['note'] = new_note
            return True
    return False

def update_stock_ma(stock_id, new_ma):
    for s in st.session_state.MOCK_STOCKS:
        if s['id'] == stock_id:
            s['ma_settings'] = new_ma
            return True
    return False

if 'active_note_id' not in st.session_state: st.session_state.active_note_id = None
if 'active_edit_id' not in st.session_state: st.session_state.active_edit_id = None

def get_groups(): return st.session_state.MOCK_GROUPS
def get_stocks_by_group(group_id): return [s for s in st.session_state.MOCK_STOCKS if s['group_id'] == group_id]

# ==========================================
# 3. 介面邏輯
# ==========================================
st.set_page_config(page_title="My Stock App", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* [修改] 稍微放寬頂部留白，避免被手機狀態列切到 */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 5rem !important;
    }
    
    /* 字體設定 */
    .big-header { font-size: 26px !important; font-weight: bold; margin-bottom: 0px !important; line-height: 1.2; }
    .big-price { font-size: 24px !important; margin-bottom: 0px !important; line-height: 1.2; }
    .detail-price-main { font-size: 28px !important; font-weight: bold; }
    .detail-price-change { font-size: 18px !important; font-weight: bold; margin-left: 10px; }
    
    .stock-up { color: #ff2b2b; }
    .stock-down { color: #00b800; }
    .stock-flat { color: gray; }
    
    /* 按鈕樣式 */
    .stButton > button {
        font-size: 20px !important;
        height: 2.8em !important;
        padding: 0px 5px !important;
        font-weight: bold !important;
        margin-top: 5px !important;
    }
    
    /* 輸入框 */
    .stTextArea textarea, .stTextInput input { font-size: 18px !important; }
    div[data-testid="column"] { gap: 0rem !important; }
    
    /* 刪除按鈕 */
    .delete-btn button {
        background-color: #ffcccc !important;
        color: #cc0000 !important;
        border: 1px solid #cc0000 !important;
    }
</style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = 'home'
if 'selected_group' not in st.session_state: st.session_state.selected_group = None
if 'selected_stock' not in st.session_state: st.session_state.selected_stock = None

# 讀取目前的編輯模式狀態
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
is_edit_mode = st.session_state.edit_mode

# --- 頁面 1: 首頁 (群組列表) ---
if st.session_state.page == 'home':
    st.title("📂 投資觀察群組")
    
    # 新增群組區塊
    if is_edit_mode:
        with st.expander("➕ 新增群組", expanded=True):
            new_group_name = st.text_input("群組名稱", placeholder="例如：美股科技股")
            if st.button("確認新增群組", use_container_width=True):
                if new_group_name:
                    add_group(new_group_name)
                    st.success(f"已新增 {new_group_name}")
                    st.rerun()
                else:
                    st.warning("請輸入名稱")
        st.write("---")

    groups = get_groups()
    executor = ThreadPoolExecutor(max_workers=5)
    
    for g in groups:
        stocks_in_group = get_stocks_by_group(g['id'])
        future_to_stock = {executor.submit(get_latest_quote_and_change, s['symbol']): s for s in stocks_in_group}
        total_pct = 0
        valid_count = 0
        for future in future_to_stock:
            try:
                _, pct = future.result()
                if pct is not None:
                    total_pct += pct
                    valid_count += 1
            except: pass
        
        avg_pct = (total_pct / valid_count) if valid_count > 0 else 0
        if avg_pct > 0: avg_display = f"<span class='stock-up'>▲ {avg_pct:.2f}%</span>"
        elif avg_pct < 0: avg_display = f"<span class='stock-down'>▼ {avg_pct:.2f}%</span>"
        else: avg_display = f"<span class='stock-flat'>- 0.00%</span>"

        with st.container(border=True):
            if is_edit_mode:
                col_text, col_action1, col_action2 = st.columns([4, 1.2, 1.2])
            else:
                col_text, col_action1, col_action2 = st.columns([5, 1.2, 1.2])
            
            with col_text:
                st.markdown(f"<div class='big-header'>{g['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='big-price'>平均: {avg_display}</div>", unsafe_allow_html=True)

            if is_edit_mode:
                with col_action1:
                    edit_key = f"edit_g_{g['id']}"
                    if st.button("✏️", key=f"btn_edit_g_{g['id']}", use_container_width=True):
                        st.session_state.active_edit_id = None if st.session_state.active_edit_id == edit_key else edit_key
                with col_action2:
                    if st.button("🗑️", key=f"btn_del_g_{g['id']}", use_container_width=True):
                        delete_group(g['id'])
                        st.rerun()
            else:
                with col_action1:
                    note_key = f"group_{g['id']}"
                    if st.button("筆記", key=f"btn_note_g_{g['id']}", use_container_width=True):
                        st.session_state.active_note_id = None if st.session_state.active_note_id == note_key else note_key
                with col_action2:
                    if st.button("進入", key=f"btn_enter_{g['id']}", use_container_width=True):
                        st.session_state.selected_group = g
                        st.session_state.page = 'group_detail'
                        st.session_state.active_note_id = None
                        st.rerun()
            
            # 隱藏區域
            if not is_edit_mode and st.session_state.active_note_id == f"group_{g['id']}":
                with st.container():
                    new_note = st.text_area("筆記", value=g.get('note', ''), key=f"txt_g_{g['id']}", label_visibility="collapsed")
                    if st.button("儲存筆記", key=f"save_g_{g['id']}"):
                        update_note('group', g['id'], new_note)
                        st.session_state.active_note_id = None
                        st.success("已儲存")
                        st.rerun()
            
            if is_edit_mode and st.session_state.active_edit_id == f"edit_g_{g['id']}":
                with st.container():
                    new_name_input = st.text_input("修改名稱", value=g['name'], key=f"inp_edit_g_{g['id']}")
                    if st.button("確認修改", key=f"cfm_edit_g_{g['id']}"):
                        update_group_name(g['id'], new_name_input)
                        st.session_state.active_edit_id = None
                        st.success("已更新")
                        st.rerun()
    
    executor.shutdown(wait=False)

    # 管理模式開關
    st.write("---")
    st.toggle("⚙️ 管理模式", key='edit_mode')


# --- 頁面 2: 個股列表 ---
elif st.session_state.page == 'group_detail':
    group = st.session_state.selected_group
    st.title(f"{group['name']}")
    
    if is_edit_mode:
        with st.expander("➕ 新增個股", expanded=True):
            col_add1, col_add2 = st.columns([1, 1])
            with col_add1:
                new_symbol = st.text_input("代號", placeholder="例如 2330.TW")
            with col_add2:
                new_stock_name = st.text_input("名稱", placeholder="例如 台積電")
            
            if st.button("確認新增個股", use_container_width=True):
                if new_symbol:
                    add_stock(group['id'], new_symbol, new_stock_name)
                    st.success(f"已新增 {new_symbol}")
                    st.rerun()
                else:
                    st.warning("請輸入代號")
        st.write("---")
    
    stocks = get_stocks_by_group(group['id'])
    
    for s in stocks:
        price, pct = get_latest_quote_and_change(s['symbol'])
        if price is not None:
            price_str = f"{price:.2f}"
            if pct > 0: pct_str = f"<span class='stock-up'>▲ {pct:.2f}%</span>"
            elif pct < 0: pct_str = f"<span class='stock-down'>▼ {pct:.2f}%</span>"
            else: pct_str = f"<span class='stock-flat'>0.00%</span>"
            display_info = f"<span class='big-price'>{price_str} | {pct_str}</span>"
        else:
            display_info = "<span class='big-price'>⏳ 載入中...</span>"

        with st.container(border=True):
            if is_edit_mode:
                col1, col_action1, col_action2 = st.columns([4, 1.2, 1.2])
            else:
                col1, col_action1, col_action2 = st.columns([5, 1.2, 1.2])
            
            with col1:
                if "TW" in s['symbol'].upper(): stock_display_name = f"{s['symbol']} {s.get('name', '')}"
                else: stock_display_name = f"{s['symbol']}"
                st.markdown(f"<div class='big-header'>{stock_display_name}</div>", unsafe_allow_html=True)
                st.markdown(display_info, unsafe_allow_html=True)
            
            if is_edit_mode:
                with col_action1:
                    edit_key = f"edit_s_{s['id']}"
                    if st.button("✏️", key=f"btn_edit_s_{s['id']}", use_container_width=True):
                         st.session_state.active_edit_id = None if st.session_state.active_edit_id == edit_key else edit_key
                with col_action2:
                    if st.button("🗑️", key=f"btn_del_s_{s['id']}", use_container_width=True):
                        delete_stock(s['id'])
                        st.rerun()
            else:
                with col_action1:
                    note_key = f"stock_{s['id']}"
                    if st.button("筆記", key=f"btn_note_s_{s['id']}", use_container_width=True):
                        st.session_state.active_note_id = None if st.session_state.active_note_id == note_key else note_key
                with col_action2:
                    if st.button("分析", key=f"btn_ana_{s['id']}", use_container_width=True):
                        st.session_state.selected_stock = s
                        st.session_state.page = 'stock_detail'
                        st.session_state.active_note_id = None
                        st.rerun()

            if not is_edit_mode and st.session_state.active_note_id == f"stock_{s['id']}":
                st.write("---")
                new_note = st.text_area("筆記", value=s.get('note', ''), key=f"txt_s_{s['id']}", label_visibility="collapsed")
                if st.button("儲存筆記", key=f"save_s_{s['id']}"):
                    update_note('stock', s['id'], new_note)
                    st.session_state.active_note_id = None
                    st.success("已儲存")
                    st.rerun()
            
            if is_edit_mode and st.session_state.active_edit_id == f"edit_s_{s['id']}":
                 with st.container():
                    edit_sym = st.text_input("代號", value=s['symbol'], key=f"ed_sym_{s['id']}")
                    edit_nam = st.text_input("名稱", value=s.get('name',''), key=f"ed_nam_{s['id']}")
                    if st.button("確認修改", key=f"cfm_edit_s_{s['id']}"):
                        update_stock_info(s['id'], edit_sym, edit_nam)
                        st.session_state.active_edit_id = None
                        st.success("已更新")
                        st.rerun()
    
    # 底部區域
    st.write("---")
    st.toggle("⚙️ 管理模式", key='edit_mode')
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ 返回群組列表", use_container_width=True):
        st.session_state.page = 'home'
        st.session_state.active_note_id = None
        st.rerun()

# --- 頁面 3: K線圖詳細頁 ---
elif st.session_state.page == 'stock_detail':
    stock = st.session_state.selected_stock
    
    if "TW" in stock['symbol'].upper(): title_str = f"{stock['symbol']} {stock.get('name', '')}"
    else: title_str = f"{stock['symbol']}"
    st.title(title_str)
    
    try:
        with st.spinner('資料下載中...'):
            df = fetch_stock_data_direct(stock['symbol'], range_str="6mo")
            
        if df is None or df.empty:
            st.error(f"❌ 無法取得 {stock['symbol']} 資料。")
        else:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            price = latest['Close']
            change = price - prev['Close']
            pct = (change / prev['Close']) * 100
            
            sign = "+" if change > 0 else ""
            color_class = "stock-up" if change > 0 else ("stock-down" if change < 0 else "stock-flat")
            
            price_html = f"""
            <div style='margin-bottom: 10px;'>
                <span class='detail-price-main'>{price:.2f}</span>
                <span class='detail-price-change {color_class}'>{sign}{change:.2f} ({sign}{pct:.2f}%)</span>
            </div>
            """
            st.markdown(price_html, unsafe_allow_html=True)
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name='K線', increasing_line_color='red', increasing_fillcolor='red',
                decreasing_line_color='green', decreasing_fillcolor='green'
            ))
            
            ma_list = [int(x.strip()) for x in stock['ma_settings'].split(',') if x.strip().isdigit()]
            colors = ['#FFA500', '#0000FF', '#800080', '#008000']
            for i, ma_day in enumerate(ma_list):
                ma_values = df['Close'].rolling(window=ma_day).mean()
                color = colors[i % len(colors)]
                fig.add_trace(go.Scatter(x=df.index, y=ma_values, line=dict(color=color, width=1.5), name=f'MA {ma_day}'))

            fig.update_layout(
                height=450, xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.02, x=0)
            )
            st.plotly_chart(fig, use_container_width=True)

            st.write("") 
            col_input, col_save = st.columns([1, 1]) 
            with col_input:
                new_ma = st.text_input("MA設定", value=stock['ma_settings'], label_visibility="collapsed")
            with col_save:
                if st.button("更新均線", use_container_width=True):
                    update_stock_ma(stock['id'], new_ma)
                    st.success("OK")
                    st.rerun()

    except Exception as e:
        st.error(f"發生未預期的錯誤: {e}")

    st.write("---")
    if st.button(f"⬅️ 返回 {st.session_state.selected_group['name']}", use_container_width=True):
        st.session_state.page = 'group_detail'
        st.rerun()

















