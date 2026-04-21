# Genius Financial Query Skill

## 技能说明

专业的金融数据查询技能，支持股票、基金、期货、债券、期权等多种金融工具的数据查询。

### 核心功能

1. **找接口** - 126 个金融数据接口，覆盖 43 个分类
2. **调用 API** - 直接调用指定的 HTTP API
3. **字段映射** - 自动将字段代码映射为中文

### 目录结构

```
genius-financial-query/
├── SKILL.md                   # 主文件
├── scripts/
│   └── handler.py            # 核心处理逻辑
└── references/
    └── field_mapping.json    # 字段映射表（126 接口，2017 字段）
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
1. 访问 http://science.z3cloud.com.cn/api-genius
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
| 股票数据 (gpsj) | 基础数据、行情数据、财务数据、股本股东、特色数据、融资融券、资金流向、打板专题 | 49 |
| 港股数据 (ggsj) | 基础数据、行情数据、财务数据 | 10 |
| 公募基金 (gmjj) | - | 4 |
| ETF专题 (etfzt) | - | 5 |
| 指数专题 (zszt) | 基础数据、行情数据、申万指数、衍生统计 | 12 |
| 债券专题 (zqzt) | - | 7 |
| 期货数据 (qhsj) | - | 5 |
| 现货数据 (xhsj) | - | 2 |
| 期权数据 (qqsj) | - | 2 |
| 宏观经济 (hgjj) | 国内宏观、国际宏观 | 9 |
| 资讯专题 (zxzt) | 公司公告、互动易、新闻报刊、研究报告、自有资讯 | 9 |
| 量化因子 (lhyz) | Barra风险模型（CNE5/CNE6） | 10 |

**总计**: 126 个接口，2017 个字段

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

### v4.0.0 (2026-04-21)
- 接口数量从 83 增加到 126
- 字段数量从 1292 增加到 2017
- 添加分类层级关系支持
- 添加输入参数映射
- 适配 OpenClaw 部署格式

### v3.1.0 (2026-04-10)
- 添加排序字段检测功能
- 添加时间范围查询支持（SD_ 和 ED_ 前缀）
