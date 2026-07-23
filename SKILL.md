# Genius Financial Query Skill

## 技能说明

专业的金融数据查询技能，支持股票、基金、期货、债券、期权等多种金融工具的数据查询。

### 核心功能

1. **找接口** - 241 个金融数据接口，覆盖 67 个分类
2. **调用 API** - 直接调用指定的 HTTP API
3. **字段映射** - 自动将字段代码映射为中文

### 目录结构

```
genius-financial-query/
├── SKILL.md                   # 主文件
├── scripts/
│   └── handler.py            # 核心处理逻辑
└── references/
    └── field_mapping.json    # 字段映射表（241 接口，3553 字段）
```

## 配置项

### 必需配置

在 `~/.openclaw/openclaw.json` 中配置：

```json
{
  "skills": {
    "entries": {
      "genius-financial-query": {
        "enabled": true,
        "apiKey": "your-genius-api-token"
      }
    }
  }
}
```

**获取 Token 步骤**：
1. 访问 http://science.z3cloud.com.cn
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
| pageSize | int | 否 | 每页条数（默认1000） | `10` |

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
        "total": 26308753,
        "size": 1,
        "current": 1,
        "pages": 26308753
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
        "total": 26308753,
        "size": 1,
        "current": 1,
        "pages": 26308753
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
| 股票数据 (gpsj) | 基础数据、行情数据、财务数据、股本股东、特色数据、融资融券、资金流向、打板专题 | 53 |
| 港股数据 (ggsj) | 基础数据、行情数据、财务数据 | 12 |
| 公募基金 (gmjj) | 基本资料、人员信息、相关机构、发行送配、申购赎回、持有人与份额变动、资产配置、交易行情、财务数据、公告资讯 | 37 |
| ETF 专题 (etfzt) | - | 5 |
| 指数专题 (zszt) | 基础数据、行情数据、申万指数、衍生统计 | 12 |
| 债券专题 (zqzt) | - | 11 |
| 期货数据 (qhsj) | - | 5 |
| 现货数据 (xhsj) | - | 2 |
| 期权数据 (qqsj) | - | 2 |
| 宏观经济 (hgjj) | 国内宏观、国际宏观 | 9 |
| 资讯专题 (zxzt) | 公司公告、互动易、新闻报刊、研究报告、自有资讯 | 9 |
| 量化因子 (lhyz) | Barra 风险模型（CNE5/CNE6） | 10 |
| reits 基金 (reits) | 产品要素、财务数据、底层数据、实时行情 | 29 |
| 观察指标 (hgzb) | 利率指标、宏观指标、热度指标、黄金指标 | 46 |
| 数据广场 (hgfx) | 市场估值、机构分析、ETF分析、宏观统计 | 6 |

**总计**: 241 个接口，3553 个字段

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

完整接口信息见 `references/field_mapping.json`。

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
        "total": 26308753,
        "size": 1,
        "current": 1,
        "pages": 26308753
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
| data.total | int | 总记录数 |
| data.size | int | 当前页大小 |
| data.current | int | 当前页码 |
| data.pages | int | 总页数 |

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

## 更新日志

### v7.3.0 (2026-07-23)
- 接口总数：241 个（-10）
- 字段总数：3553 个（-352）
- 适配最新接口文档（55 个文件）
- 部分接口删除和字段调整

### v7.1.0 (2026-07-07)
- 接口总数：252 个（+1）
- 字段总数：3908 个（+4）
- 适配最新接口文档（55 个文件）

### v7.0.0 (2026-07-03)
- 接口总数：251 个（+16）
- 字段总数：3904 个（+109）
- 分类总数：67 个（+5）
- 新增"数据广场"一级分类，包含市场估值、机构分析、ETF分析、宏观统计
- 观察指标分类新增 10 个接口（利率指标+2、宏观指标+8）
- 适配最新接口文档（55 个文件）

### v6.1.0 (2026-06-12)
- 接口总数：235 个（+2）
- 字段总数：3795 个（+27）
- 分类总数：62 个
- 新增接口：`hk_list_hear`（港股排队ipo）、`mac_ncd_yield`（同业存单收益率）
- 适配最新接口文档（51 个文件）

### v6.0.0 (2026-06-03)
- 接口总数：233 个（+35）
- 字段总数：3768 个（+176）
- 分类总数：62 个（+18）
- 新增"观察指标"一级分类，包含利率指标、宏观指标、热度指标、黄金指标
- 适配最新接口文档（51 个文件）

### v5.0.0 (2026-05-20)
- 接口总数：198 个
- 字段总数：3592 个
- 分类总数：44 个
- 适配最新接口文档（47 个文件）
- 修复接口名包含连字符的解析问题（如 quot-kline）

### v4.0.0 (2026-04-21)
- 接口数量从 83 增加到 126
- 字段数量从 1292 增加到 2017
- 添加分类层级关系支持
- 添加输入参数映射
- 适配 OpenClaw 部署格式

### v3.1.0 (2026-04-10)
- 添加排序字段检测功能
- 添加时间范围查询支持（SD_ 和 ED_ 前缀）
