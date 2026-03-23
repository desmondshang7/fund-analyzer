"""
高级可视化组件 - 资金流向桑基图、关系网络图等
"""

import plotly.graph_objects as go
from pyecharts.charts import Sankey, Graph, Pie, Bar, Timeline
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_echarts import st_pyecharts
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')


@dataclass
class SankeyConfig:
    """桑基图配置"""
    top_n_sources: int = 8           # 显示前N个收入来源
    top_n_targets: int = 8           # 显示前N个支出去向
    min_amount: float = 100          # 最小金额阈值
    show_self_transfer: bool = False  # 是否显示内部转账
    color_income: str = "#2ecc71"    # 收入颜色
    color_expense: str = "#e74c3c"   # 支出颜色
    height: int = 500                # 图表高度


@dataclass
class NetworkConfig:
    """网络图配置"""
    min_amount: float = 1000         # 最小交易金额
    max_nodes: int = 50              # 最大节点数
    repulsion: int = 5000            # 节点排斥力
    show_labels: bool = True         # 显示标签
    fraud_color: str = "#ff4757"     # 涉诈节点颜色
    normal_color: str = "#3498db"    # 正常节点颜色
    account_color: str = "#f39c12"   # 主账户颜色
    height: int = 600                # 图表高度


class AdvancedVisualizer:
    """高级可视化器 - 支持桑基图、网络图等复杂可视化"""
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化可视化器
        
        Args:
            df: 标准化的交易数据DataFrame
        """
        if df.empty:
            raise ValueError("数据为空，无法创建可视化")
        
        self.df = df.copy()
        self._ensure_required_columns()
    
    def _ensure_required_columns(self):
        """确保必要的列存在"""
        required = ['direction', 'amount', 'counterparty']
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            raise ValueError(f"缺少必要列: {missing}")
        
        # 确保数值类型
        self.df['amount'] = pd.to_numeric(self.df['amount'], errors='coerce')
        
        # 填充缺失值
        self.df['counterparty'] = self.df['counterparty'].fillna('未知')
        self.df['trans_type'] = self.df.get('trans_type', '其他')
        self.df['is_fraud'] = self.df.get('is_fraud', False).fillna(False)
        self.df['account'] = self.df.get('account', '主账户').fillna('主账户')
    
    # ==================== 桑基图 ====================
    
    def prepare_sankey_data(self, config: Optional[SankeyConfig] = None) -> Tuple[List, List, Dict]:
        """
        准备桑基图数据
        
        Returns:
            (节点列表, 链接列表, 统计信息)
        """
        if config is None:
            config = SankeyConfig()
        
        # 过滤小额交易
        df_filtered = self.df[self.df['amount'] >= config.min_amount].copy()
        
        if df_filtered.empty:
            return [], [], {"error": "过滤后数据为空"}
        
        # 获取主要收入来源（Top N）
        income_df = df_filtered[df_filtered['direction'] == 'income']
        top_sources = income_df.groupby('counterparty')['amount'].sum().nlargest(config.top_n_sources)
        
        # 获取主要支出去向（Top N）
        expense_df = df_filtered[df_filtered['direction'] == 'expense']
        top_targets = expense_df.groupby('counterparty')['amount'].sum().nlargest(config.top_n_targets)
        
        # 构建节点列表
        nodes = [{"name": "主账户", "itemStyle": {"color": config.account_color}}]
        
        # 收入节点
        for source in top_sources.index:
            nodes.append({
                "name": source,
                "itemStyle": {"color": config.color_income}
            })
        
        # 支出节点
        for target in top_targets.index:
            nodes.append({
                "name": target,
                "itemStyle": {"color": config.color_expense}
            })
        
        # 构建链接
        links = []
        total_income = 0
        total_expense = 0
        
        # 收入链接（来源 -> 主账户）
        for source, amount in top_sources.items():
            if amount > 0:
                links.append({
                    "source": source,
                    "target": "主账户",
                    "value": round(float(amount), 2)
                })
                total_income += amount
        
        # 支出链接（主账户 -> 去向）
        for target, amount in top_targets.items():
            if amount > 0:
                links.append({
                    "source": "主账户",
                    "target": target,
                    "value": round(float(amount), 2)
                })
                total_expense += amount
        
        stats = {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_flow": total_income - total_expense,
            "source_count": len(top_sources),
            "target_count": len(top_targets),
            "node_count": len(nodes),
            "link_count": len(links)
        }
        
        return nodes, links, stats
    
    def create_sankey(self, config: Optional[SankeyConfig] = None) -> Sankey:
        """
        创建资金流向桑基图
        
        Args:
            config: 桑基图配置
            
        Returns:
            PyECharts Sankey 图表对象
        """
        nodes, links, stats = self.prepare_sankey_data(config)
        
        if not nodes or not links:
            # 返回空图表
            return Sankey().set_global_opts(
                title_opts=opts.TitleOpts(title="暂无足够数据生成桑基图")
            )
        
        cfg = config or SankeyConfig()
        
        c = (
            Sankey(init_opts=opts.InitOpts(
                width="100%",
                height=f"{cfg.height}px",
                theme="light",
                bg_color="#fff"
            ))
            .add(
                series_name="资金流向",
                nodes=nodes,
                links=links,
                pos_top="10%",
                pos_bottom="10%",
                pos_left="5%",
                pos_right="5%",
                node_width=20,
                node_gap=12,
                layout_iterations=32,  # 布局迭代次数，提高美观度
                label_opts=opts.LabelOpts(
                    position="right",
                    font_size=11,
                    font_family="Microsoft YaHei",
                    formatter=JsCode("""
                        function(params) {
                            return params.name + '\n¥' + params.value.toLocaleString();
                        }
                    """)
                ),
                linestyle_opt=opts.LineStyleOpts(
                    opacity=0.25,
                    curve=0.5,
                    color="source",  # 线条颜色跟随源节点
                    curveness=0.5
                ),
                itemstyle_opts=opts.ItemStyleOpts(
                    border_width=1,
                    border_color="#aaa"
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    trigger_on="mousemove",
                    formatter=JsCode("""
                        function(params) {
                            if (params.dataType === 'node') {
                                return params.name + '<br/>金额: ¥' + params.value.toLocaleString();
                            } else {
                                return params.data.source + ' → ' + params.data.target + 
                                       '<br/>金额: ¥' + params.value.toLocaleString();
                            }
                        }
                    """)
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="资金流入流出桑基图",
                    subtitle=f"收入: ¥{stats['total_income']:,.0f} | 支出: ¥{stats['total_expense']:,.0f} | 净流入: ¥{stats['net_flow']:+,.0f}",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=16),
                    subtitle_textstyle_opts=opts.TextStyleOpts(font_size=12, color="#666")
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    formatter="{b}: ¥{c}"
                ),
            )
        )
        
        return c
    
    def create_sankey_plotly(self, config: Optional[SankeyConfig] = None) -> go.Figure:
        """
        使用 Plotly 创建桑基图（备选方案）
        
        Args:
            config: 桑基图配置
            
        Returns:
            Plotly Figure 对象
        """
        nodes, links, stats = self.prepare_sankey_data(config)
        
        if not nodes or not links:
            fig = go.Figure()
            fig.update_layout(title="暂无足够数据生成桑基图")
            return fig
        
        # 创建节点索引映射
        node_names = [n['name'] for n in nodes]
        node_indices = {name: i for i, name in enumerate(node_names)}
        node_colors = [n.get('itemStyle', {}).get('color', '#999') for n in nodes]
        
        # 转换链接为索引
        link_sources = [node_indices[link['source']] for link in links]
        link_targets = [node_indices[link['target']] for link in links]
        link_values = [link['value'] for link in links]
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=node_names,
                color=node_colors
            ),
            link=dict(
                source=link_sources,
                target=link_targets,
                value=link_values,
                color=["rgba(100,100,100,0.3)"] * len(links)
            )
        )])
        
        cfg = config or SankeyConfig()
        fig.update_layout(
            title_text=f"资金流向桑基图<br><sup>收入: ¥{stats['total_income']:,.0f} | 支出: ¥{stats['total_expense']:,.0f}</sup>",
            font_size=12,
            height=cfg.height
        )
        
        return fig
    
    # ==================== 网络图 ====================
    
    def prepare_network_data(self, config: Optional[NetworkConfig] = None) -> Tuple[List, List, List, Dict]:
        """
        准备网络图数据
        
        Returns:
            (节点列表, 链接列表, 分类列表, 统计信息)
        """
        if config is None:
            config = NetworkConfig()
        
        # 筛选转账交易和大额交易
        transfer_mask = (
            self.df['trans_type'].str.contains('转账|汇款|收款', na=False, regex=True) |
            (self.df['amount'] >= config.min_amount)
        )
        transfer_df = self.df[transfer_mask].copy()
        
        if transfer_df.empty:
            return [], [], [], {"error": "没有足够的转账交易数据"}
        
        # 按金额排序取前N个
        transfer_df = transfer_df.nlargest(config.max_nodes * 2, 'amount')
        
        # 构建节点和边
        nodes = []
        links = []
        node_map = {}  # name -> index
        node_counter = [0]  # 使用列表实现nonlocal
        
        def add_node(name: str, category: int, amount: float = 0, is_fraud: bool = False):
            """添加节点（避免重复）"""
            if name in node_map:
                # 更新现有节点的大小
                idx = node_map[name]
                if amount > 0:
                    # 根据金额调整大小
                    new_size = min(20 + np.log1p(amount) / 2, 60)
                    nodes[idx]['symbolSize'] = max(nodes[idx]['symbolSize'], new_size)
                if is_fraud:
                    nodes[idx]['category'] = 1  # 涉诈
                return idx
            
            # 新节点
            size = min(20 + np.log1p(amount) / 2, 60) if amount > 0 else 15
            color = config.fraud_color if is_fraud else (
                config.account_color if category == 0 else config.normal_color
            )
            
            nodes.append({
                "name": name,
                "symbolSize": size,
                "category": category,
                "itemStyle": {"color": color},
                "value": float(amount)
            })
            
            node_map[name] = node_counter[0]
            node_counter[0] += 1
            return node_map[name]
        
        # 统计
        fraud_count = 0
        total_amount = 0
        
        for _, row in transfer_df.iterrows():
            account = str(row['account']) if pd.notna(row['account']) else '主账户'
            counterparty = str(row['counterparty'])
            amount = float(row['amount']) if pd.notna(row['amount']) else 0
            is_fraud = bool(row['is_fraud']) if pd.notna(row['is_fraud']) else False
            
            if counterparty == '未知' or not counterparty:
                continue
            
            # 添加节点
            account_idx = add_node(account, 0, amount, False)
            cp_idx = add_node(counterparty, 1 if is_fraud else 2, amount, is_fraud)
            
            # 添加边
            if row['direction'] == 'income':
                links.append({
                    "source": counterparty,
                    "target": account,
                    "value": amount,
                    "lineStyle": {
                        "color": config.fraud_color if is_fraud else config.color_income,
                        "width": min(max(amount / 10000, 1), 5)
                    }
                })
            else:
                links.append({
                    "source": account,
                    "target": counterparty,
                    "value": amount,
                    "lineStyle": {
                        "color": config.fraud_color if is_fraud else config.color_expense,
                        "width": min(max(amount / 10000, 1), 5)
                    }
                })
            
            if is_fraud:
                fraud_count += 1
            total_amount += amount
        
        # 限制节点数量
        if len(nodes) > config.max_nodes:
            # 按交易金额排序保留重要节点
            node_importance = {}
            for link in links:
                node_importance[link['source']] = node_importance.get(link['source'], 0) + link['value']
                node_importance[link['target']] = node_importance.get(link['target'], 0) + link['value']
            
            # 保留主账户和最重要的节点
            important_nodes = ['主账户'] + sorted(
                node_importance.keys(), 
                key=lambda x: node_importance[x], 
                reverse=True
            )[:config.max_nodes-1]
            
            # 过滤节点和链接
            nodes = [n for n in nodes if n['name'] in important_nodes]
            node_names = {n['name'] for n in nodes}
            links = [l for l in links if l['source'] in node_names and l['target'] in node_names]
        
        categories = [
            {"name": "主账户", "itemStyle": {"color": config.account_color}},
            {"name": "涉诈对手方", "itemStyle": {"color": config.fraud_color}},
            {"name": "正常对手方", "itemStyle": {"color": config.normal_color}}
        ]
        
        stats = {
            "node_count": len(nodes),
            "link_count": len(links),
            "fraud_count": fraud_count,
            "total_amount": total_amount,
            "fraud_ratio": fraud_count / len(nodes) * 100 if nodes else 0
        }
        
        return nodes, links, categories, stats
    
    def create_network(self, config: Optional[NetworkConfig] = None) -> Graph:
        """
        创建交易关系网络图
        
        Args:
            config: 网络图配置
            
        Returns:
            PyECharts Graph 图表对象
        """
        nodes, links, categories, stats = self.prepare_network_data(config)
        
        if not nodes:
            return Graph().set_global_opts(
                title_opts=opts.TitleOpts(title="暂无足够数据生成网络图")
            )
        
        cfg = config or NetworkConfig()
        
        c = (
            Graph(init_opts=opts.InitOpts(
                width="100%",
                height=f"{cfg.height}px",
                theme="light",
                bg_color="#fff"
            ))
            .add(
                series_name="交易关系",
                nodes=nodes,
                links=links,
                categories=categories,
                layout="force",
                symbol="circle",
                roam=True,  # 允许缩放和拖拽
                draggable=True,
                is_focusnode=True,
                is_rotate_label=True,
                gravity=0.2,
                repulsion=cfg.repulsion,
                edge_length=[50, 200],
                label_opts=opts.LabelOpts(
                    is_show=cfg.show_labels,
                    position="right",
                    font_size=10,
                    font_family="Microsoft YaHei",
                    formatter="{b}"
                ),
                linestyle_opts=opts.LineStyleOpts(
                    curve=0.2,
                    opacity=0.7,
                    width=2
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    formatter=JsCode("""
                        function(params) {
                            if (params.dataType === 'node') {
                                return params.name + '<br/>交易总额: ¥' + 
                                       (params.value || 0).toLocaleString();
                            } else {
                                return params.data.source + ' → ' + params.data.target + 
                                       '<br/>金额: ¥' + params.value.toLocaleString();
                            }
                        }
                    """)
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="交易关系网络图",
                    subtitle=f"节点: {stats['node_count']} | 关系: {stats['link_count']} | 涉诈: {stats['fraud_count']}",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=16),
                    subtitle_textstyle_opts=opts.TextStyleOpts(font_size=12, color="#666")
                ),
                legend_opts=opts.LegendOpts(
                    orient="vertical",
                    pos_left="left",
                    pos_top="middle",
                    item_width=14,
                    item_height=14
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    formatter="{b}: {c}"
                ),
            )
        )
        
        return c
    
    def create_network_plotly(self, config: Optional[NetworkConfig] = None) -> go.Figure:
        """
        使用 Plotly 创建网络图（备选方案）
        
        Args:
            config: 网络图配置
            
        Returns:
            Plotly Figure 对象
        """
        nodes, links, categories, stats = self.prepare_network_data(config)
        
        if not nodes:
            fig = go.Figure()
            fig.update_layout(title="暂无足够数据生成网络图")
            return fig
        
        # 构建节点坐标（使用简单的环形布局）
        import random
        random.seed(42)
        
        node_positions = {}
        center_x, center_y = 0, 0
        
        # 主账户放中间
        for node in nodes:
            if node['category'] == 0:  # 主账户
                node_positions[node['name']] = (center_x, center_y)
                break
        
        # 其他节点环形分布
        other_nodes = [n for n in nodes if n['name'] not in node_positions]
        angle_step = 2 * np.pi / max(len(other_nodes), 1)
        radius = 3
        
        for i, node in enumerate(other_nodes):
            angle = i * angle_step
            x = center_x + radius * np.cos(angle) + random.uniform(-0.5, 0.5)
            y = center_y + radius * np.sin(angle) + random.uniform(-0.5, 0.5)
            node_positions[node['name']] = (x, y)
        
        # 创建边
        edge_traces = []
        for link in links:
            x0, y0 = node_positions.get(link['source'], (0, 0))
            x1, y1 = node_positions.get(link['target'], (0, 0))
            
            edge_traces.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(
                    width=link.get('lineStyle', {}).get('width', 1),
                    color=link.get('lineStyle', {}).get('color', '#999')
                ),
                hoverinfo='text',
                text=f"{link['source']} → {link['target']}<br>金额: ¥{link['value']:,.0f}",
                mode='lines',
                showlegend=False
            ))
        
        # 创建节点
        node_x, node_y, node_text, node_size, node_color = [], [], [], [], []
        for node in nodes:
            x, y = node_positions.get(node['name'], (0, 0))
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node['name']}<br>金额: ¥{node.get('value', 0):,.0f}")
            node_size.append(node.get('symbolSize', 15))
            node_color.append(node.get('itemStyle', {}).get('color', '#999'))
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text' if config and config.show_labels else 'markers',
            text=[n['name'] for n in nodes],
            textposition="top center",
            hoverinfo='text',
            hovertext=node_text,
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='white')
            ),
            showlegend=False
        )
        
        fig = go.Figure(data=edge_traces + [node_trace])
        cfg = config or NetworkConfig()
        fig.update_layout(
            title=f"交易关系网络图<br><sup>节点: {stats['node_count']} | 关系: {stats['link_count']} | 涉诈: {stats['fraud_count']}</sup>",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=cfg.height,
            plot_bgcolor='white'
        )
        
        return fig


# ==================== Streamlit 集成函数 ====================

def show_advanced_charts(df: pd.DataFrame, use_pyecharts: bool = True):
    """
    在 Streamlit 中显示高级图表
    
    Args:
        df: 交易数据DataFrame
        use_pyecharts: 是否使用 PyECharts（否则使用 Plotly）
    """
    try:
        visualizer = AdvancedVisualizer(df)
    except ValueError as e:
        st.warning(f"无法创建可视化: {e}")
        return
    
    st.subheader("🌐 资金流向可视化")
    
    tab1, tab2, tab3 = st.tabs(["📊 桑基图", "🕸️ 关系网络", "⚙️ 配置"])
    
    # 配置状态
    if 'sankey_config' not in st.session_state:
        st.session_state['sankey_config'] = SankeyConfig()
    if 'network_config' not in st.session_state:
        st.session_state['network_config'] = NetworkConfig()
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**桑基图配置**")
            st.session_state['sankey_config'].top_n_sources = st.slider(
                "显示前N个收入来源", 3, 15, 8, key="sankey_sources"
            )
            st.session_state['sankey_config'].top_n_targets = st.slider(
                "显示前N个支出去向", 3, 15, 8, key="sankey_targets"
            )
            st.session_state['sankey_config'].min_amount = st.number_input(
                "最小金额阈值", 0, 10000, 100, 100, key="sankey_min"
            )
        with col2:
            st.markdown("**网络图配置**")
            st.session_state['network_config'].min_amount = st.number_input(
                "最小交易金额", 0, 50000, 1000, 500, key="network_min"
            )
            st.session_state['network_config'].max_nodes = st.slider(
                "最大节点数", 10, 100, 50, key="network_max"
            )
            st.session_state['network_config'].repulsion = st.slider(
                "节点排斥力", 1000, 10000, 5000, 500, key="network_repulsion"
            )
    
    with tab1:
        try:
            if use_pyecharts:
                sankey = visualizer.create_sankey(st.session_state['sankey_config'])
                st_pyecharts(sankey, height=f"{st.session_state['sankey_config'].height}px")
            else:
                fig = visualizer.create_sankey_plotly(st.session_state['sankey_config'])
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"桑基图生成失败: {e}")
            st.info("尝试使用 Plotly 版本...")
            try:
                fig = visualizer.create_sankey_plotly(st.session_state['sankey_config'])
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e2:
                st.error(f"备选方案也失败: {e2}")
    
    with tab2:
        try:
            if use_pyecharts:
                network = visualizer.create_network(st.session_state['network_config'])
                st_pyecharts(network, height=f"{st.session_state['network_config'].height}px")
            else:
                fig = visualizer.create_network_plotly(st.session_state['network_config'])
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"网络图生成失败: {e}")
            st.info("尝试使用 Plotly 版本...")
            try:
                fig = visualizer.create_network_plotly(st.session_state['network_config'])
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e2:
                st.error(f"备选方案也失败: {e2}")


def show_fraud_network(df: pd.DataFrame):
    """专门显示涉诈关系网络"""
    fraud_df = df[df['is_fraud'] == True].copy()
    
    if fraud_df.empty:
        st.info("暂无涉诈交易数据")
        return
    
    st.markdown("### 🚨 涉诈交易关系网络")
    
    config = NetworkConfig(
        min_amount=0,
        max_nodes=30,
        fraud_color="#ff0000",
        normal_color="#ff9999"
    )
    
    try:
        visualizer = AdvancedVisualizer(fraud_df)
        network = visualizer.create_network(config)
        st_pyecharts(network, height="500px")
    except Exception as e:
        st.error(f"涉诈网络图生成失败: {e}")


# 便捷函数
@st.cache_data(ttl=300)
def create_sankey_cached(df_json: str, config_dict: Dict) -> Any:
    """缓存的桑基图生成（用于Streamlit缓存）"""
    df = pd.read_json(df_json)
    config = SankeyConfig(**config_dict)
    visualizer = AdvancedVisualizer(df)
    return visualizer.create_sankey(config)
