---
name: genius-financial-query
display_name: 巨灵财经数据查询
display_name_en: Genius Financial Data Query
description: 基于巨灵财经数据库查询 A股、港股、基金、REITs、ETF、指数、债券、期货、期权、现货、宏观经济与资讯公告数据。当用户询问行情、财报、净值、分红、股东、资金流向、龙虎榜、宏观指标，或需要调用 Genius 金融数据 API 时使用。
description_zh: 基于巨灵财经数据库，通过自然语言检索股票、基金、港股、期货、债券、期权、指数与宏观经济等领域的金融数据接口。
description_en: Search and call Genius financial data APIs for A-shares, HK stocks, funds, REITs, ETFs, indices, bonds, futures, options and macro-economic data.
version: 1.1.0
---

# 巨灵财经数据查询

236 个金融数据接口 + 3587 个字段的离线检索能力，取数时调用巨灵 HTTP API。

## 何时使用

- 查行情：个股/港股/ETF/指数/期货/期权的日线、实时快照、分时
- 查财报：三大报表、财务指标、业绩预告、主营业务构成
- 查基金：净值、份额规模、资产配置、基金经理
- 查特色数据：分红送股、前十大股东、股东人数、限售解禁、龙虎榜、融资融券、资金流向
- 查宏观：GDP、CPI、货币供应、Shibor、美国利率
- 查资讯：上市公司公告、新闻、7×24 快讯、券商研报
- 查 REITs：定价认购、财务报表、底层资产运营指标

**不适用**：需要自行建模预测、非中国内地市场为主的数据需求、或实时逐笔成交高频数据。

## 30 秒上手

所有能力都可以用命令行完成，**不需要写 Python**：

```bash
# 1) 找接口（离线，不需要 Token）
python scripts/query.py --search 日线

# 2) 看接口的参数和字段（离线）
python scripts/query.py --describe stk_daily_hist

# 3) 取数（需要 Token，见「配置」一节）
python scripts/query.py --api stk_daily_hist \
  --params '{"SEC_CODE":"600519","SD_TRADEDATE":"2025-11-01","ED_TRADEDATE":"2026-11-01"}' \
  --fields SEC_CODE,TRADEDATE,TCLOSE --sort TRADEDATE,DESC --mode 2 --page-size 300
```

## ⚠️ 硬约束：禁止整读字段映射文件

`references/field_mapping.json` 约 **1.3 MB / 40 万+ token**。**禁止用文件读取工具打开它**，一次整读会占满上下文窗口。

需要查接口或字段时，按下面任一方式按需检索：

| 目的 | 命令 |
|---|---|
| 按关键词找接口 | `python scripts/query.py --search 资产负债表` |
| 按关键词找字段 | `python scripts/query.py --search-field 资产总计` |
| 看单个接口全貌 | `python scripts/query.py --describe stk_bal_sheet` |
| 看分类树 | `python scripts/query.py --tree` |
| 列某分类下的接口 | `python scripts/query.py --list --category gpsj` |

同理，`get_interfaces()` 默认返回精简清单（约 38 KB）；**不要传 `brief=False`**（约 700 KB），需要说明时用 `search_interfaces()`。

## 标准工作流

1. **定位接口**：先查下面的「业务词 → 接口」路由表；没命中再用 `--search 关键词`。
2. **确认参数**：`--describe <接口代码>`，重点看 `inputParams` 的 `required` 和字段 `description` 里的格式/单位。
3. **取数**：普通接口用 `--api <接口代码>` 带 `--params`、`--fields`、`--sort`；**财报类接口一律用 `--latest-report`**（见「口径约定」，直接 `--api` 会取到上年同期比较列）。
4. **分页**：`hasMore` 为 `true` 时把 `--page-num` 加 1 继续。`total`/`pages` 通常精确，但口径不承诺，**翻页终止一律以 `hasMore` 为准**。
5. **汇报**：字段名已是中文；口径与单位在字段 `description` 里（如 `[单位：元]`、`[单位：亿元]`），引用数据时一并说明。

## 业务词 → 接口 路由表

以下映射均经实盘调用验证。

| 业务需求 | 接口代码 | 关键参数 |
|---|---|---|
| 股票列表 / 简称 | `stk_list` | `SEC_CODE`、`SEC_SNAME` |
| 个股历史日线 | `stk_daily_hist` | `SEC_CODE` + `SD_TRADEDATE`/`ED_TRADEDATE` |
| 个股周线 / 月线 | `stk_weekly` / `stk_monthly` | 同上 |
| 复权因子 | `stk_adj_fct` | `SEC_CODE` + `SD_TRADE_DATE`/`ED_TRADE_DATE`（注意下划线） |
| 利润表 | `stk_inc` | `SEC_CODE`；取数用 `--latest-report` |
| 资产负债表 | `stk_bal_sheet` | `SEC_CODE` + `RPT_TYPE=合并`；取数用 `--latest-report` |
| 现金流量表 | `stk_cash_flow` | `SEC_CODE` + `RPT_TYPE`；取数用 `--latest-report` |
| 财务指标 | `stk_fin_ratio` | `SEC_CODE` |
| 业绩预告 / 快报 | `stk_earn_fct` / `stk_earn_exp` | `SEC_CODE` |
| 主营业务构成 | `stk_bus_brk` | `SEC_CODE` |
| 分红送股 | `stk_div` | `SEC_CODE` + `SD_RPT_DATE`/`ED_RPT_DATE` |
| 前十大股东 | `stk_top10_holder` | `SEC_CODE`、`ENDDATE` |
| 股东人数 | `stk_holder_count` | `SEC_CODE` |
| 限售股解禁 | `stk_lck_rel` | `SEC_CODE` |
| 个股资金流向 | `stk_money_flow` | `SEC_CODE` |
| 沪深港通资金流向 | `stk_hk_conn_money_flow` | — |
| 融资融券汇总 / 明细 | `stk_mrg_sum` / `stk_mrg_dtl` | `SEC_CODE` |
| 龙虎榜 | `stk_drg_tiger_daily` | `SEC_CODE`、交易日 |
| 港股基础信息 | `hk_list` | `SEC_CODE` |
| 港股日行情 / 复权日行情 | `hk_daily` / `hk_adj_daily` | `SEC_CODE` + `SD_TRADEDATE`/`ED_TRADEDATE` |
| 港股复权因子 | `hk_adj_fct` | `SEC_CODE` |
| 基金净值 | `fund_nav` | **`FUND_CODE`**（不是 SEC_CODE）+ `SD_ENDDATE` |
| 场内基金行情 | `fund_exc_mkt` | `FUND_CODE` |
| 基金投资策略 / 风险收益特征 | `fund_inv_risk` | **`FUND_CODE`**；历史版本见 `fund_inv_risk_hist` |
| 基金基本资料（简介、费率） | `fund_list` / `fund_fee` | **`FUND_CODE`** |
| ETF 基础信息 / 日线 | `etf_info` / `etf_daily` | `SEC_CODE` |
| ETF 复权因子 | `etf_adj_fct` | `SEC_CODE` |
| ETF 份额规模 | `etf_share_scale` | `SEC_CODE` |
| 指数日 / 周 / 月行情 | `indx_daily` / `indx_weekly` / `indx_monthly` | `SEC_CODE` + `SD_TRADEDATE`/`ED_TRADEDATE` |
| 期货合约 / 日行情 | `fut_cont_info` / `fut_daily` | `SEC_CODE` |
| 期权合约 / 行情 | `opt_cont_info` / `opt_daily` | `SEC_CODE` |
| 贵金属现货行情 | `fut_spot_metal_quote` | `SEC_CODE` |
| 国内生产总值 | `mac_gdp` | —（按 `RPT_QTR` 排序） |
| CPI | `mac_cpi` | — |
| 货币供应量 | `mac_mny_sply` | — |
| Shibor / 美国国债收益率 | `mac_shibor` / `mac_us_tsy_yield` | — |
| 美国 CPI / 失业率 / 美元指数 | `mac_us_cpi` / `mac_us_uep` / `mac_us_usdx` | — |
| 上市公司公告 | `news_ann` | `SEC_CODE` + `SD_DECLAREDATE`/`ED_DECLAREDATE` |
| 新闻 / 7×24 快讯 | `news_article` / `news_24flash` | — |
| 券商研究报告 | `news_res_rpt` | — |
| REITs 定价 / 认购 | `reits_price` / `reits_sub` | `FUND_CODE` |
| REITs 财务报表 | `reits_bal` / `reits_cf` / `reits_profit` | **`FUND_CODE`** + `SD_ENDDATE` |
| REITs 底层资产运营 | `reits_proj_idx` / `reits_asset_perf` | `FUND_CODE` |

表里没有的需求，用 `--search 关键词` 找；一个关键词常有多个候选（例如「日线」会同时命中 `stk_daily_hist` 和 `etf_daily`），按标的类型选。

## 分类体系

13 个一级分类、236 个接口（`python scripts/query.py --tree` 可查完整树）：

| 一级分类 | 代码 | 接口数 | 主要子分类 |
|---|---|---|---|
| 实时行情 | `sshq` | 4 | 快照、K线、分时、成交明细 |
| 股票数据 | `gpsj` | 54 | 基础/行情/财务/股本股东/特色/融资融券/资金流向/打板 |
| 港股数据 | `ggsj` | 12 | 基础/行情/财务 |
| 公募基金 | `gmjj` | 37 | 10 个子分类，含净值、份额、资产配置 |
| ETF专题 | `etfzt` | 5 | 信息、基准、日线、复权、份额 |
| 指数专题 | `zszt` | 12 | 基础/行情/申万指数/衍生统计 |
| 债券专题 | `zqzt` | 11 | — |
| 期货数据 | `qhsj` | 5 | 合约、日行情、持仓排名、主力连续 |
| 现货数据 | `xhsj` | 2 | 贵金属 |
| 期权数据 | `qqsj` | 2 | 合约、行情 |
| 宏观经济 | `hgjj` | 58 | 国内宏观（6 个子分类 52 个）、国际宏观（美国利率 6 个） |
| 资讯专题 | `zxzt` | 9 | 公告、互动易、新闻、研报、自有资讯 |
| reits基金 | `reits` | 25 | 产品要素、财务数据、底层数据、实时行情 |

## 参数约定

### 证券代码

| 数据族 | 参数名 | 示例 |
|---|---|---|
| A股 / 港股 / ETF / 指数 / 期货 / 期权 | `SEC_CODE` | `600519`、`000001`、`508000` |
| 公募基金 / REITs | `FUND_CODE` | `000001`、`508000` |
| 实时行情三个接口 | `stocks` / `sid` / `securityId` | 见下方「特殊接口」 |

传错参数名不会静默返回空，服务端会明确报错，例如：`无效参数：SEC_CODE，该接口不支持此参数`。

**注意跨域同码歧义**：同一代码在不同域指向不同实体，且此时服务端不报错——`000001` 传 `SEC_CODE` 是平安银行，传 `FUND_CODE` 是华夏成长混合。务必先确认业务域再选参数名。

### 时间范围

统一用 `SD_字段名` 与 `ED_字段名` 前缀。注意字段本身可能已含下划线：

| 接口 | 时间字段 | 范围参数 |
|---|---|---|
| `stk_daily_hist` | `TRADEDATE` | `SD_TRADEDATE` / `ED_TRADEDATE` |
| `stk_bal_sheet` | `RPT_DATE` | `SD_RPT_DATE` / `ED_RPT_DATE` |
| `stk_adj_fct` | `TRADE_DATE` | `SD_TRADE_DATE` / `ED_TRADE_DATE` |
| `fund_nav` | `ENDDATE` | `SD_ENDDATE` / `ED_ENDDATE` |

实际可用的范围字段以 `--describe` 返回的 `inputParams` 为准——接口里出现了 `SD_xxx` 就说明该字段支持范围查询。

### 排序与分页

- `--sort 字段,ASC|DESC`，字段需支持排序（`get_sortable_fields()` 可查，字段 `description` 含「支持排序」）。
- `--page-size` 单页最多 1000，默认 100。
- 翻页终止条件**以 `hasMore` 为准**；`total`、`pages` 实测通常精确，可作进度参考但别当终止依据。单页最大 1000，取全量按页循环聚合（一年日线约 242 条，一页可取完）。

### 返回模式

- `--mode 2`（默认）：键值对，最易读，推荐。
- `--mode 1`：`fields` + `items` 数组格式，适合按列处理。

## 特殊接口：实时行情三兄弟

`sshq` 分类下的 `hqs`、`rtmin`、`quot-kline` 使用**另一套参数**，且不支持 `fields` / `sort` / `mode`，容易踩坑：

| 接口 | 用途 | 参数格式 | 备注 |
|---|---|---|---|
| `hqs` | 实时快照 | `{"stocks": [1600519], "env": [1,2]}` | **数组**，元素为「市场前缀+代码」：上交所补 `1`，深交所补 `2`。`env` 1=精简快照、2=扩展快照、3=五档盘口 |
| `rtmin` | 当日分时线 | `{"sid": 1600519}` | **必须是整数**，传字符串会报「JRJ 网关返回错误：40000」 |
| `quot-kline` | K线（1分钟/日/周/月） | `{"securityId": 1600519, "type": "day", "range.begin": "20261001"}` | `range.begin` 必填，格式 `yyyyMMdd` |

市场前缀规则：代码以 6、50、51、52、53、56、68、69、000 开头 → 前缀 `1`（上交所）；以 00、30、15、16、399 开头 → 前缀 `2`（深交所）。例如贵州茅台 `600519` → `1600519`。

> 若只需历史日线，用 `stk_daily_hist` 更省事（支持 `fields` / `sort` / 分页，且字段已中文化）。

## 返回格式

`execute()`（即 `--api`）的返回结构：

```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "kvData": [
      {"证券代码": "600519", "收盘价": 1439.0, "交易日期": "2026-11-10"}
    ],
    "columns": [
      {"code": "SEC_CODE", "label": "证券代码"},
      {"code": "TCLOSE", "label": "收盘价"}
    ],
    "total": 6039, "current": 1, "pages": 61, "size": 100, "hasMore": true
  },
  "metadata": {"apiName": "stk_daily_hist", "mode": 2, "total": 6039, "hasMore": true}
}
```

要点：

- 列名已被本地化为**中文**，不要用 `SEC_CODE` 这类英文字段名去取 `kvData` 里的值；需要英文代码时看 `columns` 里的 `code`。
- 同接口出现重名字段时，后一个自动带上字段代码，形如 `经营活动产生的现金流量净额(C410000)`，不会互相覆盖。
- `mode=1` 时 `data` 里是 `fields`（中文列名数组）+ `items`（对象数组），同样附带 `columns`。
- 失败时 `success=false` 且 `message` 给出原因，`data` 为 `null`。
- 与巨灵原始 HTTP 响应不同：原始响应是 `{"code":200,"msg":null,"data":{...}}` 信封，"返回格式"一节描述的是本技能加工后的结果。

## 口径约定

### 最新一期财报（有坑，务必按其执行）

财务报表类接口（`stk_bal_sheet`、`stk_inc`、`stk_cash_flow`、`reits_bal` 等）**同一 `RPT_DATE` 会返回 2 行**：

- **本期行**：`ENDDATE == RPT_DATE`（这才是你要的当季/当年数）
- **比较列**：`ENDDATE` 为上一年末（同一报告期的上年同期数，用于对比）

按 `RPT_DATE` 排序时，**比较列与本期行的先后顺序不保证稳定**——同一报告期内谁在前是服务端返回顺序决定的，可能本期在前、也可能比较列在前。因此 `sort=RPT_DATE,DESC` 取第一条会**随机**拿到上年同期数：`success=true`、有值、有单位、量级也合理，不报错，数字却是错的。**绝不能用「取第一条再看一眼」来判断**。

判断本期的唯一可靠依据是 `ENDDATE == RPT_DATE`。

**正确做法**：用 `--latest-report`，它按 `RPT_DATE` 分组后只取 `ENDDATE == RPT_DATE` 的行：

```bash
python scripts/query.py --latest-report stk_bal_sheet --code 600519 \
  --fields SEC_CODE,ENDDATE,RPT_TYPE,B100000,B200000
```

```json
{"success": true, "message": "已取到最新一期（报告期 2026-09-30）",
 "data": {"报表日期": "2026-09-30", "截止日期": "2026-09-30", "报表类型": "合并",
          "资产总计": 318304891882.72, "负债合计": 37883274859.87}}
```

`--latest-report` 的默认口径是 **`RPT_TYPE=合并`**（结果 `metadata.rptType` 会回显）；需要母公司口径传 `--rpt-type 母公司`，传空串则不做过滤。

返回里两个日期键：**`报表日期`（RPT_DATE）是公告口径的报告期标记，`截止日期`（ENDDATE）是数据实际对应的期末日**。本期行两者相等，比较列的 `截止日期` 为上年同期。

若自行写查询，等价写法是 `sort=ENDDATE,DESC` 后再筛 `ENDDATE == RPT_DATE`，或用 `ENDDATE=<报告期>` 精确锁定。**另外务必在 `--fields` 里带上 `ENDDATE`**，否则两行数据肉眼无法区分。

### 其他口径

- **合并 vs 母公司报表**：`stk_bal_sheet` / `stk_inc` / `stk_cash_flow` 用 `RPT_TYPE` 过滤，取值「合并」或「母公司」。`required` 虽为「否」，但**不过滤会把两种口径混在一起**，务必显式指定。
- **单位**：多数数值字段的 `description` 内标注 `[单位：元]`、`[单位：亿元]`、`[单位：%]`、`[单位：股]`。涨跌幅类字段（如 `CHNG_PCT`）的 `description` 未标单位，实际值已是**百分数**：`-0.4145` 表示 -0.4145%。宏观数据多为累计值（`RPT_QTR` 形如 `2026Q3`）。
- **复权**：`stk_daily_hist` 返回原始未复权价格；需要前复权/后复权时用 `stk_adj_fct` 的 `EX_FACTOR` 换算，或直接用 `hk_adj_daily` 这类已复权接口。
- **证券代码**：A 股为 6 位数字，不带交易所后缀，不要传 `600519.SH`。
- **返回值顺序**：`kvData` 每行的**键顺序不固定**，程序化取值必须按字段名访问，不能依赖位置。
- **日期区间**：`SD_`/`ED_` 为闭区间；非交易日自动跳过，因此「一年」通常少于 365 条。当日盘中数据可能尚未入库，取「今天」常为空属正常。
- **宏观发布节奏**：季度/月度指标存在公布滞后，取最新值时先确认 `RPT_QTR` / 统计月份是否符合预期。

## 常见错误

| 现象 | 原因 | 处理 |
|---|---|---|
| `无效的 token` | Token 未配置或失效 | 检查 `GENIUS_API_TOKEN` |
| `接口不存在：xxx` | `apiName` 拼错或不存在 | 用 `--search` 确认代码 |
| `无效参数：XXX，该接口不支持此参数` | 参数名不属于该接口（常见于把 `SEC_CODE` 传给 `fund_nav`） | `--describe` 看 `inputParams` |
| `参数 xxx 不能为空` | 该参数必填 | 补齐参数 |
| `JRJ 网关返回错误：40000` | 实时行情接口参数类型错误（应传数组却传了字符串，或反之） | 按「特殊接口」表格传参 |
| 返回空数组但接口成功 | 筛选条件过窄或代码不属于该市场 | 放宽条件、确认代码归属 |

## 配置

取数需要一个 API Token，三种注入方式任选：

1. **环境变量（推荐）**：`export GENIUS_API_TOKEN=your-token`
2. **配置文件**：`create_handler({"apiToken": "your-token"})`
3. **命令行**：`python scripts/query.py --token your-token --api ...`

获取 Token：访问 https://science.z3cloud.com.cn/api-genius 注册登录，在个人中心创建。

> Token 等同于账户凭证，不要写入脚本、不要提交到代码仓库、不要在回复中明文展示。未配置 Token 时，全部检索类命令（`--search`、`--describe`、`--tree`、`--list`）仍可正常离线使用。

## Python 用法（高级）

```python
import os
from scripts.handler import create_handler

handler = create_handler({'apiToken': os.environ.get('GENIUS_API_TOKEN', '')})

# 找接口 / 找字段
handler.search_interfaces('资产负债表', limit=5)
handler.search_fields('资产总计', limit=5)
handler.get_interface('stk_bal_sheet')

# 取数
result = handler.execute(
    apiName='stk_bal_sheet',
    params={'SEC_CODE': '600519', 'RPT_TYPE': '合并'},
    fields='SEC_CODE,ENDDATE,RPT_TYPE,B100000,B200000',
    sort='RPT_DATE,DESC',
    mode=2,
    pageNum=1,
    pageSize=1,
)
print(result['data']['kvData'])
```

主要方法：`execute`、`search_interfaces`、`search_fields`、`get_interfaces(brief=True)`、`get_interface`、`get_input_params`、`get_required_input_params`、`get_output_fields`、`get_sortable_fields`、`get_time_range_fields`、`build_time_range_params`、`get_category_tree`、`get_categories_by_parent`、`get_category_full_path`。

## 目录结构

```
genius-financial-query/
├── SKILL.md                      # 本文件
├── PRIVACY.md                    # 数据外发与 Token 处理说明
├── requirements.txt              # 仅 requests（取数时需要）
├── scripts/
│   ├── query.py                  # 命令行入口（推荐使用）
│   └── handler.py                # 核心逻辑：检索、取数、字段本地化
├── references/
│   └── field_mapping.json        # 1.3MB 分类/接口/字段映射（禁止整读）
```

## 技术栈

Python 3.8+、requests（仅取数时需要）。依赖见 `requirements.txt`。

## 数据处理说明

取数时会把接口名、查询参数与 Token 发送到 `science.z3cloud.com.cn`，不涉及本机文件与会话内容。详见 `PRIVACY.md`。金融数据版权归原始提供方所有，返回结果仅供研究参考，不构成投资建议。
