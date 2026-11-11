---
name: genius-financial-query
display_name: 巨灵财经数据查询
display_name_en: Genius Financial Query
description: 查询股票、基金、港股、期货、债券、期权、指数及宏观经济等金融数据。当用户询问行情、财报、净值、分红、资金流向、宏观指标，或需要调用 Genius 金融数据 API 时使用。
description_zh: 基于巨灵财经数据库，支持通过自然语言检索股票、基金、港股、期货、债券、期权、资讯、指数与宏观经济等领域的金融数据。
description_en: Based on the Juling financial database, enabling natural-language retrieval of financial data interfaces across stocks, funds, HK stocks, futures, bonds, options, news, indices and macroeconomics.
examples_zh:
  - "查询贵州茅台（600519）最近一年的日线行情"
  - "查看华安张江产业园 REIT（508000）的实时行情快照"
  - "获取宁德时代最新一期资产负债表的总资产和净资产"
examples_en:
  - "Query the daily quotes of Kweichow Moutai (600519) over the past year"
  - "Show the real-time quote snapshot of REIT 508000"
  - "Get total assets and net assets from the latest balance sheet of CATL"
version: 1.0.0
author: "Genius"
---

# Genius Financial Query Skill

## 技能说明

专业的金融数据查询技能，支持股票、基金、期货、债券、期权等多种金融工具的数据查询。

### 核心功能

1. **找接口** - 覆盖股票、基金、期货、债券、期权、指数、宏观等领域的全量金融数据接口（完整清单见 @references/field_mapping.json）
2. **调用 API** - 直接调用指定的 HTTP API
3. **字段映射** - 自动将字段代码映射为中文

### 目录结构

```
genius-financial-query/
├── SKILL.md                   # 技能定义（YAML frontmatter + 指令正文）
├── scripts/
│   └── handler.py             # 核心处理逻辑（API 调用、字段映射）
└── references/
    └── field_mapping.json     # 字段映射表（接口/字段/分类的唯一数据源）
```

## 配置项

### 必需配置

技能运行仅需一个 API Token，注入方式取决于宿主平台：

- **环境变量（通用，推荐）**：设置 `GENIUS_API_TOKEN`，代码中通过 `os.environ.get('GENIUS_API_TOKEN')` 读取
- **平台配置**：由宿主平台注入，如 OpenClaw 在 `~/.openclaw/openclaw.json` 的 `skills.entries.genius-financial-query.apiKey` 中配置
- **代码传参**：直接传入 `create_handler({'apiToken': 'your-token'})`

> 注意：不要把 Token 硬编码到脚本或提交到代码仓库。

**获取 Token 步骤**：
1. 访问 https://science.z3cloud.com.cn/api-genius
2. 注册账号并登录
3. 进入个人中心创建 API Token
4. 复制 Token 并配置

## 使用方式

### 基本查询

```python
from scripts.handler import create_handler
import os

config = {
    'apiToken': os.environ.get('GENIUS_API_TOKEN', '')
}
handler = create_handler(config)

result = handler.execute(
    apiName="stk_list",
    params={"SEC_CODE": "600519"},
    fields="SEC_CODE,SEC_SNAME",
    sort="LIST_DATE,DESC",
    pageNum=1,
    pageSize=10
)
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| apiName | str | 是 | 接口名称 | `"stk_list"` |
| params | dict | 否 | 查询参数 | `{"SEC_CODE": "600519"}` |
| fields | str | 否 | 返回字段（逗号分隔） | `"SEC_CODE,SEC_SNAME"` |
| sort | str | 否 | 排序（字段名,方向） | `"LIST_DATE,DESC"` |
| mode | int | 否 | 返回模式（1-数组格式，2-键值对格式，默认1） | `1` 或 `2` |
| pageNum | int | 否 | 页码（默认1） | `1` |
| pageSize | int | 否 | 每页条数（最多 1000；分页查询最多可获取前 20000 条，建议增加筛选条件缩小范围） | `100` |

### 返回模式说明

**mode=1（数组格式，默认）**：

```json
{
    "code": 200,
    "msg": null,
    "data": {
        "fields": ["SEC_CODE", "TRADE_DATE", "EX_FACTOR"],
        "items": [
            ["000001", "1991-04-03", 1.409681]
        ],
        "kvData": null,
        "total": 2349,
        "size": 100,
        "current": 1,
        "pages": 24,
        "hasMore": true
    }
}
```

**mode=2（键值对格式，推荐）**：

```json
{
    "code": 200,
    "msg": null,
    "data": {
        "fields": null,
        "items": null,
        "kvData": [
            {
                "SEC_CODE": "000001",
                "TRADE_DATE": "1991-04-03",
                "EX_FACTOR": 1.409681
            }
        ],
        "total": 2349,
        "size": 100,
        "current": 1,
        "pages": 24,
        "hasMore": true
    }
}
```

### 使用示例

```python
# 键值对格式返回（推荐，更易读）
result = handler.execute(
    apiName="stk_list",
    params={"SEC_CODE": "600519"},
    fields: "SEC_CODE,SEC_SNAME",
    sort: "LIST_DATE,DESC",
    mode=2,
    pageNum=1,
    pageSize=10
)
```

### 时间范围查询

使用 `SD_字段名` 和 `ED_字段名` 参数格式：

```python
result = handler.execute(
    apiName="stk_trade_cal",
    params={
        "SD_TRADEDATE": "2025-01-01",
        "ED_TRADEDATE": "2025-12-31"
    },
    fields: "SEC_CODE,TRADE_DATE,EX_FACTOR",
    sort: "TRADE_DATE,DESC",
    mode=2,
    pageNum=1,
    pageSize=365
)
```

### 排序查询

```python
# 检查字段是否支持排序
sortable = handler.get_sortable_fields("stk_list")

result = handler.execute(
    apiName="stk_list",
    params={"SEC_CODE": "600519"},
    fields: "SEC_CODE,SEC_SNAME",
    sort: "LIST_DATE,DESC",
    mode=2,
    pageNum=1,
    pageSize=10
)
```

## 支持的接口

### 分类层级

| 一级分类 | 子分类 | 接口数 |
|---------|--------|--------|
| 实时行情 (sshq) | - | 4 |
| 股票数据 (gpsj) | 基础数据、行情数据、财务数据、股本股东、特色数据、融资融券、资金流向、打板专题 | 54 |
| 港股数据 (ggsj) | 基础数据、行情数据、财务数据 | 12 |
| 公募基金 (gmjj) | 基本资料、人员信息、相关机构、发行送配、申购赎回、持有人与份额变动、资产配置、交易行情、财务数据、公告资讯 | 37 |
| ETF专题 (etfzt) | - | 5 |
| 指数专题 (zszt) | 基础数据、行情数据、申万指数、衍生统计 | 12 |
| 债券专题 (zqzt) | - | 11 |
| 期货数据 (qhsj) | - | 5 |
| 现货数据 (xhsj) | - | 2 |
| 期权数据 (qqsj) | - | 2 |
| 宏观经济 (hgjj) | 国内宏观（热度指标、利率数据、国民经济、价格指数、金融信息、景气度）、国际宏观（美国利率） | 58 |
| 资讯专题 (zxzt) | 公司公告、互动易、新闻报刊、研究报告、自有资讯 | 9 |
| reits基金 (reits) | 产品要素、财务数据、底层数据、实时行情 | 25 |

> 注：上表仅为分类概览，接口数量会随文档更新变化，实时准确的接口/字段清单以 @references/field_mapping.json 为准（见其中 `totalInterfaces`、`totalOutputFields` 字段）。

### 常用接口

| 接口代码 | 名称 | 说明 |
|---------|------|------|
| stk_list | 股票列表 | 获取股票基础信息 |
| stk_inc | 利润表 | 获取利润表数据 |
| stk_bal_sheet | 资产负债表 | 获取资产负债表数据 |
| stk_cash_flow | 现金流量表 | 获取现金流量表数据 |
| hk_list | 港股列表 | 获取港股基础信息 |
| fund_list | 基金列表 | 获取基金基础信息 |
| etf_info | ETF信息 | 获取ETF基础信息 |
| fut_cont_info | 期货合约信息 | 获取期货合约信息 |

完整接口信息见 @references/field_mapping.json（AI 执行技能时读取该文件作为上下文，用于找接口、确认输入/输出参数）。

## 返回格式

### 成功响应

```json
{
    "code": 200,
    "msg": null,
    "data": {
        "fields": ["SEC_CODE", "TRADE_DATE", "EX_FACTOR"],
        "items": [
            ["000001", "1991-04-03", 1.409681]
        ],
        "kvData": null,
        "total": 2349,
        "size": 100,
        "current": 1,
        "pages": 24,
        "hasMore": true
    }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码（200-成功） |
| msg | string/null | 错误信息 |
| data.fields | array | 字段名列表（mode=1时有效） |
| data.items | array | 数据数组（mode=1时为二维数组） |
| data.kvData | array | 键值对数据（mode=2时有效） |
| data.total | int | 估算记录总数，依赖缓存，可能与实时结果存在偏差，不建议用于分页判断 |
| data.size | int | 当前页码的记录数 |
| data.current | int | 所属页码 |
| data.pages | int | 估算总页数，依赖缓存，可能与实时结果存在偏差，不建议用于分页判断 |
| data.hasMore | boolean | 是否还有下一页，分页查询请优先以此字段为准 |

> 分页建议：翻页终止条件以 `hasMore` 为准（`true` 表示还有下一页，可将 `pageNum` 加 1 继续查询）；`total`、`pages` 为缓存估算值，仅供参考，不要用于分页判断。

## 错误处理

| 错误 | 说明 |
|-----|------|
| Token 未配置 | 请配置 GENIUS_API_TOKEN 环境变量 |
| 接口不存在 | 请检查 apiName 是否正确 |
| 参数错误 | 请检查 params 参数 |

## 技术栈

- Python 3.8+
- requests (HTTP 请求)
- json (数据解析)


