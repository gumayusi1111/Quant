# ETF Quant System 项目结构说明

本项目采用“高内聚、低耦合、模块化”设计，每个核心功能作为独立的文件夹包存在，包中可按逻辑再细分多个短小模块（单文件 <200 行）。这样既便于维护，又能在项目增长时轻松扩展。

---

## 🧭 总体结构

```
ETF_Quant_System/
│
├── data/                       # 数据存储层
│   ├── daily_data/              # 日线数据缓存
│   ├── minute_data/             # 分钟数据缓存
│   └── signal_log.csv           # 信号与交易日志
│
├── config/                     # 配置层
│   ├── settings.json            # 系统配置
│   └── tokens.json              # 私密密钥
│
├── src/                        # 核心逻辑层
│   ├── data_fetcher/            # 数据获取模块
│   │   ├── tushare_client.py     # API接口封装
│   │   ├── daily.py              # 日线数据
│   │   └── minute.py             # 分钟数据
│   │
│   ├── indicator_engine/         # 指标计算模块
│   │   ├── trend.py              # 均线、MACD等趋势指标
│   │   ├── volume.py             # 成交量、量比指标
│   │   └── boll_rsi.py           # BOLL、RSI等波动指标
│   │
│   ├── signal_generator/         # 信号生成模块
│   │   ├── rules.py              # 信号判定规则
│   │   ├── scorer.py             # 打分系统
│   │   └── generator.py          # 综合信号生成
│   │
│   ├── strategy_etf/             # 策略逻辑模块
│   │   ├── etf_trend.py          # ETF趋势策略
│   │   └── etf_rotation.py       # 行业轮动策略（扩展）
│   │
│   ├── risk_control/             # 风控模块
│   │   ├── stoploss.py           # 止盈止损逻辑
│   │   └── exposure.py           # 仓位与风险暴露
│   │
│   ├── backtester/               # 回测模块
│   │   ├── engine.py             # 简单回测逻辑
│   │   └── analyzer.py           # 绩效分析
│   │
│   ├── report_builder/           # 报告生成模块
│   │   ├── builder.py            # 输出日报/绩效报告
│   │   └── visualizer.py         # 可视化扩展
│   │
│   ├── scheduler/                # 调度与主流程
│   │   ├── nightly.py            # 盘后分析任务
│   │   └── intraday.py           # 盘中监控任务
│   │
│   ├── utils/                    # 通用工具库
│   │   ├── logger.py             # 日志工具
│   │   ├── io.py                 # IO封装
│   │   ├── timeutil.py           # 时间工具
│   │   └── config.py             # 配置读取
│
├── outputs/                    # 输出层
│   ├── daily_report.html
│   └── trade_log.csv
│
└── main.py                     # 项目主入口
```

---

## 🧩 模块划分逻辑

| 模块 | 功能说明 | 推荐子模块 |
|------|------------|------------|
| **data_fetcher** | 数据获取层，负责从Tushare等API获取K线行情 | `tushare_client.py`、`daily.py`、`minute.py` |
| **indicator_engine** | 指标计算层，对原始数据进行特征加工 | `trend.py`、`volume.py`、`boll_rsi.py` |
| **signal_generator** | 信号生成层，依据指标生成打分与买卖信号 | `rules.py`、`scorer.py`、`generator.py` |
| **strategy_etf** | 策略层，定义ETF趋势或轮动逻辑 | `etf_trend.py`、`etf_rotation.py` |
| **risk_control** | 风控层，包含止盈止损与仓位控制 | `stoploss.py`、`exposure.py` |
| **backtester** | 回测层，检验策略效果与参数优化 | `engine.py`、`analyzer.py` |
| **report_builder** | 报告层，生成日报或HTML绩效图表 | `builder.py`、`visualizer.py` |
| **scheduler** | 调度层，统一执行盘后/盘中任务 | `nightly.py`、`intraday.py` |
| **utils** | 工具层，封装常用方法 | `logger.py`、`io.py`、`config.py`、`timeutil.py` |

---

## ⚙️ 编码规范

1. 每个 `.py` 文件 ≤ 200 行  
2. 单一职责原则：一个文件只负责一个逻辑功能  
3. 所有模块通过函数或数据文件通信，不直接互相导入内部逻辑  
4. 所有输出日志统一使用 `utils/logger.py`  
5. 配置文件统一从 `config/settings.json` 读取  
6. 命名规则：`动词 + 名词`（例：`fetch_daily_data()`）

---

## 🚀 执行流程示意

1️⃣ **盘后阶段**  
- `scheduler/nightly.py` 调用 `data_fetcher` 获取最新数据  
- 运行 `indicator_engine` → `signal_generator` → 生成 `signal_log.csv`  

2️⃣ **盘中阶段**  
- `scheduler/intraday.py` 定时拉取分钟线  
- 动态监控 `signal_generator` 输出信号 → 风控判断止盈止损  

3️⃣ **收盘报告**  
- `report_builder` 汇总并生成日报  

---

## ✨ 总结

这种包式结构：
- 使系统结构清晰，维护成本低；
- 每个文件夹就是一个“逻辑单元”；
- 每个文件内逻辑短小，测试容易；
- 随时可加入机器学习模块或策略扩展。

---
