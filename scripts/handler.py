#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融数据查询核心处理模块（简化版）
- 找接口
- 调用 HTTP API
- 字段映射返回数据
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialDataHandler:
    """金融数据查询处理器（简化版）"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化处理器
        
        Args:
            config: 配置字典，包含 apiToken 等配置项
        """
        self.api_token = config.get('apiToken', '')
        self.api_base_url = 'http://science.z3cloud.com.cn/gapi/data/base'
        self.default_page_size = 1000
        self.default_page_num = 1
        self.timeout = 30
        
        if not self.api_token:
            logger.warning("API Token 未配置")
        
        self.field_mapping = self._load_field_mapping()
    
    def _load_field_mapping(self) -> Dict[str, Any]:
        """加载字段映射文件"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mapping_file = os.path.join(current_dir, '..', 'references', 'field_mapping.json')
            mapping_file = os.path.normpath(mapping_file)
            
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"字段映射文件不存在：{mapping_file}")
                return {}
        except Exception as e:
            logger.error(f"加载字段映射文件失败：{e}")
            return {}
    
    def execute(self, apiName: str, params: Optional[Dict] = None, 
                fields: Optional[str] = None, 
                sort: Optional[str] = None,
                pageNum: int = 1, 
                pageSize: int = 1000) -> Dict[str, Any]:
        """
        执行 API 查询（主入口）
        
        Args:
            apiName: 接口名称（如 stk_list）
            params: 查询参数（如 {"SEC_CODE": "600519"}）
            fields: 返回字段（如 "SEC_CODE,SEC_SNAME"）
            sort: 排序（如 "LIST_DATE,DESC"）
            mode: 返回模式, 1-数组格式返回，2-键值对格式返回，默认1
            pageNum: 页码
            pageSize: 每页条数
            
        Returns:
            包含查询结果的字典
        """
        try:
            if not self.api_token:
                return {
                    'success': False,
                    'message': '请配置 API Token',
                    'data': None
                }
            
            request_body = {
                'apiName': apiName,
                'mode': 1,
                'pageNum': pageNum,
                'pageSize': pageSize
            }
            
            if params:
                request_body['params'] = params
            
            if fields:
                request_body['fields'] = fields
            
            if sort:
                request_body['sort'] = sort
            
            response_data = self._send_request(request_body)
            
            if response_data.get('code') != 200:
                return {
                    'success': False,
                    'message': response_data.get('msg', '接口调用失败'),
                    'data': None
                }
            
            mapped_data = self._map_fields(response_data.get('data', {}), apiName)
            
            return {
                'success': True,
                'message': '查询成功',
                'data': mapped_data,
                'metadata': {
                    'apiName': apiName,
                    'total': response_data.get('data', {}).get('total', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"执行查询时发生错误：{e}")
            return {
                'success': False,
                'message': f'查询失败：{str(e)}',
                'data': None
            }
    
    def _send_request(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"发送请求：{body}")
        
        response = requests.post(
            self.api_base_url,
            headers=headers,
            json=body,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"接收响应：code={result.get('code')}")
        
        return result
    
    def _map_fields(self, data: Dict[str, Any], apiName: str) -> Dict[str, Any]:
        """
        字段映射：将 API 返回的字段映射为中文
        
        Args:
            data: API 返回的原始数据
            apiName: 接口名称
            
        Returns:
            映射后的数据
        """
        fields = data.get('fields', [])
        items = data.get('items', [])
        
        field_name_map = self._get_field_name_map(apiName)
        
        mapped_fields = [field_name_map.get(f, f) for f in fields]
        
        mapped_items = []
        for item in items:
            mapped_item = {}
            for i, field in enumerate(fields):
                field_name = field_name_map.get(field, field)
                mapped_item[field_name] = item[i] if i < len(item) else None
            mapped_items.append(mapped_item)
        
        return {
            'fields': mapped_fields,
            'items': mapped_items,
            'total': data.get('total', 0),
            'current': data.get('current', 1),
            'pages': data.get('pages', 0),
            'size': data.get('size', 0)
        }
    
    def _get_field_name_map(self, apiName: str) -> Dict[str, str]:
        """获取接口的字段名映射"""
        field_map = {}
        interfaces = self.field_mapping.get('interfaces', {})
        
        for category_code, category_data in interfaces.items():
            category_interfaces = category_data.get('interfaces', {})
            if apiName in category_interfaces:
                fields = category_interfaces[apiName].get('fields', [])
                for field in fields:
                    field_map[field['code']] = field['name']
                break
        
        return field_map
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取所有接口列表"""
        result = []
        interfaces = self.field_mapping.get('interfaces', {})
        
        for category_code, category_data in interfaces.items():
            category_name = category_data.get('categoryName', '')
            category_interfaces = category_data.get('interfaces', {})
            
            for interface_code, interface_data in category_interfaces.items():
                result.append({
                    'category': category_name,
                    'categoryCode': category_code,
                    'interfaceCode': interface_code,
                    'interfaceName': interface_data.get('name', ''),
                    'description': interface_data.get('description', ''),
                    'inputParamCount': len(interface_data.get('inputParams', [])),
                    'fieldCount': len(interface_data.get('fields', [])),
                    'inputParams': interface_data.get('inputParams', []),
                    'fields': interface_data.get('fields', [])
                })
        
        return result
    
    def get_interface(self, interfaceCode: str) -> Optional[Dict[str, Any]]:
        """获取单个接口的详细信息"""
        interfaces = self.field_mapping.get('interfaces', {})
        
        for category_code, category_data in interfaces.items():
            category_interfaces = category_data.get('interfaces', {})
            if interfaceCode in category_interfaces:
                interface_data = category_interfaces[interfaceCode]
                return {
                    'category': category_data.get('categoryName', ''),
                    'categoryCode': category_code,
                    'interfaceCode': interfaceCode,
                    'interfaceName': interface_data.get('name', ''),
                    'description': interface_data.get('description', ''),
                    'inputParamCount': len(interface_data.get('inputParams', [])),
                    'fieldCount': len(interface_data.get('fields', [])),
                    'inputParams': interface_data.get('inputParams', []),
                    'fields': interface_data.get('fields', [])
                }
        
        return None
    
    def get_category_name(self, categoryCode: str) -> str:
        """
        获取分类的中文名称
        
        Args:
            categoryCode: 分类编码（如 jcsj）
            
        Returns:
            分类中文名称
        """
        interfaces = self.field_mapping.get('interfaces', {})
        if categoryCode in interfaces:
            return interfaces[categoryCode].get('categoryName', categoryCode)
        
        return categoryCode
    
    def get_category_parent(self, categoryCode: str) -> Optional[str]:
        """
        获取分类的父分类编码
        
        Args:
            categoryCode: 分类编码（如 jcsj）
            
        Returns:
            父分类编码，如果是一级分类则返回 None
        """
        interfaces = self.field_mapping.get('interfaces', {})
        if categoryCode in interfaces:
            return interfaces[categoryCode].get('parentCategory')
        
        return None
    
    def get_category_hierarchy(self, categoryCode: str) -> List[str]:
        """
        获取分类的完整层级路径
        
        Args:
            categoryCode: 分类编码（如 jcsj）
            
        Returns:
            从一级分类到当前分类的路径列表，如 ['gpsj', 'jcsj']
        """
        path = []
        current = categoryCode
        
        while current:
            path.insert(0, current)
            current = self.get_category_parent(current)
        
        return path
    
    def get_category_full_path(self, categoryCode: str) -> str:
        """
        获取分类的完整中文路径
        
        Args:
            categoryCode: 分类编码（如 jcsj）
            
        Returns:
            完整中文路径，如 "股票数据 > 基础数据"
        """
        hierarchy = self.get_category_hierarchy(categoryCode)
        names = [self.get_category_name(code) for code in hierarchy]
        return ' > '.join(names)
    
    def get_categories_by_parent(self, parentCode: Optional[str] = None) -> List[Dict[str, str]]:
        """
        获取指定父分类下的所有子分类
        
        Args:
            parentCode: 父分类编码，如果为 None 则获取所有一级分类
            
        Returns:
            子分类列表，包含 code 和 name
        """
        result = []
        interfaces = self.field_mapping.get('interfaces', {})
        
        for code, data in interfaces.items():
            if data.get('parentCategory') == parentCode:
                result.append({
                    'code': code,
                    'name': data.get('categoryName', code)
                })
        
        return result
    
    def get_input_params(self, interfaceCode: str) -> List[Dict[str, Any]]:
        """
        获取接口的输入参数列表
        
        Args:
            interfaceCode: 接口代码
            
        Returns:
            输入参数列表
        """
        interface = self.get_interface(interfaceCode)
        if interface:
            return interface.get('inputParams', [])
        return []
    
    def get_required_input_params(self, interfaceCode: str) -> List[Dict[str, Any]]:
        """
        获取接口的必填输入参数
        
        Args:
            interfaceCode: 接口代码
            
        Returns:
            必填输入参数列表
        """
        input_params = self.get_input_params(interfaceCode)
        return [param for param in input_params if param.get('required') == '是']
    
    def get_sortable_fields(self, interfaceCode: str) -> List[str]:
        """
        获取接口支持排序的字段列表
        
        Args:
            interfaceCode: 接口代码
            
        Returns:
            支持排序的字段代码列表
        """
        sortable_fields = []
        interface = self.get_interface(interfaceCode)
        
        if interface:
            for field in interface.get('fields', []):
                desc = field.get('description', '')
                if '支持排序' in desc:
                    sortable_fields.append(field['code'])
        
        return sortable_fields
    
    def is_field_sortable(self, interfaceCode: str, fieldCode: str) -> bool:
        """
        检查字段是否支持排序
        
        Args:
            interfaceCode: 接口代码
            fieldCode: 字段代码
            
        Returns:
            是否支持排序
        """
        return fieldCode in self.get_sortable_fields(interfaceCode)
    
    def get_time_range_fields(self, interfaceCode: str) -> List[str]:
        """
        获取接口可能用于时间范围查询的字段
        
        Args:
            interfaceCode: 接口代码
            
        Returns:
            可能用于时间范围查询的字段代码列表
        """
        time_fields = []
        interface = self.get_interface(interfaceCode)
        
        if interface:
            for field in interface.get('fields', []):
                field_code = field['code']
                if any(kw in field_code.lower() for kw in ['date', 'time', 'day', 'rpt', 'trade']):
                    time_fields.append(field_code)
        
        return time_fields
    
    def build_time_range_params(self, fieldCode: str, startDate: Optional[str] = None, 
                                 endDate: Optional[str] = None) -> Dict[str, str]:
        """
        构建时间范围查询参数
        
        Args:
            fieldCode: 字段代码（如 TRADEDATE）
            startDate: 开始日期（YYYY-MM-DD）
            endDate: 结束日期（YYYY-MM-DD）
            
        Returns:
            包含 SD_fieldCode 和 ED_fieldCode 的参数字典
        """
        params = {}
        
        if startDate:
            params[f'SD_{fieldCode}'] = startDate
        
        if endDate:
            params[f'ED_{fieldCode}'] = endDate
        
        return params


def create_handler(config: Dict[str, Any]) -> FinancialDataHandler:
    """创建处理器实例"""
    return FinancialDataHandler(config)
