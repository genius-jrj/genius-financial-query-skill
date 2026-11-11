#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
巨灵财经数据查询 —— 核心处理模块

能力：
- 找接口：search_interfaces / get_interface / get_input_params / get_sortable_fields
- 找字段：search_fields
- 调 API：execute
- 字段本地化：输出中文列名，重名字段自动追加字段代码，保证不丢列

设计约定：
- 仅调用 execute() 时才需要 API Token 与网络；其余元数据能力完全离线。
- requests 延迟导入，未安装时只有取数会失败，本地检索仍可用。
- 不在 import 期修改宿主的 logging 配置。
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = 'https://science.z3cloud.com.cn/gapi/data/base'

# 单次返回超过该单元格数时，在 metadata 中提示调用方谨慎处理
LARGE_RESULT_CELLS = 20000


class FinancialDataHandler:
    """金融数据查询处理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.api_token = config.get('apiToken') or os.environ.get('GENIUS_API_TOKEN', '')
        self.api_base_url = config.get('apiBaseUrl') or DEFAULT_BASE_URL
        self.timeout = int(config.get('timeout', 30))
        self._field_mapping: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # 元数据加载
    # ------------------------------------------------------------------
    @property
    def field_mapping(self) -> Dict[str, Any]:
        """懒加载字段映射表（约 1.3MB，只在真正用到时读取）"""
        if self._field_mapping is None:
            self._field_mapping = self._load_field_mapping()
        return self._field_mapping

    def _mapping_path(self) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(current_dir, '..', 'references', 'field_mapping.json'))

    def _load_field_mapping(self) -> Dict[str, Any]:
        path = self._mapping_path()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning('字段映射文件不存在：%s', path)
            return {'interfaces': {}, 'categoryHierarchy': {}}
        except (OSError, ValueError) as e:
            logger.warning('字段映射文件解析失败：%s', e)
            return {'interfaces': {}, 'categoryHierarchy': {}}

    def _iter_interfaces(self):
        """遍历 (分类代码, 分类信息, 接口代码, 接口信息)"""
        for cat_code, cat in self.field_mapping.get('interfaces', {}).items():
            for code, iface in cat.get('interfaces', {}).items():
                yield cat_code, cat, code, iface

    def _category_tree(self) -> Dict[str, Dict[str, Any]]:
        """分类树；优先读取 categoryHierarchy，缺失时回退到各分类的 parentCategory"""
        tree = self.field_mapping.get('categoryHierarchy') or {}
        if tree:
            return tree
        tree = {}
        for cat_code, cat in self.field_mapping.get('interfaces', {}).items():
            tree[cat_code] = {'name': cat.get('categoryName', cat_code),
                              'parent': cat.get('parentCategory')}
        return tree

    # ------------------------------------------------------------------
    # 分类
    # ------------------------------------------------------------------
    def get_category_name(self, categoryCode: str) -> str:
        node = self._category_tree().get(categoryCode)
        if node:
            return node.get('name', categoryCode)
        cat = self.field_mapping.get('interfaces', {}).get(categoryCode)
        return cat.get('categoryName', categoryCode) if cat else categoryCode

    def get_category_parent(self, categoryCode: str) -> Optional[str]:
        node = self._category_tree().get(categoryCode)
        return node.get('parent') if node else None

    def get_category_hierarchy(self, categoryCode: str) -> List[str]:
        """从一级分类到当前分类的代码路径，如 ['gpsj', 'cwsj']"""
        path: List[str] = []
        current: Optional[str] = categoryCode
        seen = set()
        while current and current not in seen:
            seen.add(current)
            path.insert(0, current)
            current = self.get_category_parent(current)
        return path

    def get_category_full_path(self, categoryCode: str) -> str:
        """完整中文路径，如 '股票数据 > 财务数据'"""
        path = self.get_category_hierarchy(categoryCode)
        return ' > '.join(self.get_category_name(code) for code in path)

    def _count_interfaces_under(self, code: str, node: Optional[Dict[str, Any]] = None) -> int:
        """统计节点自身及子孙节点挂载的接口总数"""
        tree = self._category_tree()
        total = len(self.field_mapping.get('interfaces', {}).get(code, {}).get('interfaces', {}))
        for child, child_node in tree.items():
            if child_node.get('parent') == code:
                total += self._count_interfaces_under(child, child_node)
        return total

    def get_categories_by_parent(self, parentCode: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取指定父分类下的直接子分类；parentCode 为 None 时返回全部一级分类"""
        result = []
        for code, node in self._category_tree().items():
            if node.get('parent') == parentCode:
                result.append({
                    'code': code,
                    'name': node.get('name', code),
                    'level': node.get('level'),
                    'interfaceCount': self._count_interfaces_under(code, node),
                })
        return result

    def get_category_tree(self) -> Dict[str, Any]:
        """返回完整分类树（一级分类下嵌子分类）"""
        tree = self._category_tree()

        def build(parent=None):
            nodes = []
            for code, node in tree.items():
                if node.get('parent') == parent:
                    nodes.append({
                        'code': code,
                        'name': node.get('name', code),
                        'interfaceCount': self._count_interfaces_under(code, node),
                        'children': build(code),
                    })
            return nodes

        return {'categories': build()}

    # ------------------------------------------------------------------
    # 接口检索
    # ------------------------------------------------------------------
    def get_interfaces(self, brief: bool = True,
                       categoryCode: Optional[str] = None,
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取接口清单

        Args:
            brief: True（默认）只返回分类路径/接口代码/名称/数量，约 15KB，用于粗筛；
                   接口说明请用 search_interfaces(keyword) 或 get_interface(code) 获取。
                   False 返回含全部输入参数与全部输出字段的完整信息（约 700KB），
                   仅在确实需要一次性浏览全量参数时使用。
            categoryCode: 只返回该分类（含其子分类）下的接口
            limit: 最多返回条数
        """
        subtree = None
        if categoryCode:
            subtree = {categoryCode} | {
                code for code, node in self._category_tree().items()
                if categoryCode in self.get_category_hierarchy(code)
            }

        result = []
        for cat_code, cat, code, iface in self._iter_interfaces():
            if subtree is not None and cat_code not in subtree:
                continue
            item = {
                'categoryPath': self.get_category_full_path(cat_code),
                'categoryCode': cat_code,
                'interfaceCode': code,
                'interfaceName': iface.get('name', ''),
                'inputParamCount': len(iface.get('inputParams', [])),
                'fieldCount': len(iface.get('fields', [])),
            }
            if not brief:
                item['description'] = iface.get('description', '')
                item['inputParams'] = iface.get('inputParams', [])
                item['fields'] = iface.get('fields', [])
            result.append(item)
            if limit and len(result) >= limit:
                break
        return result

    def get_interface(self, interfaceCode: str) -> Optional[Dict[str, Any]]:
        """获取单个接口的完整信息（约 15KB，推荐用于确认参数与字段）"""
        for cat_code, cat, code, iface in self._iter_interfaces():
            if code == interfaceCode:
                return {
                    'category': cat.get('categoryName', ''),
                    'categoryPath': self.get_category_full_path(cat_code),
                    'categoryCode': cat_code,
                    'interfaceCode': code,
                    'interfaceName': iface.get('name', ''),
                    'description': iface.get('description', ''),
                    'inputParamCount': len(iface.get('inputParams', [])),
                    'fieldCount': len(iface.get('fields', [])),
                    'inputParams': iface.get('inputParams', []),
                    'fields': iface.get('fields', []),
                }
        return None

    def search_interfaces(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        按关键词检索接口（匹配接口代码 / 名称 / 描述），用于「业务词 -> 接口」定位

        Args:
            keyword: 关键词，如「日线」「资产负债表」「净值」
            limit: 最多返回条数
        """
        kw = (keyword or '').lower()
        if not kw:
            return []
        hits = []
        for cat_code, _cat, code, iface in self._iter_interfaces():
            haystack = ' '.join([
                code.lower(),
                (iface.get('name') or '').lower(),
                (iface.get('description') or '').lower(),
            ])
            if kw in haystack:
                hits.append({
                    'categoryPath': self.get_category_full_path(cat_code),
                    'interfaceCode': code,
                    'interfaceName': iface.get('name', ''),
                    'description': (iface.get('description') or '')[:120],
                    'fieldCount': len(iface.get('fields', [])),
                })
                if len(hits) >= limit:
                    break
        return hits

    def search_fields(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        跨接口检索字段（匹配字段代码 / 中文名），用于定位「资产总计」这类业务指标

        Returns:
            命中列表，每项含 interfaceCode / fieldCode / fieldName
        """
        kw = (keyword or '').lower()
        if not kw:
            return []
        hits = []
        for _cat_code, _cat, code, iface in self._iter_interfaces():
            for field in iface.get('fields', []):
                haystack = f"{field.get('code', '').lower()} {field.get('name', '').lower()}"
                if kw in haystack:
                    hits.append({
                        'interfaceCode': code,
                        'interfaceName': iface.get('name', ''),
                        'fieldCode': field.get('code'),
                        'fieldName': field.get('name'),
                        'type': field.get('type'),
                        'description': field.get('description', ''),
                    })
                    if len(hits) >= limit:
                        return hits
        return hits

    def get_input_params(self, interfaceCode: str) -> List[Dict[str, Any]]:
        interface = self.get_interface(interfaceCode)
        return interface.get('inputParams', []) if interface else []

    def get_required_input_params(self, interfaceCode: str) -> List[Dict[str, Any]]:
        return [p for p in self.get_input_params(interfaceCode) if p.get('required') == '是']

    def get_output_fields(self, interfaceCode: str) -> List[Dict[str, Any]]:
        interface = self.get_interface(interfaceCode)
        return interface.get('fields', []) if interface else []

    def get_sortable_fields(self, interfaceCode: str) -> List[str]:
        """支持排序的字段代码（优先用数据中的显式 sortable 标记）"""
        sortable = []
        for field in self.get_output_fields(interfaceCode):
            flag = field.get('sortable')
            if flag is None:
                flag = '支持排序' in (field.get('description') or '')
            if flag:
                sortable.append(field['code'])
        return sortable

    def is_field_sortable(self, interfaceCode: str, fieldCode: str) -> bool:
        return fieldCode in self.get_sortable_fields(interfaceCode)

    def get_time_range_fields(self, interfaceCode: str) -> List[str]:
        """可能支持 SD_/ED_ 范围查询的时间类字段"""
        keywords = ('date', 'time', 'day', 'rpt', 'trade')
        return [f['code'] for f in self.get_output_fields(interfaceCode)
                if any(k in f['code'].lower() for k in keywords)]

    def build_time_range_params(self, fieldCode: str, startDate: Optional[str] = None,
                                endDate: Optional[str] = None) -> Dict[str, str]:
        """构造 SD_字段 / ED_字段 范围参数"""
        params = {}
        if startDate:
            params[f'SD_{fieldCode}'] = startDate
        if endDate:
            params[f'ED_{fieldCode}'] = endDate
        return params

    # ------------------------------------------------------------------
    # 取数
    # ------------------------------------------------------------------
    def execute(self, apiName: str, params: Optional[Dict] = None,
                fields: Optional[str] = None,
                sort: Optional[str] = None,
                mode: int = 1,
                pageNum: int = 1,
                pageSize: int = 1000) -> Dict[str, Any]:
        """
        执行 API 查询

        Returns:
            {success, message, data:{...}, metadata:{...}}
            data 内列名已本地化为中文；重名字段形如 "经营活动产生的现金流量净额(C410000)"
        """
        if not self.api_token:
            return {
                'success': False,
                'message': '未配置 API Token。请设置环境变量 GENIUS_API_TOKEN，'
                           '或在 create_handler({"apiToken": "..."}) 中传入。',
                'data': None,
            }

        if not apiName:
            return {'success': False, 'message': 'apiName 不能为空', 'data': None}

        request_body: Dict[str, Any] = {
            'apiName': apiName,
            'mode': mode,
            'pageNum': pageNum,
            'pageSize': pageSize,
        }
        if params:
            request_body['params'] = params
        if fields:
            request_body['fields'] = fields
        if sort:
            request_body['sort'] = sort

        try:
            response_data = self._send_request(request_body)
        except Exception as e:  # 网络/解析异常统一收口，避免抛给调用方
            logger.warning('调用 %s 失败：%s', apiName, e)
            return {'success': False, 'message': f'请求失败：{e}', 'data': None}

        if response_data.get('code') != 200:
            return {
                'success': False,
                'message': response_data.get('msg') or '接口调用失败',
                'data': None,
                'metadata': {'apiName': apiName, 'code': response_data.get('code')},
            }

        raw = response_data.get('data') or {}
        mapped = self._map_fields(raw, apiName)
        metadata: Dict[str, Any] = {
            'apiName': apiName,
            'mode': mode,
            'total': raw.get('total', 0),
            'hasMore': raw.get('hasMore', False),
        }
        cells = mapped.get('size', 0) * len(mapped.get('columns', []))
        if cells > LARGE_RESULT_CELLS:
            metadata['largeResult'] = (
                f'本次返回约 {cells} 个单元格，建议缩小 fields 或加筛选条件后再取数'
            )
        return {'success': True, 'message': '查询成功', 'data': mapped, 'metadata': metadata}

    def get_latest_report(self, apiName: str, secCode: str,
                          fields: Optional[str] = None,
                          rptType: str = '合并',
                          codeParam: str = 'SEC_CODE') -> Dict[str, Any]:
        """
        取最新一期财报（自动跳过上期末比较列）

        财务报表类接口（stk_bal_sheet / stk_inc / stk_cash_flow / reits_bal 等）
        同一 RPT_DATE 下会返回 2 行：本期数（ENDDATE == RPT_DATE）与上期末比较列
        （ENDDATE 为上一年末）。直接按 RPT_DATE 倒序取第一条会拿到比较列，属于静默错误。
        本方法按 RPT_DATE 分组，只取 ENDDATE == RPT_DATE 的本期行。

        Args:
            apiName: 接口代码，如 stk_bal_sheet
            secCode: 证券/基金代码
            fields: 需要的字段（逗号分隔），会自动补上 ENDDATE 与 RPT_DATE 用于判期
            rptType: 报表类型，'合并' 或 '母公司'；传空字符串则不过滤
            codeParam: 代码参数名，A股用 SEC_CODE，基金/REITs 用 FUND_CODE
        """
        requested = [f.strip() for f in (fields or '').split(',') if f.strip()]
        ensure = [c for c in ('RPT_DATE', 'ENDDATE') if c not in requested]
        query_fields = ','.join(requested + ensure) if requested else None

        params: Dict[str, Any] = {codeParam: secCode}
        if rptType:
            params['RPT_TYPE'] = rptType

        result = self.execute(apiName, params=params, fields=query_fields,
                              sort='RPT_DATE,DESC', mode=2, pageNum=1, pageSize=40)
        if not result.get('success'):
            return result

        rows = result['data'].get('kvData') or []
        if not rows:
            return {'success': False, 'message': f'{apiName} 未返回数据', 'data': None}

        labels = {c['code']: c['label'] for c in result['data'].get('columns', [])}
        end_label = labels.get('ENDDATE', '截止日期')
        rpt_label = labels.get('RPT_DATE', '报表日期')

        for row in rows:
            end_value = str(row.get(end_label))
            rpt_value = str(row.get(rpt_label))
            if end_value == rpt_value:
                return {
                    'success': True,
                    'message': f'已取到最新一期（报告期 {rpt_value}）',
                    'data': row,
                    'metadata': {
                        'apiName': apiName,
                        'rptDate': rpt_value,
                        'rptType': rptType,
                        'currentRowIndex': rows.index(row),
                        'skippedComparativeRows': sum(
                            1 for r in rows
                            if str(r.get(rpt_label)) == rpt_value
                            and str(r.get(end_label)) != rpt_value
                        ),
                    },
                }

        return {
            'success': False,
            'message': '未能定位本期行（ENDDATE 与 RPT_DATE 全部不一致），请改用 ENDDATE 参数显式指定报告期',
            'data': None,
            'metadata': {'apiName': apiName, 'rowCount': len(rows)},
        }

    def _send_request(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """发送 HTTP 请求（requests 延迟导入）"""
        try:
            import requests  # noqa: WPS433  延迟导入：本地检索不依赖它
        except ImportError as e:
            raise RuntimeError(
                '缺少依赖 requests，请先执行：pip install -r requirements.txt'
            ) from e

        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        }
        response = requests.post(self.api_base_url, headers=headers, json=body,
                                 timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # 字段本地化
    # ------------------------------------------------------------------
    def _get_field_meta(self, apiName: str) -> Dict[str, Dict[str, str]]:
        """字段代码 -> {code, name, label}"""
        meta: Dict[str, Dict[str, str]] = {}
        for _cat_code, _cat, code, iface in self._iter_interfaces():
            if code != apiName:
                continue
            used = set()
            for field in iface.get('fields', []):
                field_code = field.get('code')
                name = field.get('name') or field_code
                label = field.get('label')
                if not label:
                    label = name if name not in used else f'{name}({field_code})'
                used.add(label)
                meta[field_code] = {'code': field_code, 'name': name, 'label': label}
            break
        return meta

    def _map_fields(self, data: Dict[str, Any], apiName: str) -> Dict[str, Any]:
        """
        把原始响应转成中文列名结果

        - 重名字段用 "中文名(字段代码)" 保证唯一，不会互相覆盖
        - columns 保留字段代码，便于二次筛选与排序
        """
        field_meta = self._get_field_meta(apiName)

        def label_of(code: str) -> str:
            return field_meta.get(code, {}).get('label', code)

        pagination = {
            'total': data.get('total', 0),
            'current': data.get('current', 1),
            'pages': data.get('pages', 0),
            'size': data.get('size', 0),
            'hasMore': data.get('hasMore', False),
        }

        kv_data = data.get('kvData')
        if kv_data is not None:
            columns = [{'code': k, 'label': label_of(k)} for k in kv_data[0].keys()] if kv_data else []
            rows = [{label_of(k): v for k, v in row.items()} for row in kv_data]
            result = {'kvData': rows, 'columns': columns}
            result.update(pagination)
            return result

        codes = data.get('fields') or []
        items = data.get('items') or []
        columns = [{'code': c, 'label': label_of(c)} for c in codes]
        rows = []
        for item in items:
            rows.append({label_of(c): (item[i] if i < len(item) else None)
                         for i, c in enumerate(codes)})
        result = {'fields': [c['label'] for c in columns], 'items': rows, 'columns': columns}
        result.update(pagination)
        return result


def create_handler(config: Optional[Dict[str, Any]] = None) -> FinancialDataHandler:
    """创建处理器实例"""
    return FinancialDataHandler(config)
