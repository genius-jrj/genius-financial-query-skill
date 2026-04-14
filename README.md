# Genius Financial Query Skill

## 技能说明

专业的金融数据查询技能，支持股票、基金、期货、债券、期权等多种金融工具的数据查询。核心功能：

1. **找接口** - 100+个金融数据接口
2. **调用 API** - 直接调用指定的 HTTP API
3. **字段映射** - 自动将字段代码映射为中文

## 目录结构

```
genius-financial-query-skill/
├── SKILL.md                   # 主文件
├── scripts/
│   └── handler.py            # 核心处理逻辑
└── references/
    └── field_mapping.json    # 字段映射表
```

## 配置项

### 必需配置

```json
{
  "apiToken": "your-genius-api-token"
}
```

**获取 Token 步骤**：
1. 访问 http://science.z3cloud.com.cn
2. 注册账号并登录
3. 进入个人中心创建 API Token
4. 复制 Token 并粘贴到配置项

## 核心功能

### FinancialDataHandler

主要类，处理所有金融数据查询请求。

#### 主要方法

```python
# 执行 API 查询
result = handler.execute(
    apiName="stk_list",          # 接口名称
    params={"SEC_CODE": "600519"}, # 查询参数
    fields="SEC_CODE,SEC_SNAME",  # 返回字段（可选）
    sort="LIST_DATE,DESC",         # 排序（可选）
    pageNum=1,                     # 页码（可选）
    pageSize=1000                  # 每页条数（可选）
)

# 获取所有接口列表
interfaces = handler.get_interfaces()

# 获取单个接口详情
interface = handler.get_interface("stk_list")

# 获取支持排序的字段列表
sortable_fields = handler.get_sortable_fields("stk_list")

# 检查字段是否支持排序
is_sortable = handler.is_field_sortable("stk_list", "SEC_CODE")

# 获取时间范围查询可用字段
time_fields = handler.get_time_range_fields("stk_trade_cal")

# 构建时间范围查询参数
time_params = handler.build_time_range_params(
    fieldCode="TRADEDATE", 
    startDate="2025-01-01", 
    endDate="2025-12-31"
)
```

#### 返回格式

```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "fields": ["股票代码", "证券简称", "上市日期"],
        "items": [
            {"股票代码": "600519", "证券简称": "贵州茅台", "上市日期": "2001-08-27"}
        ],
        "total": 100,
        "current": 1,
        "pages": 1,
        "size": 10
    },
    "metadata": {
        "apiName": "stk_list",
        "total": 100
    }
}
```

## 支持的接口 

本技能支持 100+个金融数据接口，完整接口信息见 `references/field_mapping.json`。

### 接口分类

| 分类 | 接口数 | 说明 |
|-----|--------|------|
| 基础数据 | 13 | 股票列表、港股、指数基础信息等 |
| 财务数据 | 13 | 利润表、资产负债表、现金流量表等 |
| 行情数据 | 5 | 大宗交易、港股行情等 |
| 股本股东 | 7 | 前十大股东、股权质押等 |
| 公募基金 | 4 | 基金列表、净值等 |
| ETF专题 | 5 | ETF 列表、行情等 |
| 期货数据 | 5 | 期货合约、行情等 |
| 期权数据 | 2 | 期权合约、行情等 |
| 其他 | 32 | 利率、宏观、资金流向等 |


### 常用接口示例

#### 基础数据
- `stk_list` - 股票列表
- `stk_comp_info` - 上市公司基本信息
- `stk_ipo_info` - IPO 新股上市
- `hk_list` - 港股基础信息

#### 财务数据
- `stk_inc` - 利润表
- `stk_bal_sheet` - 资产负债表
- `stk_cash_flow` - 现金流量表
- `stk_fin_ratio` - 财务指标

#### 基金 & ETF
- `fund_list` - 基金列表
- `etf_info` - ETF 基础信息

#### 期货 & 期权
- `fut_cont_info` - 期货合约信息
- `opt_cont_info` - 期权合约信息

## 使用示例

### 示例 1: 查询股票列表

```python
result = handler.execute(
    apiName="stk_list",
    params={},
    pageSize=10
)
```

### 示例 2: 查询某只股票的财务数据

```python
result = handler.execute(
    apiName="stk_inc",
    params={"SEC_CODE": "600519"},
    pageSize=1
)
```

### 示例 3: 查询基金列表

```python
result = handler.execute(
    apiName="fund_list",
    pageSize=20
)
```

### 示例 4: 时间范围查询（SD_ 和 ED_ 前缀）

当需要查询时间范围时，使用 `SD_字段名` 和 `ED_字段名` 参数格式：

```python
# 方式一：直接构建参数
result = handler.execute(
    apiName="stk_trade_cal",
    params={
        "SD_TRADEDATE": "2025-01-01",  # 开始日期
        "ED_TRADEDATE": "2025-12-31"   # 结束日期
    },
    pageSize=365
)

# 方式二：使用 build_time_range_params 辅助方法
time_params = handler.build_time_range_params(
    fieldCode="TRADEDATE",
    startDate="2025-01-01",
    endDate="2025-12-31"
)
result = handler.execute(
    apiName="stk_trade_cal",
    params=time_params,
    pageSize=365
)
```

### 示例 5: 排序查询

在使用排序前，先检查字段是否支持排序：

```python
# 步骤 1：获取支持排序的字段列表
sortable_fields = handler.get_sortable_fields("stk_list")
print(f"支持排序的字段：{sortable_fields}")

# 步骤 2：检查特定字段是否支持排序
is_sortable = handler.is_field_sortable("stk_list", "SEC_CODE")
print(f"SEC_CODE 是否支持排序：{is_sortable}")

# 步骤 3：执行排序查询
result = handler.execute(
    apiName="stk_list",
    sort="SEC_CODE,ASC",  # 字段名,排序方向（ASC/DESC）
    pageSize=10
)
```

### 示例 6: 查询时间范围可用字段

```python
# 获取接口可能用于时间范围查询的字段
time_fields = handler.get_time_range_fields("stk_list")
print(f"可能用于时间范围查询的字段：{time_fields}")
```

## 重要提示

### 时间范围查询规则

1. **参数格式**：`SD_字段名`（开始日期）和 `ED_字段名`（结束日期）
2. **日期格式**：YYYY-MM-DD
3. **字段选择**：使用 `get_time_range_fields()` 获取可用字段
4. **辅助方法**：使用 `build_time_range_params()` 快速构建参数

### 排序查询规则

1. **字段检测**：通过 `get_sortable_fields()` 获取支持排序的字段
2. **排序格式**：`字段名,方向`，方向为 `ASC`（升序）或 `DESC`（降序）
3. **验证**：使用 `is_field_sortable()` 验证字段是否支持排序
4. **字段描述**：支持排序的字段在描述中包含"支持排序"字样

## 错误处理

### 错误响应格式

```json
{
    "success": false,
    "message": "错误描述",
    "data": null
}
```

### 常见错误

| 错误 | 说明 |
|-----|------|
| Token 未配置 | 请在配置中设置 apiToken |
| 接口不存在 | 请检查 apiName 是否正确 |
| 参数错误 | 请检查 params 参数 |

## 部署说明

### 部署到 Lobster 平台

1. **打包 Skill**
   ```bash
   python create_package.py
   ```
   生成 `genius-financial-query-skill.zip`

2. **上传到平台**
   - 登录 接入 平台
   - 进入 Skill 管理页面
   - 上传 ZIP 文件

3. **配置 Token**
   - 在 Skill 配置页面设置 `apiToken`

4. **测试技能**
   - 调用 `execute()` 方法测试

### 本地测试

```python
from scripts.handler import create_handler

config = {
    'apiToken': 'your-token'
}
handler = create_handler(config)

# 获取接口列表
print(handler.get_interfaces())

# 测试查询
result = handler.execute("stk_list", pageSize=5)
print(result)
```

## 技术栈

- **Python**: 3.8+
- **依赖库**:
  - `requests`: HTTP 请求
  - `json`: 数据解析
  - `logging`: 日志记录

## 更新日志

### v3.1.0 (2026-04-10)
- ✅ 添加排序字段检测功能（`get_sortable_fields()`、`is_field_sortable()`）
- ✅ 添加时间范围查询支持（`SD_` 和 `ED_` 前缀）
- ✅ 添加 `get_time_range_fields()` 获取时间范围可用字段
- ✅ 添加 `build_time_range_params()` 快速构建时间范围参数
- ✅ 完整的使用示例和重要提示

### v3.0.0 (2026-04-10)
- ✅ 简化核心逻辑，只保留三件事：找接口、调用 API、字段映射
- ✅ 代码从 800+ 行缩减到 250 行
- ✅ 提供清晰的 execute() 主入口
- ✅ 自动字段名映射为中文
- ✅ 提供 get_interfaces() 和 get_interface() 辅助方法

### v2.0.0 (2026-04-09)
- 支持 100+个金融数据接口
- 完整的字段映射
- Token 验证功能

## 联系方式

- **作者**: Genius Skill Team
- **官网**: http://science.z3cloud.com.cn/api-genius

