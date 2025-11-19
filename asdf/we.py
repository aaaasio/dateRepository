import streamlit as st
import pandas as pd
import plotly.express as px


@st.cache_data
def load_and_melt(filename, id_vars):
    df = pd.read_csv(filename, encoding='utf-8')
    df_melted = df.melt(
        id_vars=id_vars,
        var_name='년도',
        value_name='값'
    )
    df_melted['년도'] = pd.to_numeric(df_melted['년도'], errors='coerce')
    df_melted = df_melted.dropna(subset=['년도'])
    return df_melted


file_paths = {
    "성 및 연령별 추계인구 (전국)": ("성및연령별추계인구_전국_정리됨_cleaned.csv", ['가정별', '성별', '연령']),
    "성 및 연령별 추계인구 (시도)": ("성및연령별추계인구_시도_정리됨_cleaned.csv", ['시나리오별', '지역', '성별', '연령']),
}


st.sidebar.title("설정")

dataset_name = st.sidebar.selectbox("데이터셋 선택", list(file_paths.keys()))
file_path, id_vars = file_paths[dataset_name]

df = load_and_melt(file_path, id_vars)

st.sidebar.subheader("연도 선택")
min_year, max_year = int(df["년도"].min()), int(df["년도"].max())
selected_year = st.sidebar.slider("연도", min_year, max_year, max_year)

filters = {}
for col in id_vars:
    options = df[col].dropna().unique()

    if col == "연령":
        options = [opt for opt in options if opt != "계"]

    # ✅ 수정 부분 시작 — 가정별, 시나리오별, 지역은 selectbox 사용
    if col in ["가정별", "시나리오별", "지역"]:
        selected = st.sidebar.selectbox(f"{col} 선택", options)
        filters[col] = [selected]
    else:
        if len(options) < 50:
            selected = st.sidebar.multiselect(f"{col} 선택", options, default=options[:1])
            filters[col] = selected
    # ✅ 수정 부분 끝


df_filtered = df.copy()

for col, values in filters.items():
    if values:
        if col == "연령":
            df_filtered = df_filtered[df_filtered[col].isin(values + ["계"])]
        else:
            df_filtered = df_filtered[df_filtered[col].isin(values)]

df_filtered = df_filtered[df_filtered["년도"] == selected_year]

st.title("대한민국 추계인구 대시보드")
with st.expander("추계인구란 (더보기)", expanded=False):
    st.markdown("""
#### 추계인구란?
추계인구는 인구총조사 결과를 바탕으로 **출생, 사망, 국제 이동 등 인구 변동 요인**을 반영하여  현재 시점의 인구를 **추정**한 값입니다. 이는 실제 인구를 조사하는 것이 아니라,  통계적 추정을 통해 인구 변화를 파악하는 방법입니다.  

추계는 **중위·고위·저위**의 세 가지 시나리오로 나뉘며,  각각의 시나리오는 인구 변동 요인(출생률, 사망률, 이동률)의 미래 수준을 다르게 가정합니다.

- **중위 시나리오**: 인구가 중간 수준으로 변동한다고 가정  
- **고위 시나리오**: 인구가 가장 많이 증가하는 경우  
- **저위 시나리오**: 인구가 가장 적게 증가하는 경우  

이를 통해 인구 변화의 다양한 가능성을 예측하고 정책 수립에 참고할 수 있습니다.
""")
st.divider()

total_pop = df_filtered[df_filtered["연령"] == "계"]["값"].sum()

if pd.notna(total_pop) and total_pop > 0:
    total_display = f"{total_pop:,.0f}명"
    st.markdown(f"데이터셋: {dataset_name} ｜ 연도: {selected_year} ｜ 총인구: {total_display}")
else:
    st.markdown(f"데이터셋: {dataset_name} ｜ 연도: {selected_year}")

if df_filtered.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

if "성별" in df_filtered.columns or "성" in df_filtered.columns:
    gender_col = "성별" if "성별" in df_filtered.columns else "성"
    df_pyramid = df_filtered.copy()

    df_pyramid = df_pyramid[df_pyramid["연령"] != "계"]

    age_order = [
        "0 0 4세", "5 0 9세", "10 0 14세", "15 0 19세",
        "20 0 24세", "25 0 29세", "30 0 34세", "35 0 39세",
        "40 0 44세", "45 0 49세", "50 0 54세", "55 0 59세",
        "60 0 64세", "65 0 69세", "70 0 74세", "75 0 79세",
        "80 0 84세", "85 0 89세", "90 0 94세", "95 0 99세", "100세 이상"
    ]
    df_pyramid = df_pyramid[df_pyramid["연령"].isin(age_order)]
    df_pyramid["연령"] = pd.Categorical(df_pyramid["연령"], categories=age_order, ordered=True)

    color_map = {"남자": "#1f77b4", "남": "#1f77b4", "여자": "#ff69b4", "여": "#ff69b4"}

    fig_pyramid = px.bar(
        df_pyramid.sort_values("연령"),
        x="값",
        y="연령",
        color=gender_col,
        orientation="h",
        title=f"{selected_year}년 {dataset_name} 인구 그래프",
        color_discrete_map=color_map
    )

    fig_pyramid.update_layout(
        xaxis_title="인구수",
        yaxis_title="연령",
        bargap=0.05,
        showlegend=True,
        legend_title=gender_col,
    )

    st.plotly_chart(fig_pyramid, use_container_width=True)

elif "지역" in df_filtered.columns:
    st.subheader("시도별 인구 비교")

    fig_region = px.bar(
        df_filtered,
        x="지역",
        y="값",
        color="시나리오별" if "시나리오별" in df_filtered.columns else None,
        barmode="group",
        title=f"{selected_year}년 시도별 인구 현황"
    )
    st.plotly_chart(fig_region, use_container_width=True)

st.divider()
st.subheader("데이터")
st.dataframe(df_filtered.head(200))
st.divider()
st.text("데이터 출저")
st.markdown("[KOSIS 국가통계포털](https://kosis.kr/index/index.do)")
