ETF 基础信息
接口：etf_basic
描述：获取国内 ETF 基础信息，包括了 QDII。数据来源与沪深交易所公开披露信息。
限量：单次请求最大放回 5000 条数据（当前 ETF 总数未超过 2000）
权限：用户积 8000 积分可调取，具体请参阅积分获取办法

输入参数

名称 类型 必选 描述
ts_code str N ETF 代码（带.SZ/.SH 后缀的 6 位数字，如：159526.SZ）
index_code str N 跟踪指数代码
list_date str N 上市日期（格式：YYYYMMDD）
list_status str N 上市状态（L 上市 D 退市 P 待上市）
exchange str N 交易所（SH 上交所 SZ 深交所）
mgr str N 管理人（简称，e.g.华夏基金)

输出参数

名称 类型 默认显示 描述
ts_code str Y 基金交易代码
csname str Y ETF 中文简称
extname str Y ETF 扩位简称(对应交易所简称)
cname str Y 基金中文全称
index_code str Y ETF 基准指数代码
index_name str Y ETF 基准指数中文全称
setup_date str Y 设立日期（格式：YYYYMMDD）
list_date str Y 上市日期（格式：YYYYMMDD）
list_status str Y 存续状态（L 上市 D 退市 P 待上市）
exchange str Y 交易所（上交所 SH 深交所 SZ）
mgr_name str Y 基金管理人简称
custod_name str Y 基金托管人名称
mgt_fee float Y 基金管理人收取的费用
etf_type str Y 基金投资通道类型（境内、QDII）

接口示例

#获取当前所有上市的 ETF 列表
df = pro.etf_basic(list_status='L', fields='ts_code,extname,index_code,index_name,exchange,mgr_name')

#获取“嘉实基金”所有上市的 ETF 列表
df = pro.etf_basic(mgr='嘉实基金'， list_status='L', fields='ts_code,extname,index_code,index_name,exchange,etf_type')

#获取“嘉实基金”在深交所上市的所有 ETF 列表
df = pro.etf_basic(mgr='嘉实基金'， list_status='L', exchange='SZ', fields='ts_code,extname,index_code,index_name,exchange,etf_type')

#获取以沪深 300 指数为跟踪指数的所有上市的 ETF 列表
df = pro.etf_basic(index_code='000300.SH', fields='ts_code,extname,index_code,index_name,exchange,mgr_name')

数据示例

      ts_code       extname    index_code    index_name exchange   mgr_name

0 159238.SZ 300ETF 增强 000300.SH 沪深 300 指数 SZ 景顺长城基金
1 159300.SZ 300ETF 000300.SH 沪深 300 指数 SZ 富国基金
2 159330.SZ 沪深 300ETF 基金 000300.SH 沪深 300 指数 SZ 西藏东财基金
3 159393.SZ 沪深 300 指数 ETF 000300.SH 沪深 300 指数 SZ 万家基金
4 159673.SZ 沪深 300ETF 鹏华 000300.SH 沪深 300 指数 SZ 鹏华基金
5 159919.SZ 沪深 300ETF 000300.SH 沪深 300 指数 SZ 嘉实基金
6 159925.SZ 沪深 300ETF 南方 000300.SH 沪深 300 指数 SZ 南方基金
7 159927.SZ 鹏华沪深 300 指数 000300.SH 沪深 300 指数 SZ 鹏华基金
8 510300.SH 沪深 300ETF 000300.SH 沪深 300 指数 SH 华泰柏瑞基金
9 510310.SH 沪深 300ETF 易方达 000300.SH 沪深 300 指数 SH 易方达基金
10 510320.SH 沪深 300ETF 中金 000300.SH 沪深 300 指数 SH 中金基金
11 510330.SH 沪深 300ETF 华夏 000300.SH 沪深 300 指数 SH 华夏基金
12 510350.SH 沪深 300ETF 工银 000300.SH 沪深 300 指数 SH 工银瑞信基金
13 510360.SH 沪深 300ETF 基金 000300.SH 沪深 300 指数 SH 广发基金
14 510370.SH 300 指数 ETF 000300.SH 沪深 300 指数 SH 兴业基金
15 510380.SH 国寿 300ETF 000300.SH 沪深 300 指数 SH 国寿安保基金
16 510390.SH 沪深 300ETF 平安 000300.SH 沪深 300 指数 SH 平安基金
17 515130.SH 沪深 300ETF 博时 000300.SH 沪深 300 指数 SH 博时基金
18 515310.SH 沪深 300 指数 ETF 000300.SH 沪深 300 指数 SH 汇添富基金
19 515330.SH 沪深 300ETF 天弘 000300.SH 沪深 300 指数 SH 天弘基金
20 515350.SH 民生加银 300ETF 000300.SH 沪深 300 指数 SH 民生加银基金
21 515360.SH 方正沪深 300ETF 000300.SH 沪深 300 指数 SH 方正富邦基金
22 515380.SH 沪深 300ETF 泰康 000300.SH 沪深 300 指数 SH 泰康基金
23 515390.SH 沪深 300ETF 指数基金 000300.SH 沪深 300 指数 SH 华安基金
24 515660.SH 沪深 300ETF 国联安 000300.SH 沪深 300 指数 SH 国联安基金
25 515930.SH 永赢沪深 300ETF 000300.SH 沪深 300 指数 SH 永赢基金
26 561000.SH 沪深 300ETF 增强基金 000300.SH 沪深 300 指数 SH 华安基金
27 561300.SH 300 增强 ETF 000300.SH 沪深 300 指数 SH 国泰基金
28 561930.SH 沪深 300ETF 招商 000300.SH 沪深 300 指数 SH 招商基金
29 561990.SH 沪深 300 增强 ETF 000300.SH 沪深 300 指数 SH 招商基金
30 563520.SH 沪深 300ETF 永赢 000300.SH 沪深 300 指数 SH 永赢基金

ETF 基准指数列表
接口：etf_index
描述：获取 ETF 基准指数列表信息
限量：单次请求最大返回 5000 行数据（当前未超过 2000 个）
权限：用户积累 8000 积分可调取，具体请参阅积分获取办法

输入参数

名称 类型 必选 描述
ts_code str N 指数代码
pub_date str N 发布日期（格式：YYYYMMDD）
base_date str N 指数基期（格式：YYYYMMDD）

输出参数

名称 类型 默认显示 描述
ts_code str Y 指数代码
indx_name str Y 指数全称
indx_csname str Y 指数简称
pub_party_name str Y 指数发布机构
pub_date str Y 指数发布日期
base_date str Y 指数基日
bp float Y 指数基点(点)
adj_circle str Y 指数成份证券调整周期

接口示例

#获取当前 ETF 跟踪的基准指数列表
df = pro.etf_index(fields='ts_code,indx_name,pub_date,bp')

数据示例

          ts_code        indx_name         pub_date           bp

0 000068.SH 上证自然资源指数 20100528 1000.000000
1 000001.SH 上证综合指数 19910715 100.000000
2 000989.SH 中证全指可选消费指数 20110802 1000.000000
3 000990.CSI 中证全指主要消费指数 20110802 1000.000000
4 000043.SH 上证超级大盘指数 20090423 1000.000000
... ... ... ... ...
1458 932368.CSI 中证 800 自由现金流指数 20241211 1000.000000
1460 000680.SH 上证科创板综合指数 20250120 1000.000000
1461 000681.SH 上证科创板综合价格指数 20250120 1000.000000
ETF 历史分钟行情
接口：stk_mins
描述：获取 ETF 分钟数据，支持 1min/5min/15min/30min/60min 行情，提供 Python SDK 和 http Restful API 两种方式
限量：单次最大 8000 行数据，可以通过股票代码和时间循环获取，本接口可以提供超过 10 年 ETF 历史分钟数据
权限：正式权限请参阅 权限说明

输入参数

名称 类型 必选 描述
ts_code str Y ETF 代码，e.g. 159001.SZ
freq str Y 分钟频度（1min/5min/15min/30min/60min）
start_date datetime N 开始日期 格式：2025-06-01 09:00:00
end_date datetime N 结束时间 格式：2025-06-20 19:00:00

freq 参数说明

freq 说明
1min 1 分钟
5min 5 分钟
15min 15 分钟
30min 30 分钟
60min 60 分钟

输出参数

名称 类型 默认显示 描述
ts_code str Y ETF 代码
trade_time str Y 交易时间
open float Y 开盘价
close float Y 收盘价
high float Y 最高价
low float Y 最低价
vol int Y 成交量
amount float Y 成交金额

接口用法

pro = ts.pro_api()

#获取沪深 300ETF 华夏 510330.SH 的历史分钟数据
df = pro.stk_mins(ts_code='510330.SH', freq='1min', start_date='2025-06-20 09:00:00', end_date='2025-06-20 19:00:00')

数据样例

       ts_code           trade_time  close   open   high    low        vol      amount

0 510330.SH 2025-06-20 15:00:00 3.991 3.991 3.992 3.990 800600.0 3194805.0
1 510330.SH 2025-06-20 14:59:00 3.991 3.990 3.991 3.989 182500.0 728177.0
2 510330.SH 2025-06-20 14:58:00 3.990 3.992 3.992 3.990 113700.0 453763.0
3 510330.SH 2025-06-20 14:57:00 3.992 3.992 3.992 3.991 17400.0 69460.0
4 510330.SH 2025-06-20 14:56:00 3.992 3.992 3.992 3.991 447500.0 1786373.0
.. ... ... ... ... ... ... ... ...
236 510330.SH 2025-06-20 09:34:00 3.994 3.994 3.995 3.994 2528100.0 10097818.0
237 510330.SH 2025-06-20 09:33:00 3.994 3.991 3.994 3.991 143300.0 572084.0
238 510330.SH 2025-06-20 09:32:00 3.992 3.990 3.993 3.990 1118500.0 4463264.0
239 510330.SH 2025-06-20 09:31:00 3.988 3.984 3.992 3.984 1176100.0 4691600.0
240 510330.SH 2025-06-20 09:30:00 3.983 3.983 3.983 3.983 20700.0 82448.0

ETF 实时日线
接口：rt_etf_k
描述：获取 ETF 实时日 k 线行情，支持按 ETF 代码或代码通配符一次性提取全部 ETF 实时日 k 线行情
限量：单次最大可提取 2000 条数据
积分：本接口是单独开权限的数据，单独申请权限请参考权限列表

输入参数

名称 类型 必选 描述
ts_code str Y 支持通配符方式，e.g. 5*.SH、15*.SZ、159101.SZ
topic str Y 分类参数，取上海 ETF 时，需要输入'HQ_FND_TICK'，参考下面例子

注：ts_code 代码一定要带.SH/.SZ/.BJ 后缀

输出参数

名称 类型 默认显示 描述
ts_code str Y ETF 代码
name None Y ETF 名称
pre_close float Y 昨收价
high float Y 最高价
open float Y 开盘价
low float Y 最低价
close float Y 收盘价（最新价）
vol int Y 成交量（股）
amount int Y 成交金额（元）
num int Y 开盘以来成交笔数
ask_volume1 int N 委托卖盘（股）
bid_volume1 int N 委托买盘（股）
trade_time str N 交易时间

接口示例

#获取今日开盘以来所有深市 ETF 实时日线和成交笔数
df = pro.rt_etf_k(ts_code='1\*.SZ')

#获取今日开盘以来沪市所有 ETF 实时日线和成交笔数
df = pro.rt_etf_k(ts_code='5\*.SH', topic='HQ_FND_TICK')

数据示例

       ts_code      name      pre_close     high     open     low    close        vol     amount    num

0 520860.SH 港股通科 1.024 1.054 1.048 1.041 1.048 15071600 15780985 307
1 515320.SH 电子 50 1.173 1.211 1.184 1.184 1.206 1830600 2191339 98
2 511600.SH 货币 ETF 100.008 100.003 100.002 99.999 100.000 12022 1202204 28
3 501075.SH 科创主题 2.350 2.400 2.357 2.357 2.400 4200 10040 11
4 589990.SH 科创板综 1.282 1.311 1.280 1.280 1.305 4178600 5413728 147
.. ... ... ... ... ... ... ... ... ... ...
933 516590.SH 电动汽车 1.244 1.277 1.252 1.252 1.270 1380800 1748398 79
934 502048.SH 50LOF 1.224 1.238 1.235 1.214 1.218 3200 3908 5
935 515850.SH 证券龙头 1.519 1.538 1.523 1.520 1.523 11460000 17484157 688
936 515790.SH 光伏 ETF 0.912 0.929 0.919 0.910 0.923 411566128 379094370 14939
937 516190.SH 文娱 ETF 1.137 1.154 1.151 1.146 1.151 1031700 1186303 87

ETF 日线行情
接口：fund_daily
描述：获取 ETF 行情每日收盘后成交数据，历史超过 10 年
限量：单次最大 2000 行记录，可以根据 ETF 代码和日期循环获取历史，总量不限制
积分：需要至少 2000 积分才可以调取，具体请参阅积分获取办法

输入参数

名称 类型 必选 描述
ts_code str N 基金代码
trade_date str N 交易日期(YYYYMMDD 格式，下同)
start_date str N 开始日期
end_date str N 结束日期

输出参数

名称 类型 默认显示 描述
ts_code str Y TS 代码
trade_date str Y 交易日期
open float Y 开盘价(元)
high float Y 最高价(元)
low float Y 最低价(元)
close float Y 收盘价(元)
pre_close float Y 昨收盘价(元)
change float Y 涨跌额(元)
pct_chg float Y 涨跌幅(%)
vol float Y 成交量(手)
amount float Y 成交额(千元)

接口示例

pro = ts.pro_api()

#获取”沪深 300ETF 华夏”ETF2025 年以来的行情，并通过 fields 参数指定输出了部分字段
df = pro.fund_daily(ts_code='510330.SH', start_date='20250101', end_date='20250618', fields='trade_date,open,high,low,close,vol,amount')

数据示例

trade_date open high low close vol amount
0 20250618 4.008 4.024 3.996 4.017 382896.00 153574.446
1 20250617 4.015 4.022 4.000 4.014 440272.04 176617.125
2 20250616 4.000 4.018 3.996 4.015 423526.00 169788.251
3 20250613 4.023 4.028 3.992 4.004 1216787.53 487632.318
4 20250612 4.023 4.039 4.005 4.032 574727.00 231356.321
.. ... ... ... ... ... ... ...
104 20250108 3.971 3.992 3.908 3.963 3200416.00 1267465.456
105 20250107 3.939 3.974 3.929 3.973 2239739.00 885818.954
106 20250106 3.950 3.964 3.917 3.943 1583794.00 624004.760
107 20250103 4.002 4.013 3.944 3.963 2025111.00 805573.289
108 20250102 4.110 4.117 3.973 4.001 1768592.00 714820.885

基金复权因子
接口：fund_adj
描述：获取基金复权因子，用于计算基金复权行情
限量：单次最大提取 2000 行记录，可循环提取，数据总量不限制
积分：用户积 600 积分可调取，超过 5000 积分以上频次相对较高。具体请参阅积分获取办法

复权行情实现参考：

后复权 = 当日最新价 × 当日复权因子
前复权 = 当日最新价 ÷ 最新复权因子

输入参数

名称 类型 必选 描述
ts_code str N TS 基金代码（支持多只基金输入）
trade_date str N 交易日期（格式：yyyymmdd，下同）
start_date str N 开始日期
end_date str N 结束日期
offset str N 开始行数
limit str N 最大行数

输出参数

名称 类型 默认显示 描述
ts_code str Y ts 基金代码
trade_date str Y 交易日期
adj_factor float Y 复权因子
接口使用

pro = ts.pro_api()

df = pro.fund_adj(ts_code='513100.SH', start_date='20190101', end_date='20190926')

数据示例

     ts_code    trade_date  adj_factor

0 513100.SH 20190926 1.0
1 513100.SH 20190925 1.0
2 513100.SH 20190924 1.0
3 513100.SH 20190923 1.0
4 513100.SH 20190920 1.0
5 513100.SH 20190919 1.0
6 513100.SH 20190918 1.0
7 513100.SH 20190917 1.0
8 513100.SH 20190916 1.0
9 513100.SH 20190912 1.0
10 513100.SH 20190911 1.0
11 513100.SH 20190910 1.0
12 513100.SH 20190909 1.0
13 513100.SH 20190906 1.0
14 513100.SH 20190905 1.0
15 513100.SH 20190904 1.0
16 513100.SH 20190903 1.0
17 513100.SH 20190902 1.0
18 513100.SH 20190830 1.0
19 513100.SH 20190829 1.0
20 513100.SH 20190828 1.0
