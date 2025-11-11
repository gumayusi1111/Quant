# 🧱 ETF 全量池初始化与日常更新规范（V1.1）

> 目标：把“第一次全量拉取 → 活跃池构建 → 日常增量 → 盘中分钟追踪”讲清楚，做到**按表施工、一步不乱**。

---

## 0. 前置准备（一次性）
- 申请并验证 **TuShare Pro** `token`
- 建立目录：
  ```text
  data/
    master/etf_master.csv
    universe/active_universe.csv
    daily/
    minute/
    logs/signal_log.csv
    watchlists/watchlist_today.csv
  ```
- 也可以运行 `python main.py --full-pool` 触发自动流程：它会使用 chinadata 拉取最新 ETF 基础信息（写入 `data/master/etf_master.csv`）并为所有标的补齐近 90 天日线缓存。
- 环境：`pip install tushare pandas numpy python-dateutil`

---

## 1. 第一次全量建库（Only once）
**目的：** 构建“ETF身份证 + 90天生命迹象（行情）”，为活跃度计算与指标计算打好基础。

### 1.1 拉全市场 ETF 基本信息 → `data/master/etf_master.csv`
- 接口：`pro.fund_basic(market='E')`
- 字段（至少要）：`ts_code,name,list_date,management,benchmark,market,status`
- 频率：**每2个月或每季度**覆盖更新一次（不是每天拉）

**结果：** 得到 ~1000+ 行的 ETF 清单（主键：`ts_code`）。

### 1.2 为每只 ETF 补齐近 90 个自然日的日K → `data/daily/{ts_code}.csv`
- 接口：`pro.fund_daily(ts_code=..., start_date=...)`
- 推荐区间：**近90天**（目的：稳妥计算 MA20/MACD/BOLL/RSI 及 60日活跃度）
- 字段（至少要）：`trade_date, open, high, low, close, vol, amount, pre_close, pct_chg`
- 注意：若无数据或新上市，允许缺行（下次会补齐）

**结果：** 每只 ETF 一个 CSV，内含近 90 天日线数据。

### 1.3 计算近 60 日活跃度指标（滚动统计）
- 对每只 ETF 的 60 日窗口计算：
  - `amt_mean_60 = mean(amount)`
  - `trade_days_ratio_60 = (#(vol>0))/60`
  - `listed_days = today - list_date`
- **活跃池筛选阈值建议：**
  - `amt_mean_60 ≥ 50,000,000`（保守可用 ≥ 100,000,000）
  - `trade_days_ratio_60 ≥ 0.8`
  - `listed_days ≥ 90`
- 输出：`data/universe/active_universe.csv`（约 150–300 只）

> ✅ 全量阶段到此结束。以后的每日任务**不再逐只全量拉**，而是按交易日**批量拉当日**，再增量更新。

---

## 2. 每日收盘后的增量更新（Daily EOD）
**目的：** 只追加当天数据，保持活跃池的历史完整；并生成次日观察池。

### 2.1 一次性批量拉“全市场当日基金日K”
- 接口：`pro.fund_daily(trade_date=today)` → 返回**全市场基金**当日数据
- 过滤：与 `data/master/etf_master.csv` 进行 `inner join`，只保留 ETF 行

### 2.2 只对 **活跃池** 逐只 append 当日1行
- 将对应 `ts_code` 的当日记录 **追加**到 `data/daily/{ts_code}.csv`
- 同时维护一个“统计表/宽表”，增量更新近 60 日滚动均值与交易天数占比

> 🔁 建议：**每两周**重新计算一次活跃度并覆盖 `data/universe/active_universe.csv`

### 2.3 计算技术指标并打分
- 指标：`MA(5/10/20), MACD(12,26,9), BOLL(20), RSI(14), 量比、成交额均线`
- 生成信号：趋势结构 + 量能确认 + 波动约束
- 写入：`data/logs/signal_log.csv`（含 `ts_code, signal, score, tp, sl`）

### 2.4 形成次日观察池（10–20只）
- 从活跃池按 `score` 排序，取 Top N
- 写入：`data/watchlists/watchlist_today.csv`（仅 `ts_code` 列即可）

---

## 3. 次日盘中分钟级追踪（Intraday）
**目的：** 用分钟线做择时（买点/卖点/止盈止损），仅对观察池。

### 3.1 定时拉取分钟K（每1–5分钟一次）
- 接口：`ts.pro_bar(ts_code=..., freq='1min'/'5min', start_date=today, end_date=today)`
- 对象：`data/watchlists/watchlist_today.csv` 内的 10–20 只
- 存储：`data/minute/{ts_code}_{YYYYMMDD}_{freq}.csv`（按天分文件，便于清理）

### 3.2 择时规则（示例）
- **入场**：`close > VWAP` 且 `vol > 均量1.2倍` 且 `RSI < 70`
- **出场**：跌破 `VWAP` 或 `sl`；或达到 `tp`；或收盘前止盈/止损退出

> ⏱️ TuShare 分钟数据为“近实时”并有 5–10 分钟延迟，足够 1–7 天短线波段使用。

---

## 4. 更新节奏与职责矩阵

| 层级 | 频率 | 负责人/模块 | 产物 |
|------|------|-------------|------|
| ETF 全库 | 每2个月 | `update_etf_master.py` | `data/master/etf_master.csv` |
| 活跃池重算 | 每两周 | `refresh_active_pool.py` | `data/universe/active_universe.csv` |
| 日更（EOD） | 每日收盘后 | `daily_pipeline.py` | 追加日K、`data/logs/signal_log.csv`、`data/watchlists/watchlist_today.csv` |
| 盘中分钟 | 每1–5分钟 | `intraday_pipeline.py` | 观察池分钟文件 + 实时提醒 |

---

## 5. 字段与文件约定（Naming / Schema）

### 5.1 `data/master/etf_master.csv`
- `ts_code,name,list_date,management,benchmark,market,status`

### 5.2 `data/daily/{ts_code}.csv`
- `trade_date,open,high,low,close,vol,amount,pre_close,pct_chg`（升序保存）

### 5.3 `data/universe/active_universe.csv`
- `ts_code, amt_mean_60, trade_days_ratio_60, listed_days`

### 5.4 `data/logs/signal_log.csv`
- `date,ts_code,signal,score,tp,sl,status`

### 5.5 `data/watchlists/watchlist_today.csv`
- `ts_code`（一列）

### 5.6 `data/minute/{ts_code}_{YYYYMMDD}_{freq}.csv`
- `trade_time,open,high,low,close,vol,amount,pre_close,pct_chg`

---

## 6. 常见问题（FAQ）

**Q1：第一次一定要拉 90 天吗？**
- 是。少于 60 天会影响 MA20/MACD/BOLL/RSI 稳定性，也无法计算 60 日活跃度。

**Q2：以后是否还要每天逐只拉 1000+ 只？**
- 不。每日按 `trade_date` 一把抓全市场，拿到当日 ETF 行，再**只对活跃池**追加。

**Q3：分钟线是否也要对活跃池全部拉？**
- 不。分钟只对**观察池**（10–20只）拉，用于择时。

**Q4：是否需要数据库？**
- 你目前规模 CSV 足够；未来数据暴增时可迁移 SQLite / DuckDB。

**Q5：活跃池多久重算一次？**
- 建议每两周重算；在日更阶段只需根据日K追加数据做信号，不必每天重算。

---

## 7. 一键检查清单（Checklist）
- [ ] `token` 可用，`pro = ts.pro_api()` 正常
- [ ] `data/master/etf_master.csv` 最近 2 个月内更新
- [ ] `data/daily/` 每只活跃 ETF 有近 90 天记录且按日追加
- [ ] `data/universe/active_universe.csv` 最近 1 个月内刷新
- [ ] 每日生成 `data/logs/signal_log.csv` 与 `data/watchlists/watchlist_today.csv`
- [ ] 盘中只对观察池拉分钟文件

---

## 8. 建议的时间跨度（按策略周期）
- 1–3 天：60 天历史
- **3–7 天：90 天历史（推荐）**
- 7–15 天：120 天历史
- > 1 月：180 天以上

---

## 9. 关键阈值（可在 `settings.json` 配置）
```json
{
  "active_filters": {
    "amt_mean_60": 50000000,
    "trade_days_ratio_60": 0.8,
    "listed_days_min": 90
  },
  "watchlist_top_n": 20,
  "minute_freq": "5min"
}
```

---

**一句话总结：**  
> **第一次全量拉清单 + 90 天行情** → **活跃池筛出可交易的样本** → **每天仅增量更新活跃池** → **次日盘中只追踪观察池分钟线**。  
> 省频率、稳指标、可扩展。

