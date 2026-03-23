"""
Streamlit 资金流水分析系统 - 主程序
优化版本：模块化、缓存优化、异常处理增强
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import warnings

warnings.filterwarnings('ignore')

# ==================== 路径配置 ====================
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from utils.data_loader import merge_multiple_files, validate_data
from utils.analyzer import FundAnalyzer
from utils.visualizer import show_advanced_charts, show_fraud_network

# ==================== 常量配置 ====================
class Config:
    """应用配置常量"""
    # 页面配置
    PAGE_TITLE = "💰 资金流水智能分析系统"
    PAGE_ICON = "💰"
    
    # 分析阈值
    DEFAULT_AMOUNT_THRESHOLD = 10000
    NIGHT_START_HOUR = 22
    NIGHT_END_HOUR = 6
    RAPID_TRANSACTION_WINDOW = 5  # 分钟
    
    # 图表配色
    COLOR_INCOME = "#2ecc71"      # 绿色-收入
    COLOR_EXPENSE = "#e74c3c"     # 红色-支出
    COLOR_FRAUD = "#ff4757"       # 深红-涉诈
    COLOR_WARNING = "#ffa502"     # 橙色-警告
    COLOR_PRIMARY = "#667eea"     # 主色-紫蓝
    
    # 分页设置
    PAGE_SIZE = 100
    
    # 支持的文件类型
    SUPPORTED_TYPES = ['xlsx', 'xls', 'csv']


# ==================== CSS 样式 ====================
STYLES = """
<style>
    /* 全局字体 */
    html, body, [class*="css"] {
        font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
    }
    
    /* 主标题渐变 */
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    
    /* 副标题 */
    .sub-title {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid {primary};
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    /* 涉诈警告动画 */
    .fraud-alert {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        font-weight: bold;
        text-align: center;
        animation: pulse 2s ease-in-out infinite;
        margin: 1rem 0;
    }
    
    @keyframes pulse {
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.4); }}
        50% {{ box-shadow: 0 0 20px 10px rgba(255, 107, 107, 0.2); }}
    }
    
    /* 信息卡片 */
    .info-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
    }
    
    /* 风险等级标签 */
    .risk-high { 
        background: #ff4757; 
        color: white; 
        padding: 4px 12px; 
        border-radius: 20px; 
        font-size: 0.85rem;
        font-weight: bold;
    }
    
    .risk-medium { 
        background: #ffa502; 
        color: white; 
        padding: 4px 12px; 
        border-radius: 20px; 
        font-size: 0.85rem;
        font-weight: bold;
    }
    
    .risk-low { 
        background: #2ed573; 
        color: white; 
        padding: 4px 12px; 
        border-radius: 20px; 
        font-size: 0.85rem;
        font-weight: bold;
    }
    
    /* 表格优化 */
    .dataframe {
        font-size: 0.9rem !important;
    }
    
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #f8f9fa;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        background: {primary};
    }
    
    /* 下载按钮 */
    .stDownloadButton button {
        background: linear-gradient(90deg, {primary} 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
    }
    
    /* 页脚 */
    .footer {
        text-align: center;
        color: #666;
        padding: 2rem 1rem;
        margin-top: 2rem;
        border-top: 1px solid #eee;
    }
</style>
""".format(primary=Config.COLOR_PRIMARY)


# ==================== 页面初始化 ====================
def init_page():
    """初始化页面配置"""
    st.set_page_config(
        page_title=Config.PAGE_TITLE,
        page_icon=Config.PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/fund-analyzer',
            'Report a bug': 'https://github.com/fund-analyzer/issues',
            'About': '资金流水分析系统 v1.0 - 支持支付宝、微信、银行流水智能分析'
        }
    )
    st.markdown(STYLES, unsafe_allow_html=True)


# ==================== 侧边栏组件 ====================
def render_sidebar() -> Tuple[List, float, bool]:
    """
    渲染侧边栏
    
    Returns:
        (上传的文件列表, 大额阈值, 是否仅显示涉诈)
    """
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem 0;'>
            <div style='font-size: 3.5rem; margin-bottom: 0.5rem;'>💰</div>
            <h2 style='margin: 0; color: {primary}; font-weight: bold;'>资金分析专家</h2>
            <p style='color: #888; margin-top: 0.5rem; font-size: 0.9rem;'>智能识别 · 深度分析 · 涉诈预警</p>
        </div>
        """.format(primary=Config.COLOR_PRIMARY), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 文件上传
        st.header("📁 数据上传")
        
        uploaded_files = st.file_uploader(
            "选择流水文件（支持多选）",
            type=Config.SUPPORTED_TYPES,
            accept_multiple_files=True,
            help="支持支付宝、微信、银行流水文件，可同时上传多个"
        )
        
        st.markdown("---")
        
        # 分析设置
        st.header("⚙️ 分析设置")
        
        col1, col2 = st.columns(2)
        with col1:
            amount_threshold = st.number_input(
                "大额阈值（元）",
                min_value=1000,
                max_value=1000000,
                value=Config.DEFAULT_AMOUNT_THRESHOLD,
                step=5000,
                help="超过此金额的交易将被高亮显示"
            )
        with col2:
            show_fraud_only = st.checkbox(
                "仅涉诈",
                value=False,
                help="只展示标记为涉诈的交易"
            )
        
        # 高级设置
        with st.expander("🔧 高级设置"):
            night_start = st.slider("夜间开始", 18, 24, Config.NIGHT_START_HOUR)
            night_end = st.slider("夜间结束", 0, 8, Config.NIGHT_END_HOUR)
            st.session_state['night_hours'] = (night_start, night_end)
        
        st.markdown("---")
        
        # 使用说明
        with st.expander("ℹ️ 使用说明"):
            st.markdown("""
            **📱 支付宝**
            - 路径：我的 → 账单 → 导出
            - 支持：Excel (.xlsx)
            
            **💬 微信**
            - 路径：服务 → 钱包 → 账单 → 下载
            - 支持：Excel (.xlsx)
            
            **🏦 银行**
            - 路径：网银 → 交易明细 → 导出
            - 支持：Excel (.xls/.xlsx)
            """)
        
        # 重置按钮
        if st.button("🔄 重置分析", use_container_width=True, type="secondary"):
            st.cache_data.clear()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # 版本信息
        st.markdown("---")
        st.caption("v1.0.0 | © 2024 资金分析系统")
    
    return uploaded_files, amount_threshold, show_fraud_only


# ==================== 数据加载（带缓存） ====================
@st.cache_data(ttl=3600, show_spinner=False)
def load_data_cached(files: Tuple) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    缓存加载数据
    
    Args:
        files: 上传的文件元组（hashable）
    
    Returns:
        (合并后的DataFrame, 文件信息列表)
    """
    # 转换回列表
    file_list = list(files)
    
    with st.spinner("🔄 正在解析数据文件..."):
        df, info = merge_multiple_files(file_list)
    
    return df, info


def render_file_info(file_info: List[Dict]):
    """渲染文件加载信息"""
    st.subheader("📊 已加载文件")
    
    total_records = sum(info.get('records', 0) for info in file_info if info.get('type') != 'error')
    
    cols = st.columns(min(len(file_info), 4))
    for idx, info in enumerate(file_info):
        col = cols[idx % 4]
        with col:
            if info['type'] == 'error':
                st.error(f"❌ **{info['name']}**\n\n{info.get('error', '加载失败')[:50]}...")
            else:
                source_emoji = {'alipay': '📱', 'wechat': '💬', 'bank': '🏦'}.get(info['type'], '📄')
                st.success(
                    f"{source_emoji} **{info['name'][:20]}**" + 
                    ("..." if len(info['name']) > 20 else "") +
                    f"\n\n{info['type'].upper()} · {info['records']:,} 条"
                )
    
    st.caption(f"共计 **{len(file_info)}** 个文件，**{total_records:,}** 条记录")


# ==================== 核心指标卡片 ====================
def render_metrics(stats: Dict, amount_threshold: float):
    """渲染核心指标卡片"""
    st.subheader("📈 核心指标概览")
    
    # 计算同比/环比（模拟）
    fraud_warning = stats['fraud_count'] > 0
    net_positive = stats['net_flow'] >= 0
    
    metrics_data = [
        ("📋 总交易笔数", f"{stats['total_records']:,}", None, "笔"),
        ("💵 总收入", f"¥{stats['total_income']:,.0f}", 
         f"日均 ¥{stats.get('avg_daily_income', 0):,.0f}", "income"),
        ("💸 总支出", f"¥{stats['total_expense']:,.0f}", 
         f"日均 ¥{stats.get('avg_daily_expense', 0):,.0f}", "expense"),
        ("📊 净流量", f"¥{stats['net_flow']:+,.0f}", 
         "盈余" if net_positive else "赤字", "net"),
        ("🚨 涉诈交易", f"{stats['fraud_count']} 笔", 
         f"¥{stats['fraud_amount']:,.0f}" if stats['fraud_count'] > 0 else None, "fraud"),
        ("🏦 数据源", f"{len(stats['sources'])} 个", 
         f"{stats['accounts']} 个账户", None)
    ]
    
    cols = st.columns(6)
    for col, (label, value, delta, mtype) in zip(cols, metrics_data):
        with col:
            # 涉诈警告样式
            if mtype == "fraud" and stats['fraud_count'] > 0:
                st.metric(label=label, value=value, delta=delta, delta_color="inverse")
            elif mtype == "net":
                st.metric(label=label, value=value, delta=delta, 
                         delta_color="normal" if net_positive else "inverse")
            elif mtype == "expense":
                st.metric(label=label, value=value, delta=delta, delta_color="off")
            else:
                st.metric(label=label, value=value, delta=delta)
    
    # 涉诈警告横幅
    if fraud_warning:
        st.markdown(f"""
        <div class="fraud-alert">
            ⚠️ 警告：发现 {stats['fraud_count']} 笔涉诈交易，涉及金额 ¥{stats['fraud_amount']:,.2f}
        </div>
        """, unsafe_allow_html=True)


# ==================== 图表生成函数 ====================
def create_trend_chart(daily_data: pd.DataFrame) -> go.Figure:
    """创建资金趋势图"""
    fig = go.Figure()
    
    if 'income' in daily_data.columns and daily_data['income'].sum() > 0:
        fig.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['income'],
            name='💰 收入',
            fill='tozeroy',
            fillcolor='rgba(46, 204, 113, 0.2)',
            line=dict(color=Config.COLOR_INCOME, width=2),
            hovertemplate='日期: %{x}<br>收入: ¥%{y:,.0f}<extra></extra>'
        ))
    
    if 'expense' in daily_data.columns and daily_data['expense'].sum() > 0:
        fig.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['expense'],
            name='💸 支出',
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.2)',
            line=dict(color=Config.COLOR_EXPENSE, width=2),
            hovertemplate='日期: %{x}<br>支出: ¥%{y:,.0f}<extra></extra>'
        ))
    
    if 'net' in daily_data.columns:
        fig.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['net'],
            name='📊 净流入',
            mode='lines',
            line=dict(color=Config.COLOR_PRIMARY, width=2, dash='dot'),
            hovertemplate='日期: %{x}<br>净流入: ¥%{y:+,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title={
            'text': "📈 资金流入流出趋势",
            'x': 0.5,
            'font': {'size': 16, 'color': '#333'}
        },
        xaxis_title="日期",
        yaxis_title="金额（元）",
        hovermode='x unified',
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Microsoft YaHei")
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')
    
    return fig


def create_heatmap(hourly_data: pd.DataFrame) -> go.Figure:
    """创建时段热力图"""
    pivot_data = hourly_data.pivot(
        index='hour', 
        columns='direction', 
        values='count'
    ).fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=['支出' if c == 'expense' else '收入' if c == 'income' else c 
           for c in pivot_data.columns],
        y=pivot_data.index,
        colorscale='YlOrRd',
        hovertemplate='时段: %{y}:00<br>%{x}<br>交易数: %{z}<extra></extra>'
    ))
    
    # 添加夜间标记
    night_hours = st.session_state.get('night_hours', (Config.NIGHT_START_HOUR, Config.NIGHT_END_HOUR))
    fig.add_hrect(y0=night_hours[0], y1=24, fillcolor="gray", opacity=0.1, 
                  annotation_text="夜间", annotation_position="right")
    fig.add_hrect(y0=0, y1=night_hours[1], fillcolor="gray", opacity=0.1)
    
    fig.update_layout(
        title="🌡️ 24小时交易热力图",
        xaxis_title="",
        yaxis_title="小时",
        height=350,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_counterparty_chart(top_cp: pd.DataFrame) -> go.Figure:
    """创建对手方分析图"""
    fig = px.bar(
        top_cp.head(10),
        x='total_amount',
        y='counterparty',
        orientation='h',
        title="💰 TOP10 支出对手方",
        color='fraud_count',
        color_continuous_scale='Reds',
        text=top_cp.head(10)['percentage'].apply(lambda x: f'{x:.1f}%'),
        height=400
    )
    
    fig.update_traces(
        textposition='outside',
        hovertemplate='对手方: %{y}<br>金额: ¥%{x:,.0f}<br>涉诈: %{marker.color}笔<extra></extra>'
    )
    
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_title="交易金额（元）",
        yaxis_title="",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_type_pie(type_dist: pd.Series) -> go.Figure:
    """创建交易类型饼图"""
    fig = px.pie(
        values=type_dist.values,
        names=type_dist.index,
        title="📊 交易类型分布",
        hole=0.5,
        height=400
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>笔数: %{value}<br>占比: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=False,
        annotations=[dict(text='交易类型', x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    
    return fig


# ==================== 标签页组件 ====================
def tab_trend_analysis(analyzer: FundAnalyzer):
    """趋势分析标签页"""
    st.subheader("⏰ 时间维度分析")
    
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        daily_data = analyzer.daily_trend()
        fig = create_trend_chart(daily_data)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        hourly = analyzer.hourly_distribution()
        fig = create_heatmap(hourly)
        st.plotly_chart(fig, use_container_width=True)
        
        # 夜间交易统计
        night_hours = st.session_state.get('night_hours', (Config.NIGHT_START_HOUR, Config.NIGHT_END_HOUR))
        night = analyzer.detect_night_transactions(night_hours[0], night_hours[1])
        if night['count'] > 0:
            st.warning(
                f"🌙 夜间交易（{night_hours[0]}:00-{night_hours[1]}:00）："
                f"**{night['count']}** 笔，¥**{night['amount']:,.0f}** "
                f"(占比 {night['percentage_of_total']:.1f}%)"
            )
    
    # 月度趋势（如果有跨月数据）
    monthly = analyzer.monthly_trend()
    if len(monthly) > 1:
        st.markdown("#### 📅 月度趋势")
        fig_month = go.Figure()
        fig_month.add_trace(go.Bar(
            x=monthly['month_str'], y=monthly['income'],
            name='收入', marker_color=Config.COLOR_INCOME
        ))
        fig_month.add_trace(go.Bar(
            x=monthly['month_str'], y=monthly['expense'],
            name='支出', marker_color=Config.COLOR_EXPENSE
        ))
        fig_month.update_layout(
            barmode='group',
            height=300,
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_month, use_container_width=True)


def tab_counterparty_analysis(analyzer: FundAnalyzer, df: pd.DataFrame):
    """对手方分析标签页"""
    st.subheader("👤 资金流向分析")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        top_cp = analyzer.counterparty_analysis(top_n=10)
        if not top_cp.empty:
            fig = create_counterparty_chart(top_cp)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无支出数据")
    
    with col_b:
        type_dist = df['trans_type'].value_counts().head(8)
        if not type_dist.empty:
            fig = create_type_pie(type_dist)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无交易类型数据")
    
    # 对手方详细表格
    st.markdown("### 📋 对手方明细")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        min_trans = st.number_input("最少交易次数", 1, 100, 1)
    with col2:
        min_amount = st.slider("最小金额筛选", 0, int(top_cp['total_amount'].max()) if not top_cp.empty else 100000, 0, 1000)
    
    if not top_cp.empty:
        filtered_cp = top_cp[
            (top_cp['total_amount'] >= min_amount) & 
            (top_cp['trans_count'] >= min_trans)
        ]
        
        # 高亮涉诈行
        def highlight_fraud(row):
            if row['fraud_count'] > 0:
                return ['background: linear-gradient(90deg, #ffcccc 0%, #ffeaea 100%)'] * len(row)
            return [''] * len(row)
        
        styled_df = filtered_cp.style.apply(highlight_fraud, axis=1).format({
            'total_amount': '¥{:,.0f}',
            'avg_amount': '¥{:,.0f}',
            'max_amount': '¥{:,.0f}',
            'percentage': '{:.1f}%',
            'freq_per_day': '{:.2f}'
        })
        
        st.dataframe(styled_df, use_container_width=True, height=300)


def tab_fraud_analysis(analyzer: FundAnalyzer, df: pd.DataFrame):
    """涉诈深挖标签页"""
    st.subheader("🚨 涉诈交易深度分析")
    
    fraud_patterns = analyzer.fraud_patterns()
    
    if fraud_patterns:
        # 涉诈概览
        cols = st.columns(4)
        metrics = [
            ("📝 涉诈笔数", f"{fraud_patterns['total_count']}"),
            ("💰 涉诈金额", f"¥{fraud_patterns['total_amount']:,.0f}"),
            ("📊 平均单笔", f"¥{fraud_patterns['avg_amount']:,.0f}"),
            ("⚡ 快速多笔", f"{fraud_patterns.get('rapid_transactions', 0)} 组")
        ]
        for col, (label, value) in zip(cols, metrics):
            col.metric(label, value)
        
        col_c, col_d = st.columns(2)
        
        with col_c:
            # 涉诈时段分布
            hour_dist = pd.DataFrame(
                list(fraud_patterns['hour_distribution'].items()),
                columns=['小时', '笔数']
            ).sort_values('小时')
            
            fig = px.bar(
                hour_dist, x='小时', y='笔数',
                title="⏰ 涉诈交易时段分布",
                color='笔数', color_continuous_scale='Reds',
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_d:
            # 涉诈对手方
            cp_dist = pd.DataFrame(
                list(fraud_patterns['top_counterparties'].items()),
                columns=['对手方', '笔数']
            )
            
            fig = px.treemap(
                cp_dist, path=['对手方'], values='笔数',
                title="🗺️ 涉诈对手方分布",
                height=350, color='笔数', color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 涉诈明细
        st.markdown("### 📋 涉诈交易清单")
        fraud_df = df[df['is_fraud']].sort_values('amount', ascending=False)
        
        display_cols = ['transaction_time', 'source', 'amount', 'counterparty', 'trans_type', 'remark']
        display_cols = [c for c in display_cols if c in fraud_df.columns]
        
        st.dataframe(
            fraud_df[display_cols].style.format({'amount': '¥{:,.0f}'}),
            use_container_width=True, height=300
        )
        
        # 下载涉诈清单
        csv = fraud_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 下载涉诈清单 (CSV)",
            csv,
            f"fraud_list_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.info("ℹ️ 当前数据中未标记涉诈交易")


def tab_smart_detection(analyzer: FundAnalyzer, df: pd.DataFrame):
    """智能检测标签页"""
    st.subheader("⚡ 自动可疑模式检测")
    
    # 整数金额分析
    round_stats = analyzer.detect_round_amount()
    
    st.markdown("#### 🔢 整数金额特征分析")
    cols = st.columns(4)
    round_metrics = [
        ("整百占比", f"{round_stats['round_100']['ratio']:.1f}%", round_stats['round_100']['count']),
        ("整千占比", f"{round_stats['round_1000']['ratio']:.1f}%", round_stats['round_1000']['count']),
        ("整万占比", f"{round_stats['round_10000']['ratio']:.1f}%", round_stats['round_10000']['count']),
        ("涉诈中整百", f"{round_stats['round_100'].get('fraud_ratio', 0):.1f}%", None)
    ]
    for col, (label, value, count) in zip(cols, round_metrics):
        help_text = f"{count} 笔交易" if count else None
        col.metric(label, value, help=help_text)
    
    # 自动检测
    suspicious_result = analyzer.auto_detect_suspicious()
    suspicious_items = suspicious_result.get('suspicious_items', [])
    
    if suspicious_items:
        st.markdown(f"#### 🚨 检测到的可疑模式 "
                   f"<span class='risk-{suspicious_result['risk_level']}'>{suspicious_result['risk_level']}风险</span>", 
                   unsafe_allow_html=True)
        
        for idx, item in enumerate(suspicious_items, 1):
            risk_class = 'risk-high' if item.get('risk_level') == '高' else 'risk-medium' if item.get('risk_level') == '中' else 'risk-low'
            
            with st.expander(f"{idx}. [{item['rule_id']}] {item['rule_name']} - "
                           f"<span class='{risk_class}'>{item['risk_level']}风险</span> "
                           f"({item['count']}条)", expanded=idx<=3):
                
                st.write(f"**描述：** {item['description']}")
                if 'total_amount' in item:
                    st.write(f"**涉及金额：** ¥{item['total_amount']:,.0f}")
                if 'examples' in item:
                    st.json(item['examples'])
                if 'percentage' in item:
                    st.progress(item['percentage'] / 100, text=f"占总交易 {item['percentage']:.1f}%")
    else:
        st.success("✅ 未发现明显可疑模式")
    
    # 自定义规则
    st.markdown("#### 🛠️ 自定义规则检测")
    
    col_rule1, col_rule2, col_rule3 = st.columns(3)
    with col_rule1:
        time_window = st.number_input("时间窗口（分钟）", 1, 60, 5, key="custom_time")
    with col_rule2:
        min_count = st.number_input("最少交易笔数", 2, 20, 3, key="custom_count")
    with col_rule3:
        min_amount_custom = st.number_input("最小金额（元）", 0, 1000000, 0, 1000, key="custom_amt")
    
    # 高频交易检测
    rapid_result = analyzer.transaction_frequency_analysis(window_minutes=time_window)
    rapid_counterparties = rapid_result.get('top_rapid_counterparties', {})
    
    if rapid_counterparties:
        rapid_df = pd.DataFrame([
            {'对手方': k, '快速交易次数': v} 
            for k, v in rapid_counterparties.items() 
            if v >= min_count
        ])
        if not rapid_df.empty:
            st.warning(f"⚠️ 发现 {len(rapid_df)} 个对手方在{time_window}分钟内交易≥{min_count}次")
            st.dataframe(rapid_df, use_container_width=True)
        else:
            st.info(f"未发现符合条件的快速交易")
    else:
        st.info(f"未发现{time_window}分钟内的连续交易")


def tab_data_details(df: pd.DataFrame, amount_threshold: float):
    """明细数据标签页"""
    st.subheader("📋 完整交易明细")
    
    # 筛选控件
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        sources = df['source'].unique().tolist() if 'source' in df.columns else []
        source_filter = st.multiselect("数据源", sources, default=sources)
    
    with col_f2:
        directions = ['income', 'expense', 'unknown']
        direction_filter = st.multiselect("收支类型", directions, default=['income', 'expense'])
    
    with col_f3:
        max_amt_val = float(df['amount'].max()) if not df.empty else 1000000
        min_amt, max_amt = st.slider("金额范围", 0.0, max_amt_val, (0.0, max_amt_val), 1000.0)
    
    with col_f4:
        search = st.text_input("🔍 搜索关键词", placeholder="对手方、备注...")
    
    # 应用筛选
    filtered = df.copy()
    if 'source' in df.columns and source_filter:
        filtered = filtered[filtered['source'].isin(source_filter)]
    if 'direction' in df.columns and direction_filter:
        filtered = filtered[filtered['direction'].isin(direction_filter)]
    if 'amount' in df.columns:
        filtered = filtered[(filtered['amount'] >= min_amt) & (filtered['amount'] <= max_amt)]
    
    if search and not filtered.empty:
        mask = filtered.astype(str).apply(
            lambda x: x.str.contains(search, case=False, na=False)
        ).any(axis=1)
        filtered = filtered[mask]
    
    # 显示结果统计
    st.write(f"显示 **{len(filtered):,}** / **{len(df):,}** 条记录 "
             f"({len(filtered)/len(df)*100:.1f}%)")
    
    # 分页显示
    page_size = Config.PAGE_SIZE
    total_pages = max(1, (len(filtered) - 1) // page_size + 1)
    
    if total_pages > 1:
        col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
        with col_page2:
            page = st.slider("页码", 1, total_pages, 1, key="page_slider")
        start_idx = (page - 1) * page_size
        display_df = filtered.iloc[start_idx:start_idx + page_size]
    else:
        display_df = filtered
    
    # 样式化显示
    def color_amount(val):
        try:
            num = float(val)
            if num >= amount_threshold:
                return f'color: {Config.COLOR_FRAUD}; font-weight: bold; font-size: 1.1em'
            elif num >= amount_threshold / 2:
                return f'color: {Config.COLOR_WARNING}; font-weight: bold'
            return ''
        except:
            return ''
    
    def highlight_fraud_row(row):
        if row.get('is_fraud'):
            return ['background: linear-gradient(90deg, #ffcccc 0%, #ffeaea 100%)'] * len(row)
        return [''] * len(row)
    
    numeric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
    format_dict = {col: '¥{:,.2f}' for col in numeric_cols if 'amount' in col or 'balance' in col}
    
    styled_df = display_df.style \
        .applymap(color_amount, subset=['amount'] if 'amount' in display_df.columns else []) \
        .apply(highlight_fraud_row, axis=1) \
        .format(format_dict)
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # 导出功能
    st.markdown("---")
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with col_exp1:
        csv_all = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            f"📥 导出全部 ({len(df):,}条)", csv_all,
            f"all_transactions_{timestamp}.csv", "text/csv",
            use_container_width=True
        )
    with col_exp2:
        csv_filtered = filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            f"📥 导出筛选 ({len(filtered):,}条)", csv_filtered,
            f"filtered_{timestamp}.csv", "text/csv",
            use_container_width=True
        )
    with col_exp3:
        # Excel 导出（使用 xlsxwriter）
        try:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                filtered.to_excel(writer, index=False, sheet_name='交易明细')
            st.download_button(
                f"📥 导出 Excel", buffer.getvalue(),
                f"transactions_{timestamp}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.caption("Excel导出需安装xlsxwriter")


# ==================== 页脚 ====================
def render_footer():
    """渲染页脚"""
    st.markdown("---")
    st.markdown(f"""
    <div class="footer">
        <p><strong>{Config.PAGE_TITLE}</strong></p>
        <p>支持支付宝、微信、银行流水自动识别与智能分析 | 涉诈预警 | 资金流向追踪</p>
        <p style="font-size: 0.8rem; color: #999; margin-top: 1rem;">
            基于 Streamlit + Plotly + Pandas 构建 | 
            <a href="https://github.com/fund-analyzer" target="_blank">GitHub</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


# ==================== 主程序 ====================
def main():
    """主程序入口"""
    init_page()
    
    # 侧边栏
    uploaded_files, amount_threshold, show_fraud_only = render_sidebar()
    
    # 标题
    st.markdown(f'<h1 class="main-title">{Config.PAGE_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">智能识别多源流水 · 深度分析资金流向 · 精准预警涉诈风险</p>', 
                unsafe_allow_html=True)
    
    # 空状态提示
    if not uploaded_files:
        render_empty_state()
        render_footer()
        return
    
    # 数据加载
    try:
        # 转换文件列表为元组以便缓存
        df, file_info = load_data_cached(tuple(uploaded_files))
        render_file_info(file_info)
        
        if df.empty:
            st.error("❌ 未能成功读取任何有效数据，请检查文件格式是否为标准Excel/CSV")
            st.stop()
        
        # 数据质量验证
        issues = validate_data(df)
        if issues:
            with st.expander("⚠️ 数据质量警告", expanded=True):
                for issue in issues:
                    st.warning(issue)
        
        # 应用筛选
        df_display = df[df['is_fraud'] == True] if show_fraud_only else df
        
        if show_fraud_only and df_display.empty:
            st.warning("未找到涉诈交易记录，显示全部数据")
            df_display = df
        
        # 初始化分析器
        try:
            analyzer = FundAnalyzer(df_display)
        except ValueError as e:
            st.error(f"分析器初始化失败: {e}")
            st.stop()
        
        stats = analyzer.basic_stats()
        
        # 核心指标
        render_metrics(stats, amount_threshold)
        
        # 标签页
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 趋势分析", 
            "👥 对手方", 
            "🔍 涉诈深挖",
            "🌐 资金流向", 
            "⚡ 智能检测",
            "📋 明细数据"
        ])
        
        with tab1:
            tab_trend_analysis(analyzer)
        
        with tab2:
            tab_counterparty_analysis(analyzer, df_display)
        
        with tab3:
            tab_fraud_analysis(analyzer, df_display)
        
        with tab4:
            # 高级可视化：桑基图和网络图
            from utils.visualizer import show_advanced_charts
            show_advanced_charts(df_display)
            
            # 如果存在涉诈数据，显示专门的涉诈网络
            if df_display['is_fraud'].any():
                st.markdown("---")
                from utils.visualizer import show_fraud_network
                show_fraud_network(df_display)
        
        with tab5:
            tab_smart_detection(analyzer, df_display)
        
        with tab6:
            tab_data_details(df_display, amount_threshold)
        
    except Exception as e:
        st.error(f"❌ 数据处理出错: {str(e)}")
        st.exception(e)
        st.info("💡 提示：请确保上传的文件格式正确，且包含必要的列（交易时间、金额、收支方向等）")
    
    render_footer()


def render_empty_state():
    """渲染空状态提示"""
    st.info("👆 **请先在左侧上传资金流水文件开始分析**", icon="📤")
    
    col1, col2, col3 = st.columns(3)
    
    guides = [
        ("📱 支付宝", 
         "我的 → 账单 → 导出", 
         "Excel (.xlsx)", 
         "交易类型、商户、金额、时间"),
        ("💬 微信", 
         "服务 → 钱包 → 账单 → 下载", 
         "Excel (.xlsx)", 
         "转账、红包、商户、时间"),
        ("🏦 银行", 
         "网银/APP → 交易明细 → 导出", 
         "Excel (.xls/.xlsx)", 
         "借贷标志、对手方、余额")
    ]
    
    for col, (title, path, format_, features) in zip([col1, col2, col3], guides):
        with col:
            st.markdown(f"""
            <div class="info-card">
                <h4>{title}</h4>
                <p><strong>导出路径：</strong><br/>{path}</p>
                <p><strong>支持格式：</strong>{format_}</p>
                <p><strong>自动识别：</strong>{features}</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
