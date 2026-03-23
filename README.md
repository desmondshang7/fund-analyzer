# 💰 资金流水智能分析系统

基于 Streamlit 的多源资金流水分析工具，支持支付宝、微信、银行流水自动识别与智能分析，具备涉诈预警功能。

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 功能特性

### 📊 数据支持
- **支付宝账单** - 自动识别交易类型、商户、金额
- **微信账单** - 支持转账、红包、商户交易分析
- **银行流水** - 工商银行等主流银行格式支持

### 🔍 分析功能
- **时间维度** - 日/周/月趋势分析，24小时热力图
- **对手方分析** - TOP交易对手统计，资金流向追踪
- **涉诈检测** - 自动识别可疑交易模式
  - 大额整数金额检测
  - 高频小额测试交易
  - 夜间交易集中分析
  - 快速多笔交易检测

### 🌐 高级可视化
- **桑基图** - 直观展示资金流入流出路径
- **关系网络图** - 交易对手方关系可视化
- **交互式图表** - Plotly + PyECharts 双引擎

## 🚀 快速开始

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/fund-analyzer.git
cd fund-analyzer

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 运行应用

```bash
streamlit run app.py
```

应用将在 http://localhost:8501 启动

## 📁 项目结构

```
fund-analyzer/
├── app.py                 # 主程序入口
├── requirements.txt       # 依赖清单
├── README.md             # 项目说明
├── .gitignore            # Git忽略规则
└── utils/                # 工具模块
    ├── __init__.py
    ├── data_loader.py    # 数据读取与标准化
    ├── analyzer.py       # 资金分析核心算法
    └── visualizer.py     # 高级可视化组件
```

## 📖 使用指南

### 1. 导出数据

**支付宝**
- 打开支付宝 → 我的 → 账单 → 导出
- 选择时间范围，下载Excel文件

**微信**
- 打开微信 → 服务 → 钱包 → 账单
- 常见问题 → 下载账单 → 用于个人对账

**银行流水**
- 登录网银或手机银行
- 交易明细 → 导出Excel

### 2. 上传分析

1. 启动应用后，在左侧上传文件
2. 支持同时上传多个文件
3. 系统自动识别数据源类型
4. 查看分析结果和可视化图表

### 3. 分析维度

| 标签页 | 功能 |
|--------|------|
| 📈 趋势分析 | 资金流入流出趋势、时段分布 |
| 👥 对手方 | TOP交易对手、类型分布 |
| 🔍 涉诈深挖 | 涉诈交易统计、时段/对手方分析 |
| 🌐 资金流向 | 桑基图、关系网络可视化 |
| ⚡ 智能检测 | 自动可疑模式识别 |
| 📋 明细数据 | 完整交易记录、筛选导出 |

## ⚙️ 配置说明

### 分析设置
- **大额阈值** - 默认10,000元，可自定义
- **夜间时段** - 默认22:00-06:00，可调整
- **时间窗口** - 快速交易检测间隔，默认5分钟

### 数据安全
- 所有数据处理在本地完成
- 不上传任何数据到服务器
- 敏感文件已添加到.gitignore

## 🛠️ 技术栈

- **Web框架**: Streamlit
- **数据处理**: Pandas, NumPy
- **可视化**: Plotly, PyECharts
- **图表组件**: streamlit-echarts

## 📋 依赖清单

```
streamlit==1.28.0
pandas==2.1.3
plotly==5.17.0
pyecharts==2.0.4
streamlit-echarts==0.4.0
openpyxl==3.1.2
xlsxwriter==3.1.9
numpy==1.26.2
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 更新日志

### v1.0.0 (2024-03-23)
- ✅ 多数据源自动识别
- ✅ 基础统计分析
- ✅ 涉诈交易检测
- ✅ 桑基图和网络图可视化
- ✅ 交互式数据探索

## 📄 许可证

本项目基于 MIT 许可证开源 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - 优秀的Python Web应用框架
- [Plotly](https://plotly.com/) - 强大的可视化库
- [PyECharts](https://pyecharts.org/) - Python ECharts封装

---

<p align="center">
  💰 资金流水智能分析系统 | 让资金分析更简单
</p>
