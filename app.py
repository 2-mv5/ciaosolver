import streamlit as st
import pandas as pd

# --- 設定 ---
st.set_page_config(page_title="チャオチャオ HU", layout="centered")

def calculate_gto(s_pos, r_pos):
    TRUE_AMT = 1.0
    LIE_AMT = 2.0
    NUMS = [4, 3, 2, 1]

    # 1. 嘘の配分 (相手EV基準)
    lie_alloc = {n: 0.0 for n in NUMS}
    
    if r_pos > 0:
        rem = LIE_AMT
        for m in NUMS:
            reward = s_pos + m
            loss_ratio = r_pos / (reward + r_pos)
            capacity = loss_ratio / (1.0 - loss_ratio)
            amount = min(rem, capacity)
            lie_alloc[m] = amount
            rem -= amount
        if rem > 0: lie_alloc[1] += rem
    else:
        if s_pos > 0: lie_alloc[1] = LIE_AMT
        else: 
            for m in NUMS: lie_alloc[m] = LIE_AMT / 4

    # 2. データ生成

　　# 2. データ生成
    results = []
    total_sender_ev = 0.0
    total_doubt_prob = 0.0  # ★追加: 集計用変数

    for m in NUMS:
        total_tokens = TRUE_AMT + lie_alloc[m]
        fake_prob = (lie_alloc[m] / total_tokens) if total_tokens > 0 else 0
        alloc_pct = (lie_alloc[m] / LIE_AMT) * 100
        
        receiver_ev = (fake_prob * (s_pos + m)) - ((1.0 - fake_prob) * r_pos)

        if receiver_ev > 0.001: doubt = 100.0
        elif receiver_ev < -0.001: doubt = 0.0
        else:
            if lie_alloc[m] < 1e-4: doubt = 0.0
            else:
                doubt = (m / (s_pos + 2*m)) * 100.0

        pass_prob = 1.0 - (doubt / 100.0)
        relative_loss = s_pos + m
        true_ev = m
        lie_outcome = (m * pass_prob) + (-relative_loss * (doubt / 100.0))
        
        term_ev = (true_ev * (1/6)) + (lie_outcome * (2/6) * (lie_alloc[m]/LIE_AMT))
        total_sender_ev += term_ev
        display_ev = (true_ev * (TRUE_AMT/total_tokens)) + (lie_outcome * (lie_alloc[m]/total_tokens))
        
        # ★追加: 全体被ダウト率の計算
        # その数字を宣言する確率 = 正直(1/6) + 嘘(2/6 * 配分率)
        prob_declaring_m = (1/6) + ((2/6) * (lie_alloc[m] / LIE_AMT))
        total_doubt_prob += prob_declaring_m * (doubt / 100.0)
        
        r_ev_val = receiver_ev if abs(receiver_ev) > 0.005 else 0.00

        results.append({
            "宣言": m,
            "嘘の配分割合": f"{alloc_pct:.1f}%",
            "数字が嘘の確率": f"{fake_prob*100:.1f}%",
            "自分EV": f"{display_ev:.2f}歩",
            "ダウト宣言率": f"{doubt:.1f}%",
            "相手EV": f"{r_ev_val:+.2f}歩" if r_ev_val != 0 else "0.00歩"
        })
    return results, total_sender_ev, (total_doubt_prob * 100.0)
# --- UI構築 ---
st.title("🎲 チャオチャオ HU")
st.caption("")

col1, col2 = st.columns(2)
with col1:
    s_pos = st.number_input("自分のマス数", min_value=0, value=0, step=1)
with col2:
    r_pos = st.number_input("相手のマス数", min_value=0, value=0, step=1)

if st.button("計算する", type="primary"):
    # ★変更: 3つの値を受け取る
    data, total_ev, total_doubt = calculate_gto(s_pos, r_pos)
    
    # ★追加: 重要な数字を並べて表示 (Metric)
    m1, m2 = st.columns(2)
    m1.metric("総合期待値", f"{total_ev:+.2f} 歩/ターン")
    m2.metric("被ダウト率 (全体)", f"{total_doubt:.1f} %")
    
 # テーブル表示 (行番号を隠す)
    df = pd.DataFrame(data)
    # st.tableの代わりにdataframeを使い、hide_index=Trueにする
    st.dataframe(df, hide_index=True, use_container_width=True)
    
    # 結果表示
    st.success(f"あなたの総合期待値: **{total_ev:+.2f} 歩/ターン**")
    
