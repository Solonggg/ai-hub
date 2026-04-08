#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI/UX Pro Max Search - 面向 UI/UX 指南数据集的检索工具
Usage: python search.py "<query>" [--domain <domain>] [--stack <stack>] [--max-results 3]
       python search.py "<query>" --design-system [-p "Project Name"]
       python search.py "<query>" --design-system --persist [-p "Project Name"] [--page "dashboard"]

Domains: style, prompt, color, chart, landing, product, ux, typography
Stacks: html-tailwind, react, nextjs

Persistence (Master + Overrides pattern):
  --persist    Save design system to design-system/MASTER.md
  --page       Also create a page-specific override file in design-system/pages/
"""

import argparse
import sys
import io
from core import CSV_CONFIG, AVAILABLE_STACKS, MAX_RESULTS, search, search_stack
from design_system import generate_design_system, persist_design_system

# Force UTF-8 for stdout/stderr to handle emojis on Windows (cp1252 default)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def format_output(result):
    """Format results for terminal reading."""
    if "error" in result:
        return f"错误：{result['error']}"

    output = []
    if result.get("stack"):
        output.append("## UI/UX 栈规范检索结果")
        output.append(f"**技术栈：** {result['stack']} | **原始查询：** {result['query']}")
    else:
        output.append("## UI/UX 检索结果")
        output.append(f"**领域：** {result['domain']} | **原始查询：** {result['query']}")
    if result.get("normalized_query") and result["normalized_query"] != result["query"]:
        output.append(f"**归一化查询：** {result['normalized_query']}")
    output.append(f"**数据源：** {result['file']} | **命中：** {result['count']} 条\n")

    for i, row in enumerate(result['results'], 1):
        output.append(f"### 结果 {i}")
        for key, value in row.items():
            value_str = str(value)
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            output.append(f"- **{key}:** {value_str}")
        output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UI/UX 检索工具")
    parser.add_argument("query", help="检索词，支持中文")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="检索领域")
    parser.add_argument("--stack", "-s", choices=AVAILABLE_STACKS, help="按技术栈检索规范")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="最大返回条数，默认 3")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    # Design system generation
    parser.add_argument("--design-system", "-ds", action="store_true", help="生成完整设计系统建议")
    parser.add_argument("--project-name", "-p", type=str, default=None, help="设计系统输出中的项目名")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="设计系统输出格式")
    # Persistence (Master + Overrides pattern)
    parser.add_argument("--persist", action="store_true", help="将设计系统保存到 design-system/ 目录")
    parser.add_argument("--page", type=str, default=None, help="同时创建页面级覆盖文件")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="持久化输出目录，默认当前目录")

    args = parser.parse_args()

    # Design system takes priority
    if args.design_system:
        result = generate_design_system(
            args.query, 
            args.project_name, 
            args.format,
            persist=args.persist,
            page=args.page,
            output_dir=args.output_dir
        )
        print(result)
        
        # Print persistence confirmation
        if args.persist:
            project_slug = args.project_name.lower().replace(' ', '-') if args.project_name else "default"
            print("\n" + "=" * 60)
            print(f"✅ 设计系统已落盘到 design-system/{project_slug}/")
            print(f"   📄 design-system/{project_slug}/MASTER.md（全局主规则）")
            if args.page:
                page_filename = args.page.lower().replace(' ', '-')
                print(f"   📄 design-system/{project_slug}/pages/{page_filename}.md（页面覆盖规则）")
            print("")
            print(f"📖 使用方式：开发页面时优先检查 design-system/{project_slug}/pages/[page].md。")
            print("   页面文件存在时以页面规则覆盖 MASTER.md；否则直接遵循 MASTER.md。")
            print("=" * 60)
    # Stack search
    elif args.stack:
        result = search_stack(args.query, args.stack, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
    # Domain search
    else:
        result = search(args.query, args.domain, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
