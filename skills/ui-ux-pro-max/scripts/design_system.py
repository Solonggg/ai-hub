#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Design System Generator - Aggregates search results and applies reasoning
to generate comprehensive design system recommendations.

Usage:
    from design_system import generate_design_system
    result = generate_design_system("SaaS dashboard", "My Project")
    
    # With persistence (Master + Overrides pattern)
    result = generate_design_system("SaaS dashboard", "My Project", persist=True)
    result = generate_design_system("SaaS dashboard", "My Project", persist=True, page="dashboard")
"""

import csv
import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from core import search, DATA_DIR, normalize_query


# ============ CONFIGURATION ============
REASONING_FILE = "ui-reasoning.csv"

SEARCH_CONFIG = {
    "product": {"max_results": 1},
    "style": {"max_results": 3},
    "color": {"max_results": 2},
    "landing": {"max_results": 2},
    "typography": {"max_results": 2}
}

CJK_RE = re.compile(r'[\u3400-\u9fff]')


# ============ DESIGN SYSTEM GENERATOR ============
class DesignSystemGenerator:
    """Generates design system recommendations from aggregated searches."""

    def __init__(self):
        self.reasoning_data = self._load_reasoning()

    def _load_reasoning(self) -> list:
        """Load reasoning rules from CSV."""
        filepath = DATA_DIR / REASONING_FILE
        if not filepath.exists():
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def _multi_domain_search(self, query: str, style_priority: list = None) -> dict:
        """Execute searches across multiple domains."""
        results = {}
        for domain, config in SEARCH_CONFIG.items():
            if domain == "style" and style_priority:
                # For style, also search with priority keywords
                priority_query = " ".join(style_priority[:2]) if style_priority else query
                combined_query = f"{query} {priority_query}"
                results[domain] = search(combined_query, domain, config["max_results"])
            else:
                results[domain] = search(query, domain, config["max_results"])
        return results

    def _find_reasoning_rule(self, category: str) -> dict:
        """Find matching reasoning rule for a category."""
        category_lower = category.lower()

        # Try exact match first
        for rule in self.reasoning_data:
            if rule.get("UI_Category", "").lower() == category_lower:
                return rule

        # Try partial match
        for rule in self.reasoning_data:
            ui_cat = rule.get("UI_Category", "").lower()
            if ui_cat in category_lower or category_lower in ui_cat:
                return rule

        # Try keyword match
        for rule in self.reasoning_data:
            ui_cat = rule.get("UI_Category", "").lower()
            keywords = ui_cat.replace("/", " ").replace("-", " ").split()
            if any(kw in category_lower for kw in keywords):
                return rule

        return {}

    def _apply_reasoning(self, category: str, search_results: dict) -> dict:
        """Apply reasoning rules to search results."""
        rule = self._find_reasoning_rule(category)

        if not rule:
            return {
                "pattern": "Hero + Features + CTA",
                "style_priority": ["Minimalism", "Flat Design"],
                "color_mood": "Professional",
                "typography_mood": "Clean",
                "key_effects": "Subtle hover transitions",
                "anti_patterns": "",
                "decision_rules": {},
                "severity": "MEDIUM"
            }

        # Parse decision rules JSON
        decision_rules = {}
        try:
            decision_rules = json.loads(rule.get("Decision_Rules", "{}"))
        except json.JSONDecodeError:
            pass

        return {
            "pattern": rule.get("Recommended_Pattern", ""),
            "style_priority": [s.strip() for s in rule.get("Style_Priority", "").split("+")],
            "color_mood": rule.get("Color_Mood", ""),
            "typography_mood": rule.get("Typography_Mood", ""),
            "key_effects": rule.get("Key_Effects", ""),
            "anti_patterns": rule.get("Anti_Patterns", ""),
            "decision_rules": decision_rules,
            "severity": rule.get("Severity", "MEDIUM")
        }

    def _select_best_match(self, results: list, priority_keywords: list) -> dict:
        """Select best matching result based on priority keywords."""
        if not results:
            return {}

        if not priority_keywords:
            return results[0]

        # First: try exact style name match
        for priority in priority_keywords:
            priority_lower = priority.lower().strip()
            for result in results:
                style_name = result.get("Style Category", "").lower()
                if priority_lower in style_name or style_name in priority_lower:
                    return result

        # Second: score by keyword match in all fields
        scored = []
        for result in results:
            result_str = str(result).lower()
            score = 0
            for kw in priority_keywords:
                kw_lower = kw.lower().strip()
                # Higher score for style name match
                if kw_lower in result.get("Style Category", "").lower():
                    score += 10
                # Lower score for keyword field match
                elif kw_lower in result.get("Keywords", "").lower():
                    score += 3
                # Even lower for other field matches
                elif kw_lower in result_str:
                    score += 1
            scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored and scored[0][0] > 0 else results[0]

    def _extract_results(self, search_result: dict) -> list:
        """Extract results list from search result dict."""
        return search_result.get("results", [])

    def _is_chinese_context(self, query: str, project_name: str = None) -> bool:
        return bool(CJK_RE.search(f"{query} {project_name or ''}"))

    def _localize_typography_for_chinese(self, typography: dict, query: str, category: str, style_name: str) -> dict:
        localized = dict(typography or {})
        context = normalize_query(f"{query} {category} {style_name}").lower()
        elegant_signals = ("luxury", "premium", "elegant", "wedding", "hotel", "beauty", "brand", "editorial")
        heading_font = "Noto Serif SC" if any(signal in context for signal in elegant_signals) else "Noto Sans SC"

        localized["Heading Font"] = heading_font
        localized["Body Font"] = "Noto Sans SC"
        localized["Mood/Style Keywords"] = localized.get(
            "Mood/Style Keywords",
            "中文界面优先保证字重层级、长文本可读性与移动端稳定显示"
        )
        localized["Best For"] = localized.get(
            "Best For",
            "中文产品界面、内容型页面、信息密度较高的业务页面"
        )
        localized["Google Fonts URL"] = (
            "https://fonts.google.com/?query=Noto%20Sans%20SC%20Noto%20Serif%20SC"
        )
        localized["CSS Import"] = (
            "@import url('https://fonts.googleapis.com/css2?"
            "family=Noto+Sans+SC:wght@400;500;600;700;800&"
            "family=Noto+Serif+SC:wght@500;600;700&display=swap');"
        )
        return localized

    def generate(self, query: str, project_name: str = None) -> dict:
        """Generate complete design system recommendation."""
        # Step 1: First search product to get category
        product_result = search(query, "product", 1)
        product_results = product_result.get("results", [])
        category = "General"
        if product_results:
            category = product_results[0].get("Product Type", "General")

        # Step 2: Get reasoning rules for this category
        reasoning = self._apply_reasoning(category, {})
        style_priority = reasoning.get("style_priority", [])

        # Step 3: Multi-domain search with style priority hints
        search_results = self._multi_domain_search(query, style_priority)
        search_results["product"] = product_result  # Reuse product search

        # Step 4: Select best matches from each domain using priority
        style_results = self._extract_results(search_results.get("style", {}))
        color_results = self._extract_results(search_results.get("color", {}))
        typography_results = self._extract_results(search_results.get("typography", {}))
        landing_results = self._extract_results(search_results.get("landing", {}))

        best_style = self._select_best_match(style_results, reasoning.get("style_priority", []))
        best_color = color_results[0] if color_results else {}
        best_typography = typography_results[0] if typography_results else {}
        best_landing = landing_results[0] if landing_results else {}

        if self._is_chinese_context(query, project_name):
            best_typography = self._localize_typography_for_chinese(
                best_typography, query, category, best_style.get("Style Category", "")
            )

        # Step 5: Build final recommendation
        # Combine effects from both reasoning and style search
        style_effects = best_style.get("Effects & Animation", "")
        reasoning_effects = reasoning.get("key_effects", "")
        combined_effects = style_effects if style_effects else reasoning_effects

        return {
            "project_name": project_name or query.upper(),
            "category": category,
            "pattern": {
                "name": best_landing.get("Pattern Name", reasoning.get("pattern", "Hero + Features + CTA")),
                "sections": best_landing.get("Section Order", "Hero > Features > CTA"),
                "cta_placement": best_landing.get("Primary CTA Placement", "Above fold"),
                "color_strategy": best_landing.get("Color Strategy", ""),
                "conversion": best_landing.get("Conversion Optimization", "")
            },
            "style": {
                "name": best_style.get("Style Category", "Minimalism"),
                "type": best_style.get("Type", "General"),
                "effects": style_effects,
                "keywords": best_style.get("Keywords", ""),
                "best_for": best_style.get("Best For", ""),
                "performance": best_style.get("Performance", ""),
                "accessibility": best_style.get("Accessibility", ""),
                "light_mode": best_style.get("Light Mode ✓", ""),
                "dark_mode": best_style.get("Dark Mode ✓", ""),
            },
            "colors": {
                "primary": best_color.get("Primary", "#2563EB"),
                "on_primary": best_color.get("On Primary", ""),
                "secondary": best_color.get("Secondary", "#3B82F6"),
                "accent": best_color.get("Accent", "#F97316"),
                "background": best_color.get("Background", "#F8FAFC"),
                "foreground": best_color.get("Foreground", "#1E293B"),
                "muted": best_color.get("Muted", ""),
                "border": best_color.get("Border", ""),
                "destructive": best_color.get("Destructive", ""),
                "ring": best_color.get("Ring", ""),
                "notes": best_color.get("Notes", ""),
                # Keep legacy keys for backward compat in MASTER.md
                "cta": best_color.get("Accent", "#F97316"),
                "text": best_color.get("Foreground", "#1E293B"),
            },
            "typography": {
                "heading": best_typography.get("Heading Font", "Inter"),
                "body": best_typography.get("Body Font", "Inter"),
                "mood": best_typography.get("Mood/Style Keywords", reasoning.get("typography_mood", "")),
                "best_for": best_typography.get("Best For", ""),
                "google_fonts_url": best_typography.get("Google Fonts URL", ""),
                "css_import": best_typography.get("CSS Import", "")
            },
            "key_effects": combined_effects,
            "anti_patterns": reasoning.get("anti_patterns", ""),
            "decision_rules": reasoning.get("decision_rules", {}),
            "severity": reasoning.get("severity", "MEDIUM")
        }


# ============ OUTPUT FORMATTERS ============
BOX_WIDTH = 90  # Wider box for more content
ANSI_RE = re.compile(r'\033\[[0-9;]*m')


def hex_to_ansi(hex_color: str) -> str:
    """Convert hex color to ANSI True Color swatch (██) with fallback."""
    if not hex_color or not hex_color.startswith('#'):
        return ""
    colorterm = os.environ.get('COLORTERM', '')
    if colorterm not in ('truecolor', '24bit'):
        return ""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return ""
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m██\033[0m "


def ansi_ljust(s: str, width: int) -> str:
    """Like str.ljust but accounts for ANSI and East Asian character width."""
    visible_len = 0
    plain_text = ANSI_RE.sub('', s)
    for ch in plain_text:
        visible_len += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    pad = width - visible_len
    return s + (" " * max(0, pad))


def section_header(name: str, width: int) -> str:
    """Create a Unicode section separator: ├─── NAME ───...┤"""
    label = f"─── {name} "
    fill = "─" * (width - len(label) - 1)
    return f"├{label}{fill}┤"


def format_ascii_box(design_system: dict) -> str:
    """Format design system as Unicode box with ANSI color swatches."""
    project = design_system.get("project_name", "PROJECT")
    pattern = design_system.get("pattern", {})
    style = design_system.get("style", {})
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    effects = design_system.get("key_effects", "")
    anti_patterns = design_system.get("anti_patterns", "")

    def wrap_text(text: str, prefix: str, width: int) -> list:
        """Wrap long text into multiple lines."""
        if not text:
            return []
        words = text.split()
        lines = []
        current_line = prefix
        for word in words:
            if len(current_line) + len(word) + 1 <= width - 2:
                current_line += (" " if current_line != prefix else "") + word
            else:
                if current_line != prefix:
                    lines.append(current_line)
                current_line = prefix + word
        if current_line != prefix:
            lines.append(current_line)
        return lines

    # Build sections from pattern
    sections_raw = pattern.get("sections", "")
    section_delimiter = ">" if ">" in sections_raw else ","
    sections = [s.strip() for s in sections_raw.split(section_delimiter) if s.strip()]

    # Build output lines
    lines = []
    w = BOX_WIDTH - 1

    # Header with double-line box
    lines.append("╔" + "═" * w + "╗")
    lines.append(ansi_ljust(f"║  项目：{project} | 推荐设计系统", BOX_WIDTH) + "║")
    lines.append("╚" + "═" * w + "╝")
    lines.append("┌" + "─" * w + "┐")

    # Pattern section
    lines.append(section_header("页面结构", BOX_WIDTH + 1))
    lines.append(ansi_ljust(f"│  名称：{pattern.get('name', '')}", BOX_WIDTH) + "│")
    if pattern.get('conversion'):
        lines.append(ansi_ljust(f"│     转化重点：{pattern.get('conversion', '')}", BOX_WIDTH) + "│")
    if pattern.get('cta_placement'):
        lines.append(ansi_ljust(f"│     CTA 位置：{pattern.get('cta_placement', '')}", BOX_WIDTH) + "│")
    lines.append(ansi_ljust("│     页面分区：", BOX_WIDTH) + "│")
    for i, section in enumerate(sections, 1):
        wrapped_section_lines = wrap_text(section, f"│       {i}. ", BOX_WIDTH)
        if wrapped_section_lines:
            for section_line in wrapped_section_lines:
                lines.append(ansi_ljust(section_line, BOX_WIDTH) + "│")
        else:
            lines.append(ansi_ljust(f"│       {i}. {section}", BOX_WIDTH) + "│")

    # Style section
    lines.append(section_header("视觉风格", BOX_WIDTH + 1))
    lines.append(ansi_ljust(f"│  名称：{style.get('name', '')}", BOX_WIDTH) + "│")
    light = style.get("light_mode", "")
    dark = style.get("dark_mode", "")
    if light or dark:
        lines.append(ansi_ljust(f"│     模式支持：浅色 {light}  深色 {dark}", BOX_WIDTH) + "│")
    if style.get("keywords"):
        for line in wrap_text(f"关键词：{style.get('keywords', '')}", "│     ", BOX_WIDTH):
            lines.append(ansi_ljust(line, BOX_WIDTH) + "│")
    if style.get("best_for"):
        for line in wrap_text(f"适用场景：{style.get('best_for', '')}", "│     ", BOX_WIDTH):
            lines.append(ansi_ljust(line, BOX_WIDTH) + "│")
    if style.get("performance") or style.get("accessibility"):
        perf_a11y = f"性能：{style.get('performance', '')} | 无障碍：{style.get('accessibility', '')}"
        lines.append(ansi_ljust(f"│     {perf_a11y}", BOX_WIDTH) + "│")

    # Colors section (extended palette with ANSI swatches)
    lines.append(section_header("颜色系统", BOX_WIDTH + 1))
    color_entries = [
        ("主色",         "primary",      "--color-primary"),
        ("主色文字",     "on_primary",   "--color-on-primary"),
        ("辅助色",       "secondary",    "--color-secondary"),
        ("强调/CTA",     "accent",       "--color-accent"),
        ("背景",         "background",   "--color-background"),
        ("正文",         "foreground",   "--color-foreground"),
        ("弱化色",       "muted",        "--color-muted"),
        ("边框",         "border",       "--color-border"),
        ("危险色",       "destructive",  "--color-destructive"),
        ("焦点环",       "ring",         "--color-ring"),
    ]
    for label, key, css_var in color_entries:
        hex_val = colors.get(key, "")
        if not hex_val:
            continue
        swatch = hex_to_ansi(hex_val)
        content = f"│     {swatch}{label + ':':14s} {hex_val:10s} ({css_var})"
        lines.append(ansi_ljust(content, BOX_WIDTH) + "│")
    if colors.get("notes"):
        for line in wrap_text(f"说明：{colors.get('notes', '')}", "│     ", BOX_WIDTH):
            lines.append(ansi_ljust(line, BOX_WIDTH) + "│")

    # Typography section
    lines.append(section_header("字体排版", BOX_WIDTH + 1))
    lines.append(ansi_ljust(f"│  标题：{typography.get('heading', '')} / 正文：{typography.get('body', '')}", BOX_WIDTH) + "│")
    if typography.get("mood"):
        for line in wrap_text(f"气质：{typography.get('mood', '')}", "│     ", BOX_WIDTH):
            lines.append(ansi_ljust(line, BOX_WIDTH) + "│")
    if typography.get("best_for"):
        for line in wrap_text(f"适用场景：{typography.get('best_for', '')}", "│     ", BOX_WIDTH):
            lines.append(ansi_ljust(line, BOX_WIDTH) + "│")
    if typography.get("google_fonts_url"):
        lines.append(ansi_ljust(f"│     字体链接：{typography.get('google_fonts_url', '')}", BOX_WIDTH) + "│")
    if typography.get("css_import"):
        lines.append(ansi_ljust(f"│     CSS 引入：{typography.get('css_import', '')[:64]}...", BOX_WIDTH) + "│")

    # Key Effects section
    if effects:
        lines.append(section_header("关键表现", BOX_WIDTH + 1))
        for line in wrap_text(effects, "│     ", BOX_WIDTH):
            lines.append(ansi_ljust(line, BOX_WIDTH) + "│")

    # Anti-patterns section
    if anti_patterns:
        lines.append(section_header("避免事项", BOX_WIDTH + 1))
        for line in wrap_text(anti_patterns, "│     ", BOX_WIDTH):
            lines.append(ansi_ljust(line, BOX_WIDTH) + "│")

    # Pre-Delivery Checklist section
    lines.append(section_header("交付前检查", BOX_WIDTH + 1))
    checklist_items = [
        "[ ] 不用表情充当功能图标，统一使用 SVG 图标库",
        "[ ] 所有可点击元素都有明确交互态",
        "[ ] 状态过渡保持在 150-300ms",
        "[ ] 浅色与深色模式都校验文本对比度",
        "[ ] 键盘焦点态与无障碍标签可见",
        "[ ] 尊重 prefers-reduced-motion",
        "[ ] 至少验证 375px、768px、1024px 三档布局"
    ]
    for item in checklist_items:
        lines.append(ansi_ljust(f"│     {item}", BOX_WIDTH) + "│")

    lines.append("└" + "─" * w + "┘")

    return "\n".join(lines)


def format_markdown(design_system: dict) -> str:
    """Format design system as markdown."""
    project = design_system.get("project_name", "PROJECT")
    pattern = design_system.get("pattern", {})
    style = design_system.get("style", {})
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    effects = design_system.get("key_effects", "")
    anti_patterns = design_system.get("anti_patterns", "")

    lines = []
    lines.append(f"## 设计系统：{project}")
    lines.append("")

    # Pattern section
    lines.append("### 页面结构")
    lines.append(f"- **名称：** {pattern.get('name', '')}")
    if pattern.get('conversion'):
        lines.append(f"- **转化重点：** {pattern.get('conversion', '')}")
    if pattern.get('cta_placement'):
        lines.append(f"- **CTA 位置：** {pattern.get('cta_placement', '')}")
    if pattern.get('color_strategy'):
        lines.append(f"- **颜色策略：** {pattern.get('color_strategy', '')}")
    lines.append(f"- **页面分区：** {pattern.get('sections', '')}")
    lines.append("")

    # Style section
    lines.append("### 视觉风格")
    lines.append(f"- **名称：** {style.get('name', '')}")
    light = style.get("light_mode", "")
    dark = style.get("dark_mode", "")
    if light or dark:
        lines.append(f"- **模式支持：** 浅色 {light} | 深色 {dark}")
    if style.get('keywords'):
        lines.append(f"- **关键词：** {style.get('keywords', '')}")
    if style.get('best_for'):
        lines.append(f"- **适用场景：** {style.get('best_for', '')}")
    if style.get('performance') or style.get('accessibility'):
        lines.append(f"- **性能：** {style.get('performance', '')} | **无障碍：** {style.get('accessibility', '')}")
    lines.append("")

    # Colors section (extended palette)
    lines.append("### 颜色系统")
    lines.append("| 角色 | Hex | CSS 变量 |")
    lines.append("|------|-----|----------|")
    md_color_entries = [
        ("主色",         "primary",      "--color-primary"),
        ("主色文字",     "on_primary",   "--color-on-primary"),
        ("辅助色",       "secondary",    "--color-secondary"),
        ("强调/CTA",     "accent",       "--color-accent"),
        ("背景",         "background",   "--color-background"),
        ("正文",         "foreground",   "--color-foreground"),
        ("弱化色",       "muted",        "--color-muted"),
        ("边框",         "border",       "--color-border"),
        ("危险色",       "destructive",  "--color-destructive"),
        ("焦点环",       "ring",         "--color-ring"),
    ]
    for label, key, css_var in md_color_entries:
        hex_val = colors.get(key, "")
        if hex_val:
            lines.append(f"| {label} | `{hex_val}` | `{css_var}` |")
    if colors.get("notes"):
        lines.append(f"\n*说明：{colors.get('notes', '')}*")
    lines.append("")

    # Typography section
    lines.append("### 字体排版")
    lines.append(f"- **标题字体：** {typography.get('heading', '')}")
    lines.append(f"- **正文字体：** {typography.get('body', '')}")
    if typography.get("mood"):
        lines.append(f"- **气质：** {typography.get('mood', '')}")
    if typography.get("best_for"):
        lines.append(f"- **适用场景：** {typography.get('best_for', '')}")
    if typography.get("google_fonts_url"):
        lines.append(f"- **字体链接：** {typography.get('google_fonts_url', '')}")
    if typography.get("css_import"):
        lines.append("- **CSS 引入：**")
        lines.append(f"```css")
        lines.append(f"{typography.get('css_import', '')}")
        lines.append(f"```")
    lines.append("")

    # Key Effects section
    if effects:
        lines.append("### 关键表现")
        lines.append(f"{effects}")
        lines.append("")

    # Anti-patterns section
    if anti_patterns:
        lines.append("### 避免事项")
        newline_bullet = '\n- '
        lines.append(f"- {anti_patterns.replace(' + ', newline_bullet)}")
        lines.append("")

    # Pre-Delivery Checklist section
    lines.append("### 交付前检查")
    lines.append("- [ ] 不用表情充当功能图标，统一使用 SVG 图标库")
    lines.append("- [ ] 所有可点击元素都有明确交互态")
    lines.append("- [ ] 状态过渡保持在 150-300ms")
    lines.append("- [ ] 浅色与深色模式都校验文本对比度")
    lines.append("- [ ] 键盘焦点态与无障碍标签可见")
    lines.append("- [ ] 尊重 `prefers-reduced-motion`")
    lines.append("- [ ] 至少验证 375px、768px、1024px 三档布局")
    lines.append("")

    return "\n".join(lines)


# ============ MAIN ENTRY POINT ============
def generate_design_system(query: str, project_name: str = None, output_format: str = "ascii", 
                           persist: bool = False, page: str = None, output_dir: str = None) -> str:
    """
    Main entry point for design system generation.

    Args:
        query: Search query (e.g., "SaaS dashboard", "e-commerce luxury")
        project_name: Optional project name for output header
        output_format: "ascii" (default) or "markdown"
        persist: If True, save design system to design-system/ folder
        page: Optional page name for page-specific override file
        output_dir: Optional output directory (defaults to current working directory)

    Returns:
        Formatted design system string
    """
    generator = DesignSystemGenerator()
    design_system = generator.generate(query, project_name)
    
    # Persist to files if requested
    if persist:
        persist_design_system(design_system, page, output_dir, query)

    if output_format == "markdown":
        return format_markdown(design_system)
    return format_ascii_box(design_system)


# ============ PERSISTENCE FUNCTIONS ============
def persist_design_system(design_system: dict, page: str = None, output_dir: str = None, page_query: str = None) -> dict:
    """
    Persist design system to design-system/<project>/ folder using Master + Overrides pattern.
    
    Args:
        design_system: The generated design system dictionary
        page: Optional page name for page-specific override file
        output_dir: Optional output directory (defaults to current working directory)
        page_query: Optional query string for intelligent page override generation
    
    Returns:
        dict with created file paths and status
    """
    base_dir = Path(output_dir) if output_dir else Path.cwd()
    
    # Use project name for project-specific folder
    project_name = design_system.get("project_name", "default")
    project_slug = project_name.lower().replace(' ', '-')
    
    design_system_dir = base_dir / "design-system" / project_slug
    pages_dir = design_system_dir / "pages"
    
    created_files = []
    
    # Create directories
    design_system_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    master_file = design_system_dir / "MASTER.md"
    
    # Generate and write MASTER.md
    master_content = format_master_md(design_system)
    with open(master_file, 'w', encoding='utf-8') as f:
        f.write(master_content)
    created_files.append(str(master_file))
    
    # If page is specified, create page override file with intelligent content
    if page:
        page_file = pages_dir / f"{page.lower().replace(' ', '-')}.md"
        page_content = format_page_override_md(design_system, page, page_query)
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(page_content)
        created_files.append(str(page_file))
    
    return {
        "status": "success",
        "design_system_dir": str(design_system_dir),
        "created_files": created_files
    }


def format_master_md(design_system: dict) -> str:
    """Format design system as MASTER.md with hierarchical override logic."""
    project = design_system.get("project_name", "PROJECT")
    pattern = design_system.get("pattern", {})
    style = design_system.get("style", {})
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    effects = design_system.get("key_effects", "")
    anti_patterns = design_system.get("anti_patterns", "")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = []
    
    # Logic header
    lines.append("# 设计系统主文件")
    lines.append("")
    lines.append("> **规则：** 开发具体页面时，先检查 `design-system/pages/[page-name].md`。")
    lines.append("> 如果该文件存在，以页面文件中的规则 **覆盖** 本主文件。")
    lines.append("> 如果不存在，则严格遵循本主文件。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**项目：** {project}")
    lines.append(f"**生成时间：** {timestamp}")
    lines.append(f"**产品类型：** {design_system.get('category', 'General')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Global Rules section
    lines.append("## 全局规则")
    lines.append("")

    # Color Palette
    lines.append("### 颜色系统")
    lines.append("")
    lines.append("| 角色 | Hex | CSS 变量 |")
    lines.append("|------|-----|----------|")
    master_color_entries = [
        ("主色",         "primary",      "--color-primary"),
        ("主色文字",     "on_primary",   "--color-on-primary"),
        ("辅助色",       "secondary",    "--color-secondary"),
        ("强调/CTA",     "accent",       "--color-accent"),
        ("背景",         "background",   "--color-background"),
        ("正文",         "foreground",   "--color-foreground"),
        ("弱化色",       "muted",        "--color-muted"),
        ("边框",         "border",       "--color-border"),
        ("危险色",       "destructive",  "--color-destructive"),
        ("焦点环",       "ring",         "--color-ring"),
    ]
    for label, key, css_var in master_color_entries:
        hex_val = colors.get(key, "")
        if hex_val:
            lines.append(f"| {label} | `{hex_val}` | `{css_var}` |")
    lines.append("")
    if colors.get("notes"):
        lines.append(f"**颜色说明：** {colors.get('notes', '')}")
        lines.append("")

    # Typography
    lines.append("### 字体排版")
    lines.append("")
    lines.append(f"- **标题字体：** {typography.get('heading', 'Noto Sans SC')}")
    lines.append(f"- **正文字体：** {typography.get('body', 'Noto Sans SC')}")
    if typography.get("mood"):
        lines.append(f"- **气质：** {typography.get('mood', '')}")
    if typography.get("google_fonts_url"):
        lines.append(f"- **字体链接：** [{typography.get('heading', '')} + {typography.get('body', '')}]({typography.get('google_fonts_url', '')})")
    lines.append("")
    if typography.get("css_import"):
        lines.append("**CSS 引入：**")
        lines.append("```css")
        lines.append(typography.get("css_import", ""))
        lines.append("```")
        lines.append("")

    # Spacing Variables
    lines.append("### 间距变量")
    lines.append("")
    lines.append("| Token | 值 | 用途 |")
    lines.append("|-------|----|------|")
    lines.append("| `--space-xs` | `4px` / `0.25rem` | 贴身间距 |")
    lines.append("| `--space-sm` | `8px` / `0.5rem` | 图标与行内间距 |")
    lines.append("| `--space-md` | `16px` / `1rem` | 常规内边距 |")
    lines.append("| `--space-lg` | `24px` / `1.5rem` | 区块内边距 |")
    lines.append("| `--space-xl` | `32px` / `2rem` | 大型留白 |")
    lines.append("| `--space-2xl` | `48px` / `3rem` | 区块外边距 |")
    lines.append("| `--space-3xl` | `64px` / `4rem` | 首屏区留白 |")
    lines.append("")

    # Shadow Depths
    lines.append("### 阴影层级")
    lines.append("")
    lines.append("| 等级 | 值 | 用途 |")
    lines.append("|------|----|------|")
    lines.append("| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | 轻微抬升 |")
    lines.append("| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | 卡片、按钮 |")
    lines.append("| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | 弹窗、下拉层 |")
    lines.append("| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | 首屏主视觉、重点卡片 |")
    lines.append("")
    
    # Component Specs section
    lines.append("---")
    lines.append("")
    lines.append("## 组件规格")
    lines.append("")
    
    # Buttons
    lines.append("### 按钮")
    lines.append("")
    lines.append("```css")
    lines.append("/* 主按钮 */")
    lines.append(".btn-primary {")
    lines.append(f"  background: {colors.get('cta', '#F97316')};")
    lines.append("  color: white;")
    lines.append("  padding: 12px 24px;")
    lines.append("  border-radius: 8px;")
    lines.append("  font-weight: 600;")
    lines.append("  transition: all 200ms ease;")
    lines.append("  cursor: pointer;")
    lines.append("}")
    lines.append("")
    lines.append(".btn-primary:hover {")
    lines.append("  opacity: 0.9;")
    lines.append("  transform: translateY(-1px);")
    lines.append("}")
    lines.append("")
    lines.append("/* 次按钮 */")
    lines.append(".btn-secondary {")
    lines.append(f"  background: transparent;")
    lines.append(f"  color: {colors.get('primary', '#2563EB')};")
    lines.append(f"  border: 2px solid {colors.get('primary', '#2563EB')};")
    lines.append("  padding: 12px 24px;")
    lines.append("  border-radius: 8px;")
    lines.append("  font-weight: 600;")
    lines.append("  transition: all 200ms ease;")
    lines.append("  cursor: pointer;")
    lines.append("}")
    lines.append("```")
    lines.append("")
    
    # Cards
    lines.append("### 卡片")
    lines.append("")
    lines.append("```css")
    lines.append(".card {")
    lines.append(f"  background: {colors.get('background', '#FFFFFF')};")
    lines.append("  border-radius: 12px;")
    lines.append("  padding: 24px;")
    lines.append("  box-shadow: var(--shadow-md);")
    lines.append("  transition: all 200ms ease;")
    lines.append("  cursor: pointer;")
    lines.append("}")
    lines.append("")
    lines.append(".card:hover {")
    lines.append("  box-shadow: var(--shadow-lg);")
    lines.append("  transform: translateY(-2px);")
    lines.append("}")
    lines.append("```")
    lines.append("")
    
    # Inputs
    lines.append("### 输入框")
    lines.append("")
    lines.append("```css")
    lines.append(".input {")
    lines.append("  padding: 12px 16px;")
    lines.append("  border: 1px solid #E2E8F0;")
    lines.append("  border-radius: 8px;")
    lines.append("  font-size: 16px;")
    lines.append("  transition: border-color 200ms ease;")
    lines.append("}")
    lines.append("")
    lines.append(".input:focus {")
    lines.append(f"  border-color: {colors.get('primary', '#2563EB')};")
    lines.append("  outline: none;")
    lines.append(f"  box-shadow: 0 0 0 3px {colors.get('primary', '#2563EB')}20;")
    lines.append("}")
    lines.append("```")
    lines.append("")
    
    # Modals
    lines.append("### 弹窗")
    lines.append("")
    lines.append("```css")
    lines.append(".modal-overlay {")
    lines.append("  background: rgba(0, 0, 0, 0.5);")
    lines.append("  backdrop-filter: blur(4px);")
    lines.append("}")
    lines.append("")
    lines.append(".modal {")
    lines.append("  background: white;")
    lines.append("  border-radius: 16px;")
    lines.append("  padding: 32px;")
    lines.append("  box-shadow: var(--shadow-xl);")
    lines.append("  max-width: 500px;")
    lines.append("  width: 90%;")
    lines.append("}")
    lines.append("```")
    lines.append("")
    
    # Style section
    lines.append("---")
    lines.append("")
    lines.append("## 风格规范")
    lines.append("")
    lines.append(f"**风格：** {style.get('name', 'Minimalism')}")
    lines.append("")
    if style.get("keywords"):
        lines.append(f"**关键词：** {style.get('keywords', '')}")
        lines.append("")
    if style.get("best_for"):
        lines.append(f"**适用场景：** {style.get('best_for', '')}")
        lines.append("")
    if effects:
        lines.append(f"**关键表现：** {effects}")
        lines.append("")

    # Layout Pattern
    lines.append("### 页面结构")
    lines.append("")
    lines.append(f"**结构名称：** {pattern.get('name', '')}")
    lines.append("")
    if pattern.get('conversion'):
        lines.append(f"- **转化策略：** {pattern.get('conversion', '')}")
    if pattern.get('cta_placement'):
        lines.append(f"- **CTA 位置：** {pattern.get('cta_placement', '')}")
    lines.append(f"- **页面分区：** {pattern.get('sections', '')}")
    lines.append("")

    # Anti-Patterns section
    lines.append("---")
    lines.append("")
    lines.append("## 反模式（禁止使用）")
    lines.append("")
    if anti_patterns:
        anti_list = [a.strip() for a in anti_patterns.split("+")]
        for anti in anti_list:
            if anti:
                lines.append(f"- ❌ {anti}")
    lines.append("")
    lines.append("### 补充禁止项")
    lines.append("")
    lines.append("- ❌ **用表情当图标**：功能图标统一使用 SVG 图标库")
    lines.append("- ❌ **缺少交互态**：所有可点击元素都必须有明确状态反馈")
    lines.append("- ❌ **悬浮导致布局偏移**：避免让 hover/press 影响周边排版")
    lines.append("- ❌ **文本对比度不足**：正文至少满足 4.5:1")
    lines.append("- ❌ **状态变化过于生硬**：默认保留 150-300ms 的过渡")
    lines.append("- ❌ **焦点态不可见**：键盘和辅助技术必须能识别当前焦点")
    lines.append("")

    # Pre-Delivery Checklist
    lines.append("---")
    lines.append("")
    lines.append("## 交付前检查")
    lines.append("")
    lines.append("交付任何 UI 代码前，至少确认以下事项：")
    lines.append("")
    lines.append("- [ ] 不用表情充当功能图标，且图标库保持一致")
    lines.append("- [ ] 所有可点击元素都有明确交互态")
    lines.append("- [ ] 状态过渡保持在 150-300ms")
    lines.append("- [ ] 浅色模式与深色模式都校验 4.5:1 文本对比度")
    lines.append("- [ ] 焦点态、屏幕阅读器标签、错误反馈都可见")
    lines.append("- [ ] 遵守 `prefers-reduced-motion`")
    lines.append("- [ ] 至少验证 375px、768px、1024px、1440px 四档")
    lines.append("- [ ] 固定头部/底部不会遮挡内容")
    lines.append("- [ ] 移动端不存在横向滚动")
    lines.append("")
    
    return "\n".join(lines)


def format_page_override_md(design_system: dict, page_name: str, page_query: str = None) -> str:
    """Format a page-specific override file with intelligent AI-generated content."""
    project = design_system.get("project_name", "PROJECT")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page_title = page_name.replace("-", " ").replace("_", " ").title()
    
    # Detect page type and generate intelligent overrides
    page_overrides = _generate_intelligent_overrides(page_name, page_query, design_system)
    
    lines = []
    
    lines.append(f"# {page_title} 页面覆盖规则")
    lines.append("")
    lines.append(f"> **项目：** {project}")
    lines.append(f"> **生成时间：** {timestamp}")
    lines.append(f"> **页面类型：** {page_overrides.get('page_type', '通用页面')}")
    lines.append("")
    lines.append("> ⚠️ **注意：** 本文件中的规则会 **覆盖** `design-system/MASTER.md`。")
    lines.append("> 这里只记录相对主文件的差异项，未提及部分一律回到主文件执行。")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Page-specific rules with actual content
    lines.append("## 页面专属规则")
    lines.append("")

    # Layout Overrides
    lines.append("### 布局覆盖")
    lines.append("")
    layout = page_overrides.get("layout", {})
    if layout:
        for key, value in layout.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- 无覆盖，沿用主文件布局")
    lines.append("")
    
    # Spacing Overrides
    lines.append("### 间距覆盖")
    lines.append("")
    spacing = page_overrides.get("spacing", {})
    if spacing:
        for key, value in spacing.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- 无覆盖，沿用主文件间距")
    lines.append("")
    
    # Typography Overrides
    lines.append("### 字体覆盖")
    lines.append("")
    typography = page_overrides.get("typography", {})
    if typography:
        for key, value in typography.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- 无覆盖，沿用主文件字体")
    lines.append("")
    
    # Color Overrides
    lines.append("### 颜色覆盖")
    lines.append("")
    colors = page_overrides.get("colors", {})
    if colors:
        for key, value in colors.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- 无覆盖，沿用主文件颜色")
    lines.append("")
    
    # Component Overrides
    lines.append("### 组件覆盖")
    lines.append("")
    components = page_overrides.get("components", [])
    if components:
        for comp in components:
            lines.append(f"- {comp}")
    else:
        lines.append("- 无覆盖，沿用主文件组件规格")
    lines.append("")
    
    # Page-Specific Components
    lines.append("---")
    lines.append("")
    lines.append("## 页面专属组件")
    lines.append("")
    unique_components = page_overrides.get("unique_components", [])
    if unique_components:
        for comp in unique_components:
            lines.append(f"- {comp}")
    else:
        lines.append("- 当前页面没有额外专属组件")
    lines.append("")
    
    # Recommendations
    lines.append("---")
    lines.append("")
    lines.append("## 额外建议")
    lines.append("")
    recommendations = page_overrides.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            lines.append(f"- {rec}")
    lines.append("")
    
    return "\n".join(lines)


def _generate_intelligent_overrides(page_name: str, page_query: str, design_system: dict) -> dict:
    """
    Generate intelligent overrides based on page type using layered search.
    
    Uses the existing search infrastructure to find relevant style, UX, and layout
    data instead of hardcoded page types.
    """
    from core import search
    
    page_lower = page_name.lower()
    query_lower = (page_query or "").lower()
    combined_context = f"{page_lower} {query_lower}"
    
    # Search across multiple domains for page-specific guidance
    style_search = search(combined_context, "style", max_results=1)
    ux_search = search(combined_context, "ux", max_results=3)
    landing_search = search(combined_context, "landing", max_results=1)
    
    # Extract results from search response
    style_results = style_search.get("results", [])
    ux_results = ux_search.get("results", [])
    landing_results = landing_search.get("results", [])
    
    # Detect page type from search results or context
    page_type = _detect_page_type(combined_context, style_results)
    
    # Build overrides from search results
    layout = {}
    spacing = {}
    typography = {}
    colors = {}
    components = []
    unique_components = []
    recommendations = []
    
    # Extract style-based overrides
    if style_results:
        style = style_results[0]
        style_name = style.get("Style Category", "")
        keywords = style.get("Keywords", "")
        best_for = style.get("Best For", "")
        effects = style.get("Effects & Animation", "")
        
        # Infer layout from style keywords
        if any(kw in keywords.lower() for kw in ["data", "dense", "dashboard", "grid"]):
            layout["最大宽度"] = "1400px 或全宽"
            layout["栅格"] = "12 栏栅格，便于数据密度调整"
            spacing["信息密度"] = "高，优先保证信息展示效率"
        elif any(kw in keywords.lower() for kw in ["minimal", "simple", "clean", "single"]):
            layout["最大宽度"] = "800px（窄版聚焦）"
            layout["布局"] = "单列居中"
            spacing["信息密度"] = "低，优先保证清晰度"
        else:
            layout["最大宽度"] = "1200px（标准）"
            layout["布局"] = "通栏分区 + 内容居中"

        if effects:
            recommendations.append(f"表现建议：{effects}")
    
    # Extract UX guidelines as recommendations
    for ux in ux_results:
        category = ux.get("Category", "")
        do_text = ux.get("Do", "")
        dont_text = ux.get("Don't", "")
        if do_text:
            recommendations.append(f"{category}：{do_text}")
        if dont_text:
            components.append(f"避免：{dont_text}")
    
    # Extract landing pattern info for section structure
    if landing_results:
        landing = landing_results[0]
        sections = landing.get("Section Order", "")
        cta_placement = landing.get("Primary CTA Placement", "")
        color_strategy = landing.get("Color Strategy", "")
        
        if sections:
            layout["页面分区"] = sections
        if cta_placement:
            recommendations.append(f"CTA 位置：{cta_placement}")
        if color_strategy:
            colors["策略"] = color_strategy
    
    # Add page-type specific defaults if no search results
    if not layout:
        layout["最大宽度"] = "1200px"
        layout["布局"] = "响应式栅格"

    if not recommendations:
        recommendations = [
            "先回到 MASTER.md 执行全局设计规则",
            "仅在当前页面确有差异时再补充覆盖项"
        ]
    
    return {
        "page_type": page_type,
        "layout": layout,
        "spacing": spacing,
        "typography": typography,
        "colors": colors,
        "components": components,
        "unique_components": unique_components,
        "recommendations": recommendations
    }


def _detect_page_type(context: str, style_results: list) -> str:
    """Detect page type from context and search results."""
    context_lower = normalize_query(context).lower()
    
    # Check for common page type patterns
    page_patterns = [
        (["dashboard", "admin", "analytics", "data", "metrics", "stats", "monitor", "overview"], "仪表盘 / 数据视图"),
        (["checkout", "payment", "cart", "purchase", "order", "billing"], "结算 / 支付"),
        (["settings", "profile", "account", "preferences", "config"], "设置 / 个人中心"),
        (["landing", "marketing", "homepage", "hero", "home", "promo"], "落地页 / 营销页"),
        (["login", "signin", "signup", "register", "auth", "password"], "认证页面"),
        (["pricing", "plans", "subscription", "tiers", "packages"], "价格 / 套餐页"),
        (["blog", "article", "post", "news", "content", "story"], "文章 / 内容页"),
        (["product", "item", "detail", "pdp", "shop", "store"], "详情页"),
        (["search", "results", "browse", "filter", "catalog", "list"], "搜索结果页"),
        (["empty", "404", "error", "not found", "zero"], "空状态 / 错误页"),
    ]
    
    for keywords, page_type in page_patterns:
        if any(kw in context_lower for kw in keywords):
            return page_type
    
    # Fallback: try to infer from style results
    if style_results:
        style_name = style_results[0].get("Style Category", "").lower()
        best_for = style_results[0].get("Best For", "").lower()
        
        if "dashboard" in best_for or "data" in best_for:
            return "仪表盘 / 数据视图"
        elif "landing" in best_for or "marketing" in best_for:
            return "落地页 / 营销页"

    return "通用页面"


# ============ CLI SUPPORT ============
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Design System")
    parser.add_argument("query", help="Search query (e.g., 'SaaS dashboard')")
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="Output format")

    args = parser.parse_args()

    result = generate_design_system(args.query, args.project_name, args.format)
    print(result)
