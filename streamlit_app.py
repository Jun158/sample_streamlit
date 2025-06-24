# streamlit_app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ページの設定
st.set_page_config(
    page_title="Sales Data Dashboard",
    page_icon="📊",
    layout="wide"
)

# タイトル
st.title("📊 Sales Data Dashboard")
st.markdown("---")

# サイドバーでファイルアップロード
st.sidebar.header("データの読み込み")
uploaded_file = st.sidebar.file_uploader(
    "CSVファイルをアップロードしてください", 
    type=['csv']
)

# デフォルトファイルまたはアップロードファイルの処理
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    # デフォルトのサンプルデータを使用
    try:
        df = pd.read_csv('sample_data.csv')
        st.sidebar.info("サンプルデータを使用しています")
    except FileNotFoundError:
        st.error("sample_data.csv が見つかりません。ファイルをアップロードしてください。")
        st.stop()

# データの前処理
df['date'] = pd.to_datetime(df['date'])

# サイドバーでフィルタリングオプション
st.sidebar.header("フィルタリング")

# 日付範囲の選択
date_range = st.sidebar.date_input(
    "日付範囲を選択",
    value=(df['date'].min(), df['date'].max()),
    min_value=df['date'].min(),
    max_value=df['date'].max()
)

# カテゴリの選択
categories = st.sidebar.multiselect(
    "カテゴリを選択",
    options=df['category'].unique(),
    default=df['category'].unique()
)

# 地域の選択
regions = st.sidebar.multiselect(
    "地域を選択",
    options=df['region'].unique(),
    default=df['region'].unique()
)

# データのフィルタリング
if len(date_range) == 2:
    mask = (
        (df['date'] >= pd.to_datetime(date_range[0])) &
        (df['date'] <= pd.to_datetime(date_range[1])) &
        (df['category'].isin(categories)) &
        (df['region'].isin(regions))
    )
    filtered_df = df[mask]
else:
    filtered_df = df[
        (df['category'].isin(categories)) &
        (df['region'].isin(regions))
    ]

# メインコンテンツ
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="総売上",
        value=f"¥{filtered_df['sales'].sum():,}",
        delta=f"{len(filtered_df)} レコード"
    )

with col2:
    st.metric(
        label="平均売上",
        value=f"¥{filtered_df['sales'].mean():.0f}",
        delta=f"{filtered_df['sales'].std():.0f} 標準偏差"
    )

with col3:
    st.metric(
        label="総利益",
        value=f"¥{filtered_df['profit'].sum():,}",
        delta=f"{filtered_df['profit'].mean():.0f} 平均"
    )

with col4:
    st.metric(
        label="利益率",
        value=f"{(filtered_df['profit'].sum() / filtered_df['sales'].sum() * 100):.1f}%"
    )

st.markdown("---")

# グラフの表示
tab1, tab2, tab3, tab4 = st.tabs(["📈 時系列分析", "📊 カテゴリ分析", "🗺️ 地域分析", "🔍 詳細分析"])

with tab1:
    st.subheader("売上の時系列推移")
    
    # Plotlyを使った時系列グラフ
    fig_time = px.line(
        filtered_df, 
        x='date', 
        y='sales',
        title='売上推移',
        labels={'sales': '売上', 'date': '日付'}
    )
    fig_time.update_layout(height=400)
    st.plotly_chart(fig_time, use_container_width=True)
    
    # 移動平均の追加オプション
    if st.checkbox("移動平均を表示"):
        window = st.slider("移動平均の期間", 3, 30, 7)
        filtered_df_sorted = filtered_df.sort_values('date')
        filtered_df_sorted['moving_avg'] = filtered_df_sorted['sales'].rolling(window=window).mean()
        
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(
            x=filtered_df_sorted['date'],
            y=filtered_df_sorted['sales'],
            mode='lines',
            name='売上',
            line=dict(color='blue', width=1)
        ))
        fig_ma.add_trace(go.Scatter(
            x=filtered_df_sorted['date'],
            y=filtered_df_sorted['moving_avg'],
            mode='lines',
            name=f'{window}日移動平均',
            line=dict(color='red', width=2)
        ))
        fig_ma.update_layout(title=f'売上推移と{window}日移動平均', height=400)
        st.plotly_chart(fig_ma, use_container_width=True)

with tab2:
    st.subheader("カテゴリ別分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # カテゴリ別売上
        category_sales = filtered_df.groupby('category')['sales'].sum().reset_index()
        fig_cat = px.bar(
            category_sales,
            x='category',
            y='sales',
            title='カテゴリ別売上',
            color='sales',
            color_continuous_scale='viridis'
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        # カテゴリ別利益率
        category_profit = filtered_df.groupby('category').agg({
            'sales': 'sum',
            'profit': 'sum'
        }).reset_index()
        category_profit['profit_rate'] = (category_profit['profit'] / category_profit['sales'] * 100)
        
        fig_profit = px.pie(
            category_profit,
            values='profit',
            names='category',
            title='カテゴリ別利益分布'
        )
        st.plotly_chart(fig_profit, use_container_width=True)

with tab3:
    st.subheader("地域別分析")
    
    # 地域別の売上と利益
    region_data = filtered_df.groupby('region').agg({
        'sales': ['sum', 'mean'],
        'profit': ['sum', 'mean']
    }).round(2)
    
    st.dataframe(region_data, use_container_width=True)
    
    # 地域別散布図
    fig_region = px.scatter(
        filtered_df,
        x='sales',
        y='profit',
        color='region',
        size='sales',
        title='地域別 売上 vs 利益',
        labels={'sales': '売上', 'profit': '利益'}
    )
    st.plotly_chart(fig_region, use_container_width=True)

with tab4:
    st.subheader("詳細分析")
    
    # 相関関係の表示
    st.write("**数値データの相関関係**")
    corr_matrix = filtered_df[['sales', 'profit']].corr()
    fig_corr = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        title="相関行列"
    )
    st.plotly_chart(fig_corr, use_container_width=True)
    
    # 生データの表示
    st.write("**フィルタリングされたデータ**")
    st.dataframe(filtered_df, use_container_width=True)
    
    # データのダウンロード
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="フィルタリングされたデータをCSVでダウンロード",
        data=csv,
        file_name=f'filtered_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv'
    )

# フッター
st.markdown("---")
st.markdown("*このダッシュボードはStreamlitで作成されました*")
