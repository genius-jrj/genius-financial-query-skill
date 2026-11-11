#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
巨灵财经数据查询 —— 命令行入口

所有输出均为 JSON（UTF-8），便于直接管道处理。

示例：
    # 分类树 / 分类下的接口
    python scripts/query.py --tree
    python scripts/query.py --list --category gpsj

    # 找接口 / 找字段（离线，不需要 Token）
    python scripts/query.py --search 日线
    python scripts/query.py --search-field 资产总计
    python scripts/query.py --describe stk_daily_hist

    # 取数（需要 GENIUS_API_TOKEN）
    python scripts/query.py --api stk_daily_hist \
        --params '{"SEC_CODE":"600519","SD_TRADEDATE":"2025-01-01","ED_TRADEDATE":"2025-12-31"}' \
        --fields SEC_CODE,TRADEDATE,TCLOSE --sort TRADEDATE,DESC --mode 2 --page-size 300
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handler import create_handler  # noqa: E402


def emit(payload, pretty=False):
    """以 UTF-8 输出 JSON，规避 Windows 控制台编码问题"""
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
    if hasattr(sys.stdout, 'buffer'):
        text = json.dumps(payload, ensure_ascii=False,
                          indent=2 if pretty else None)
        sys.stdout.buffer.write((text + '\n').encode('utf-8'))
        sys.stdout.buffer.flush()
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None))


def main():
    parser = argparse.ArgumentParser(
        description='巨灵财经数据查询：找接口 / 找字段 / 取数',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--list', action='store_true', help='列出接口清单（精简）')
    parser.add_argument('--tree', action='store_true', help='输出分类树')
    parser.add_argument('--category', help='配合 --list，限定分类代码（含子分类）')
    parser.add_argument('--search', metavar='关键词', help='按关键词检索接口')
    parser.add_argument('--search-field', metavar='关键词', help='跨接口检索字段')
    parser.add_argument('--describe', metavar='接口代码', help='查看接口完整定义')
    parser.add_argument('--api', metavar='接口代码', help='执行取数')
    parser.add_argument('--latest-report', metavar='接口代码',
                        help='取最新一期财报（自动跳过上期末比较列），配合 --code 使用')
    parser.add_argument('--code', help='配合 --latest-report，证券/基金代码')
    parser.add_argument('--rpt-type', default='合并',
                        help='配合 --latest-report，报表类型：合并（默认）/母公司/传空串不过滤')
    parser.add_argument('--code-param', default='SEC_CODE',
                        help='配合 --latest-report，代码参数名（A股 SEC_CODE，基金/REITs FUND_CODE）')
    parser.add_argument('--params', default=None, help='查询参数，JSON 字符串')
    parser.add_argument('--fields', default=None, help='返回字段，逗号分隔')
    parser.add_argument('--sort', default=None, help='排序，格式 字段,ASC|DESC')
    parser.add_argument('--mode', type=int, default=2, choices=[1, 2],
                        help='返回模式：1 数组，2 键值对（默认 2，更易读）')
    parser.add_argument('--page-num', type=int, default=1)
    parser.add_argument('--page-size', type=int, default=100)
    parser.add_argument('--limit', type=int, default=20, help='检索/列表返回条数上限')
    parser.add_argument('--full', action='store_true',
                        help='配合 --list，返回全量参数与字段（约 700KB，慎用）')
    parser.add_argument('--token', default=None,
                        help='API Token；缺省读取环境变量 GENIUS_API_TOKEN')
    parser.add_argument('--pretty', action='store_true', help='缩进输出')
    args = parser.parse_args()

    handler = create_handler({'apiToken': args.token} if args.token else {})

    try:
        if args.tree:
            emit(handler.get_category_tree(), args.pretty)

        elif args.search_field:
            emit({'keyword': args.search_field,
                  'hits': handler.search_fields(args.search_field, args.limit)}, args.pretty)

        elif args.search:
            emit({'keyword': args.search,
                  'hits': handler.search_interfaces(args.search, args.limit)}, args.pretty)

        elif args.describe:
            info = handler.get_interface(args.describe)
            if info is None:
                emit({'error': f'接口不存在：{args.describe}',
                      'hint': '可用 --search 关键词 或 --list 查询可用接口'}, args.pretty)
                return 1
            emit(info, args.pretty)

        elif args.list:
            emit({'interfaces': handler.get_interfaces(
                brief=not args.full, categoryCode=args.category, limit=args.limit)}, args.pretty)

        elif args.latest_report:
            if not args.code:
                emit({'error': '--latest-report 需要配合 --code 使用'}, args.pretty)
                return 1
            result = handler.get_latest_report(
                args.latest_report,
                secCode=args.code,
                fields=args.fields,
                rptType=args.rpt_type,
                codeParam=args.code_param,
            )
            emit(result, args.pretty)
            return 0 if result.get('success') else 1

        elif args.api:
            params = None
            if args.params:
                try:
                    params = json.loads(args.params)
                except ValueError as e:
                    emit({'error': f'--params 不是合法 JSON：{e}'}, args.pretty)
                    return 1
            result = handler.execute(
                apiName=args.api,
                params=params,
                fields=args.fields,
                sort=args.sort,
                mode=args.mode,
                pageNum=args.page_num,
                pageSize=args.page_size,
            )
            emit(result, args.pretty)
            return 0 if result.get('success') else 1

        else:
            parser.print_help()
            return 1

    except Exception as e:  # 兜底：CLI 不抛栈，统一 JSON 化
        emit({'error': f'{type(e).__name__}: {e}'}, args.pretty)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
