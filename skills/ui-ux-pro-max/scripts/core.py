#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI/UX Pro Max Core - BM25 search engine for UI/UX style guides
"""

import csv
import re
from pathlib import Path
from math import log
from collections import defaultdict

# ============ CONFIGURATION ============
DATA_DIR = Path(__file__).parent.parent / "data"
MAX_RESULTS = 3

CSV_CONFIG = {
    "style": {
        "file": "styles.csv",
        "search_cols": ["Style Category", "Keywords", "Best For", "Type", "AI Prompt Keywords"],
        "output_cols": ["Style Category", "Type", "Keywords", "Primary Colors", "Effects & Animation", "Best For", "Light Mode ✓", "Dark Mode ✓", "Performance", "Accessibility", "Framework Compatibility", "Complexity", "AI Prompt Keywords", "CSS/Technical Keywords", "Implementation Checklist", "Design System Variables"]
    },
    "color": {
        "file": "colors.csv",
        "search_cols": ["Product Type", "Notes"],
        "output_cols": ["Product Type", "Primary", "On Primary", "Secondary", "On Secondary", "Accent", "On Accent", "Background", "Foreground", "Card", "Card Foreground", "Muted", "Muted Foreground", "Border", "Destructive", "On Destructive", "Ring", "Notes"]
    },
    "chart": {
        "file": "charts.csv",
        "search_cols": ["Data Type", "Keywords", "Best Chart Type", "When to Use", "When NOT to Use", "Accessibility Notes"],
        "output_cols": ["Data Type", "Keywords", "Best Chart Type", "Secondary Options", "When to Use", "When NOT to Use", "Data Volume Threshold", "Color Guidance", "Accessibility Grade", "Accessibility Notes", "A11y Fallback", "Library Recommendation", "Interactive Level"]
    },
    "landing": {
        "file": "landing.csv",
        "search_cols": ["Pattern Name", "Keywords", "Conversion Optimization", "Section Order"],
        "output_cols": ["Pattern Name", "Keywords", "Section Order", "Primary CTA Placement", "Color Strategy", "Conversion Optimization"]
    },
    "product": {
        "file": "products.csv",
        "search_cols": ["Product Type", "Keywords", "Primary Style Recommendation", "Key Considerations"],
        "output_cols": ["Product Type", "Keywords", "Primary Style Recommendation", "Secondary Styles", "Landing Page Pattern", "Dashboard Style (if applicable)", "Color Palette Focus"]
    },
    "ux": {
        "file": "ux-guidelines.csv",
        "search_cols": ["Category", "Issue", "Description", "Platform"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"]
    },
    "typography": {
        "file": "typography.csv",
        "search_cols": ["Font Pairing Name", "Category", "Mood/Style Keywords", "Best For", "Heading Font", "Body Font"],
        "output_cols": ["Font Pairing Name", "Category", "Heading Font", "Body Font", "Mood/Style Keywords", "Best For", "Google Fonts URL", "CSS Import", "Tailwind Config", "Notes"]
    },
    "icons": {
        "file": "icons.csv",
        "search_cols": ["Category", "Icon Name", "Keywords", "Best For"],
        "output_cols": ["Category", "Icon Name", "Keywords", "Library", "Import Code", "Usage", "Best For", "Style"]
    },
    "react": {
        "file": "react-performance.csv",
        "search_cols": ["Category", "Issue", "Keywords", "Description"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"]
    },
    "web": {
        "file": "app-interface.csv",
        "search_cols": ["Category", "Issue", "Keywords", "Description"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"]
    },
    "google-fonts": {
        "file": "google-fonts.csv",
        "search_cols": ["Family", "Category", "Stroke", "Classifications", "Keywords", "Subsets", "Designers"],
        "output_cols": ["Family", "Category", "Stroke", "Classifications", "Styles", "Variable Axes", "Subsets", "Designers", "Popularity Rank", "Google Fonts URL"]
    }
}

STACK_CONFIG = {
    "react-native": {"file": "stacks/react-native.csv"},
}

# Common columns for all stacks
_STACK_COLS = {
    "search_cols": ["Category", "Guideline", "Description", "Do", "Don't"],
    "output_cols": ["Category", "Guideline", "Description", "Do", "Don't", "Code Good", "Code Bad", "Severity", "Docs URL"]
}

AVAILABLE_STACKS = list(STACK_CONFIG.keys())

CJK_RE = re.compile(r'[\u3400-\u9fff]')
CJK_BLOCK_RE = re.compile(r'[\u3400-\u9fff]+')

# Longest phrases should come first to avoid shorter aliases swallowing intent.
QUERY_ALIASES = [
    ("数据大屏", ["dashboard", "analytics", "monitoring", "data panel"]),
    ("数据看板", ["dashboard", "analytics", "monitoring"]),
    ("仪表盘", ["dashboard", "analytics", "panel"]),
    ("管理后台", ["admin", "dashboard", "management"]),
    ("后台", ["admin", "dashboard", "management"]),
    ("落地页", ["landing page", "hero", "conversion", "cta"]),
    ("官网", ["landing page", "homepage", "marketing website"]),
    ("首页", ["homepage", "landing", "hero"]),
    ("详情页", ["product detail", "detail page"]),
    ("列表页", ["list", "catalog", "results"]),
    ("小程序", ["mini program", "wechat", "mobile app"]),
    ("小红书", ["social media", "content", "community", "creator economy"]),
    ("直播", ["streaming", "live", "media"]),
    ("短视频", ["video", "streaming", "social media"]),
    ("社区", ["community", "social", "content"]),
    ("社交", ["social", "community", "sharing"]),
    ("内容", ["content", "media", "creator"]),
    ("电商", ["ecommerce", "retail", "shop", "store"]),
    ("商城", ["ecommerce", "retail", "shop", "store"]),
    ("医疗", ["medical", "healthcare", "clinic", "patient"]),
    ("问诊", ["medical", "healthcare", "consultation", "patient"]),
    ("健康", ["health", "healthcare", "wellness"]),
    ("教育", ["education", "learning", "training", "school"]),
    ("课程", ["education", "learning", "course"]),
    ("金融", ["finance", "fintech", "banking", "payment"]),
    ("支付", ["payment", "finance", "checkout"]),
    ("政务", ["government", "public service", "accessible"]),
    ("餐饮", ["restaurant", "food service", "booking"]),
    ("外卖", ["delivery", "food", "order"]),
    ("旅游", ["travel", "tourism", "booking"]),
    ("酒店", ["hotel", "hospitality", "booking"]),
    ("房产", ["real estate", "property", "housing"]),
    ("家装", ["home", "service", "lifestyle"]),
    ("汽车", ["automotive", "vehicle", "dashboard"]),
    ("工具", ["tool", "utility", "productivity"]),
    ("效率", ["productivity", "workflow", "tool"]),
    ("办公", ["productivity", "workflow", "collaboration"]),
    ("企业服务", ["b2b service", "enterprise", "saas"]),
    ("客服", ["support", "service", "chat"]),
    ("知识库", ["knowledge base", "documentation", "search"]),
    ("AI", ["ai", "artificial intelligence", "chatbot", "assistant"]),
    ("搜索", ["search", "results", "query"]),
    ("聊天", ["chat", "messenger", "conversation"]),
    ("注册", ["signup", "register", "authentication"]),
    ("登录", ["login", "signin", "authentication"]),
    ("结账", ["checkout", "payment", "cart"]),
    ("下单", ["checkout", "order", "payment"]),
    ("表单", ["form", "validation", "input"]),
    ("图表", ["chart", "graph", "visualization"]),
    ("配色", ["color", "palette", "semantic color"]),
    ("颜色", ["color", "palette"]),
    ("字体", ["font", "typography", "typeface"]),
    ("字体系", ["typography", "font pairing"]),
    ("图标", ["icon", "svg icon", "symbol"]),
    ("无障碍", ["accessibility", "wcag", "a11y"]),
    ("可访问性", ["accessibility", "wcag", "a11y"]),
    ("动效", ["animation", "motion", "micro interaction"]),
    ("交互", ["ux", "interaction", "usability"]),
    ("加载", ["loading", "skeleton", "progress"]),
    ("转化", ["conversion", "cta", "landing"]),
    ("极简", ["minimal", "minimalism", "clean"]),
    ("简约", ["minimal", "minimalism", "clean"]),
    ("高级感", ["luxury", "premium", "elegant"]),
    ("科技感", ["futuristic", "tech", "modern"]),
    ("年轻化", ["playful", "vibrant", "gen z"]),
    ("国潮", ["brand", "editorial", "bold", "premium"]),
    ("玻璃拟态", ["glassmorphism", "frosted glass", "blur"]),
    ("新拟态", ["neumorphism", "soft ui"]),
    ("粗野主义", ["brutalism", "bold", "raw"]),
    ("新粗野", ["neubrutalism", "bold", "playful"]),
    ("深色模式", ["dark mode", "oled"]),
    ("暗黑", ["dark mode", "oled"]),
    ("明亮", ["light mode", "bright"]),
    ("高密度", ["data dense", "dense", "dashboard"]),
]


def _contains_cjk(text):
    return bool(CJK_RE.search(str(text)))


def _cjk_ngrams(text, min_n=2, max_n=3):
    grams = []
    cleaned = "".join(CJK_BLOCK_RE.findall(str(text)))
    for n in range(min_n, max_n + 1):
        if len(cleaned) < n:
            continue
        for idx in range(len(cleaned) - n + 1):
            grams.append(cleaned[idx:idx + n])
    return grams


def normalize_query(query):
    """Expand Chinese intent into English search aliases while preserving the original query."""
    raw_query = str(query).strip()
    lowered = raw_query.lower()
    expanded_parts = [raw_query]

    for phrase, aliases in QUERY_ALIASES:
        if phrase in raw_query or phrase.lower() in lowered:
            expanded_parts.extend(aliases)

    expanded_parts.extend(re.findall(r'[a-z0-9][a-z0-9+#./-]*', lowered))

    if _contains_cjk(raw_query):
        for chunk in CJK_BLOCK_RE.findall(raw_query):
            expanded_parts.append(chunk)
            expanded_parts.extend(_cjk_ngrams(chunk))

    deduped = []
    seen = set()
    for part in expanded_parts:
        for token in str(part).split():
            token = token.strip()
            if token and token not in seen:
                seen.add(token)
                deduped.append(token)

    return " ".join(deduped)


# ============ BM25 IMPLEMENTATION ============
class BM25:
    """BM25 ranking algorithm for text search"""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_lengths = []
        self.avgdl = 0
        self.idf = {}
        self.doc_freqs = defaultdict(int)
        self.N = 0

    def tokenize(self, text):
        """Tokenize Latin text and CJK text for mixed-language search."""
        text = str(text).lower()
        ascii_text = re.sub(r'[^a-z0-9+#./\-\s]', ' ', text)
        ascii_tokens = [w for w in ascii_text.split() if len(w) > 1]

        cjk_tokens = []
        for chunk in CJK_BLOCK_RE.findall(text):
            cjk_tokens.append(chunk)
            cjk_tokens.extend(_cjk_ngrams(chunk))

        return ascii_tokens + cjk_tokens

    def fit(self, documents):
        """Build BM25 index from documents"""
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.N = len(self.corpus)
        if self.N == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lengths) / self.N

        for doc in self.corpus:
            seen = set()
            for word in doc:
                if word not in seen:
                    self.doc_freqs[word] += 1
                    seen.add(word)

        for word, freq in self.doc_freqs.items():
            self.idf[word] = log((self.N - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query):
        """Score all documents against query"""
        query_tokens = self.tokenize(query)
        scores = []

        for idx, doc in enumerate(self.corpus):
            score = 0
            doc_len = self.doc_lengths[idx]
            term_freqs = defaultdict(int)
            for word in doc:
                term_freqs[word] += 1

            for token in query_tokens:
                if token in self.idf:
                    tf = term_freqs[token]
                    idf = self.idf[token]
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                    score += idf * numerator / denominator

            scores.append((idx, score))

        return sorted(scores, key=lambda x: x[1], reverse=True)


# ============ SEARCH FUNCTIONS ============
def _load_csv(filepath):
    """Load CSV and return list of dicts"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _search_csv(filepath, search_cols, output_cols, query, max_results):
    """Core search function using BM25"""
    if not filepath.exists():
        return []

    data = _load_csv(filepath)

    # Build documents from search columns
    documents = [" ".join(str(row.get(col, "")) for col in search_cols) for row in data]

    # BM25 search
    bm25 = BM25()
    bm25.fit(documents)
    ranked = bm25.score(query)

    # Get top results with score > 0
    results = []
    for idx, score in ranked[:max_results]:
        if score > 0:
            row = data[idx]
            results.append({col: row.get(col, "") for col in output_cols if col in row})

    return results


def detect_domain(query):
    """Auto-detect the most relevant domain from query"""
    query_lower = normalize_query(query).lower()

    domain_keywords = {
        "color": ["color", "palette", "hex", "#", "rgb", "token", "semantic", "accent", "destructive", "muted", "foreground"],
        "chart": ["chart", "graph", "visualization", "trend", "bar", "pie", "scatter", "heatmap", "funnel"],
        "landing": ["landing", "page", "cta", "conversion", "hero", "testimonial", "pricing", "section"],
        "product": ["saas", "ecommerce", "e-commerce", "fintech", "healthcare", "gaming", "portfolio", "crypto", "dashboard", "fitness", "restaurant", "hotel", "travel", "music", "education", "learning", "legal", "insurance", "medical", "beauty", "pharmacy", "dental", "pet", "dating", "wedding", "recipe", "delivery", "ride", "booking", "calendar", "timer", "tracker", "diary", "note", "chat", "messenger", "crm", "invoice", "parking", "transit", "vpn", "alarm", "weather", "sleep", "meditation", "fasting", "habit", "grocery", "meme", "wardrobe", "plant care", "reading", "flashcard", "puzzle", "trivia", "arcade", "photography", "streaming", "podcast", "newsletter", "marketplace", "freelancer", "coworking", "airline", "museum", "theater", "church", "non-profit", "charity", "kindergarten", "daycare", "senior care", "veterinary", "florist", "bakery", "brewery", "construction", "automotive", "real estate", "logistics", "agriculture", "coding bootcamp"],
        "style": ["style", "design", "ui", "minimalism", "glassmorphism", "neumorphism", "brutalism", "dark mode", "flat", "aurora", "prompt", "css", "implementation", "variable", "checklist", "tailwind"],
        "ux": ["ux", "usability", "accessibility", "wcag", "touch", "scroll", "animation", "keyboard", "navigation", "mobile"],
        "typography": ["font pairing", "typography pairing", "heading font", "body font"],
        "google-fonts": ["google font", "font family", "font weight", "font style", "variable font", "noto", "font for", "find font", "font subset", "font language", "monospace font", "serif font", "sans serif font", "display font", "handwriting font", "font", "typography", "serif", "sans"],
        "icons": ["icon", "icons", "lucide", "heroicons", "symbol", "glyph", "pictogram", "svg icon"],
        "react": ["react", "next.js", "nextjs", "suspense", "memo", "usecallback", "useeffect", "rerender", "bundle", "waterfall", "barrel", "dynamic import", "rsc", "server component"],
        "web": ["aria", "focus", "outline", "semantic", "virtualize", "autocomplete", "form", "input type", "preconnect"]
    }

    scores = {domain: sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', query_lower)) for domain, keywords in domain_keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "style"


def search(query, domain=None, max_results=MAX_RESULTS):
    """Main search function with auto-domain detection"""
    normalized_query = normalize_query(query)

    if domain is None:
        domain = detect_domain(normalized_query)

    config = CSV_CONFIG.get(domain, CSV_CONFIG["style"])
    filepath = DATA_DIR / config["file"]

    if not filepath.exists():
        return {"error": f"File not found: {filepath}", "domain": domain}

    results = _search_csv(filepath, config["search_cols"], config["output_cols"], normalized_query, max_results)

    return {
        "domain": domain,
        "query": query,
        "normalized_query": normalized_query,
        "file": config["file"],
        "count": len(results),
        "results": results
    }


def search_stack(query, stack, max_results=MAX_RESULTS):
    """Search stack-specific guidelines"""
    if stack not in STACK_CONFIG:
        return {"error": f"Unknown stack: {stack}. Available: {', '.join(AVAILABLE_STACKS)}"}

    filepath = DATA_DIR / STACK_CONFIG[stack]["file"]

    if not filepath.exists():
        return {"error": f"Stack file not found: {filepath}", "stack": stack}

    normalized_query = normalize_query(query)
    results = _search_csv(filepath, _STACK_COLS["search_cols"], _STACK_COLS["output_cols"], normalized_query, max_results)

    return {
        "domain": "stack",
        "stack": stack,
        "query": query,
        "normalized_query": normalized_query,
        "file": STACK_CONFIG[stack]["file"],
        "count": len(results),
        "results": results
    }
