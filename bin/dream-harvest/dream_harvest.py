#!/usr/bin/env python3
import argparse
import base64
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json_yaml(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def isoformat_from_epoch(epoch_seconds: float) -> str:
    from datetime import datetime
    return datetime.utcfromtimestamp(epoch_seconds).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_unique(target: List[str], values: Iterable[str]) -> None:
    for value in values:
        if value and value not in target:
            target.append(value)


def build_archive_filename(started_at: str, agent: str) -> str:
    return f"{started_at.split('T', 1)[0]}-{agent}.md"


def build_archive_title(day: str, agent: str) -> str:
    return f"# {day} {agent} 对话归档"


def empty_summary() -> Dict[str, List[str]]:
    return {
        "topics": [],
        "conclusions": [],
        "todos": [],
        "risks": [],
    }


def load_archive_sections(path: Path, agent: str, day: Optional[str] = None) -> Dict:
    archive_day = day or path.stem[:10]
    if not path.exists():
        return {
            "title": build_archive_title(archive_day, agent),
            "summary": empty_summary(),
            "sessions": [],
        }
    return parse_archive_sections(path.read_text(encoding="utf-8"), agent, archive_day)


def parse_archive_sections(content: str, agent: str, day: str) -> Dict:
    summary = empty_summary()
    sessions = []
    blocks = content.split("\n## 会话 ")
    header = blocks[0]
    for line in header.splitlines():
        if line.startswith("- 今日主题："):
            append_unique(summary["topics"], [line.split("：", 1)[1]])
        elif line.startswith("- 关键结论："):
            append_unique(summary["conclusions"], [line.split("：", 1)[1]])
        elif line.startswith("- 待办事项："):
            append_unique(summary["todos"], [line.split("：", 1)[1]])
        elif line.startswith("- 风险与未决问题："):
            append_unique(summary["risks"], [line.split("：", 1)[1]])
    for block in blocks[1:]:
        lines = block.splitlines()
        index = int(lines[0].strip())
        session = {
            "index": index,
            "session_id": "",
            "started_at": "",
            "ended_at": "",
            "project": "",
            "messages": [],
            "summary": empty_summary(),
        }
        current_role = None
        for line in lines[1:]:
            if line.startswith("- session_id："):
                session["session_id"] = line.split("：", 1)[1]
            elif line.startswith("- 开始时间："):
                session["started_at"] = line.split("：", 1)[1]
            elif line.startswith("- 结束时间："):
                session["ended_at"] = line.split("：", 1)[1]
            elif line.startswith("- 项目："):
                session["project"] = line.split("：", 1)[1]
            elif line.startswith("- 主题："):
                append_unique(session["summary"]["topics"], [line.split("：", 1)[1]])
            elif line.startswith("- 结论："):
                append_unique(session["summary"]["conclusions"], [line.split("：", 1)[1]])
            elif line.startswith("- 待办："):
                append_unique(session["summary"]["todos"], [line.split("：", 1)[1]])
            elif line.startswith("- 风险："):
                append_unique(session["summary"]["risks"], [line.split("：", 1)[1]])
            elif line == "#### User":
                current_role = "user"
            elif line == "#### Assistant":
                current_role = "assistant"
            elif current_role and line:
                session["messages"].append({"role": current_role, "text": line})
                current_role = None
        sessions.append(session)
    return {
        "title": build_archive_title(day, agent),
        "summary": summary,
        "sessions": sessions,
    }


def merge_daily_summary(sections: Dict, summary: Dict) -> None:
    append_unique(sections["summary"]["topics"], summary.get("topics", []))
    append_unique(sections["summary"]["conclusions"], summary.get("conclusions", []))
    append_unique(sections["summary"]["todos"], summary.get("todos", []))
    append_unique(sections["summary"]["risks"], summary.get("risks", []))


def build_session_section(index: int, session: Dict) -> Dict:
    return {
        "index": index,
        "session_id": session["session_id"],
        "started_at": session.get("started_at", ""),
        "ended_at": session.get("ended_at", ""),
        "project": session.get("project", ""),
        "messages": list(session.get("messages", [])),
        "summary": {
            "topics": list(session.get("summary", {}).get("topics", [])),
            "conclusions": list(session.get("summary", {}).get("conclusions", [])),
            "todos": list(session.get("summary", {}).get("todos", [])),
            "risks": list(session.get("summary", {}).get("risks", [])),
        },
    }


def merge_session_section(sections: Dict, session: Dict) -> None:
    for existing in sections["sessions"]:
        if existing["session_id"] == session["session_id"]:
            existing.update(build_session_section(existing["index"], session))
            return
    sections["sessions"].append(build_session_section(len(sections["sessions"]) + 1, session))


def render_archive_sections(sections: Dict) -> str:
    summary = sections["summary"]
    lines = [
        sections["title"],
        "",
        "## 当日摘要",
        f"- 今日主题：{'；'.join(summary['topics'])}",
        f"- 关键结论：{'；'.join(summary['conclusions'])}",
        f"- 待办事项：{'；'.join(summary['todos'])}",
        f"- 风险与未决问题：{'；'.join(summary['risks'])}",
    ]
    for session in sections["sessions"]:
        lines.extend([
            "",
            f"## 会话 {session['index']:02d}",
            "### 元信息",
            f"- session_id：{session['session_id']}",
            f"- 开始时间：{session['started_at']}",
            f"- 结束时间：{session['ended_at']}",
            f"- 项目：{session['project']}",
            "- 标签：",
            "",
            "### 会话摘要",
            f"- 主题：{'；'.join(session['summary']['topics'])}",
            f"- 结论：{'；'.join(session['summary']['conclusions'])}",
            f"- 待办：{'；'.join(session['summary']['todos'])}",
            f"- 风险：{'；'.join(session['summary']['risks'])}",
            "",
            "### 完整对话",
        ])
        for message in session["messages"]:
            label = "User" if message["role"] == "user" else "Assistant"
            lines.extend([f"#### {label}", message["text"]])
    return "\n".join(lines) + "\n"


def write_archive_sections(path: Path, sections: Dict) -> None:
    write_text(path, render_archive_sections(sections))


def upsert_archive_session(archive_dir: Path, state_dir: Path, session: Dict) -> Dict:
    archive_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / build_archive_filename(session["started_at"], session["agent"])
    archive_day = session["started_at"].split("T", 1)[0]
    sections = load_archive_sections(archive_file, session["agent"], archive_day)
    sections["title"] = build_archive_title(archive_day, session["agent"])
    merge_daily_summary(sections, session.get("summary", empty_summary()))
    merge_session_section(sections, session)
    write_archive_sections(archive_file, sections)
    return {"archive_file": archive_file}


def load_scan_state(path: Path) -> Dict:
    if not path.exists():
        return {"files": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_scan_state(path: Path, payload: Dict) -> None:
    write_json_yaml(path, payload)


def read_appended_lines(path: Path, file_state: Dict) -> Iterable[str]:
    offset = file_state.get("offset", 0)
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        for line in handle:
            yield line.rstrip("\n")


def build_file_state(path: Path) -> Dict:
    stat = path.stat()
    return {
        "offset": stat.st_size,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }


def should_rescan_from_start(path: Path, file_state: Dict) -> bool:
    stat = path.stat()
    return stat.st_size < file_state.get("offset", 0) or stat.st_mtime != file_state.get("mtime")


def collect_codex_message_text(content: List[Dict]) -> str:
    parts = []
    for item in content:
        text = item.get("text")
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def collect_claude_message_text(message: Dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            text = item.get("text")
            if text:
                parts.append(text)
        return "\n".join(parts).strip()
    return ""


def finalize_session_summary(session: Dict) -> Dict:
    summary = session.get("summary") or empty_summary()
    if session.get("messages"):
        first_user = next((item["text"] for item in session["messages"] if item["role"] == "user"), "")
        last_assistant = next((item["text"] for item in reversed(session["messages"]) if item["role"] == "assistant"), "")
        append_unique(summary["topics"], [first_user])
        append_unique(summary["conclusions"], [last_assistant])
    session["summary"] = summary
    return session


def parse_codex_session_file(path: Path) -> Dict:
    session = {
        "agent": "codex",
        "session_id": "",
        "started_at": "",
        "ended_at": "",
        "project": "",
        "messages": [],
        "summary": empty_summary(),
    }
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item.get("type") == "session_meta":
            payload = item.get("payload", {})
            session["session_id"] = payload.get("id", "")
            session["started_at"] = payload.get("timestamp", "")
            session["project"] = payload.get("cwd", "")
        elif item.get("type") == "response_item":
            payload = item.get("payload", {})
            if payload.get("type") != "message" or payload.get("role") not in {"user", "assistant"}:
                continue
            text = collect_codex_message_text(payload.get("content", []))
            if not text:
                continue
            session["messages"].append({"role": payload["role"], "text": text})
            session["ended_at"] = item.get("timestamp", session["started_at"])
    return finalize_session_summary(session)


def parse_claude_session_file(path: Path) -> Dict:
    session = {
        "agent": "claude-code",
        "session_id": "",
        "started_at": "",
        "ended_at": "",
        "project": "",
        "messages": [],
        "summary": empty_summary(),
    }
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item.get("type") not in {"user", "assistant"}:
            continue
        session["session_id"] = item.get("sessionId", session["session_id"])
        session["started_at"] = session["started_at"] or item.get("timestamp", "")
        session["ended_at"] = item.get("timestamp", session["ended_at"])
        session["project"] = session["project"] or item.get("cwd", "")
        text = collect_claude_message_text(item.get("message", {}))
        if not text:
            continue
        session["messages"].append({"role": item["type"], "text": text})
    return finalize_session_summary(session)


def parse_jetbrains_events_file(path: Path, raw_session_id: str) -> Dict:
    file_time = isoformat_from_epoch(path.stat().st_mtime)
    agent_id = raw_session_id.split(":", 1)[0].strip() if ":" in raw_session_id else ""
    session = {
        "agent": "jetbrains-ai",
        "session_id": raw_session_id.split(":", 1)[-1],
        "started_at": file_time,
        "ended_at": file_time,
        "project": "",
        "messages": [],
        "summary": empty_summary(),
    }
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if not line:
            continue
        payload = json.loads(base64.b64decode(line).decode("utf-8"))
        event_type = payload.get("type", "")
        payload_agent_id = ((payload.get("agentId") or {}).get("id") or "").strip()
        if not agent_id and payload_agent_id:
            agent_id = payload_agent_id
        if event_type.endswith("ChatSessionUserPromptEvent"):
            text = payload.get("prompt", "").strip()
            if text:
                session["messages"].append({"role": "user", "text": text})
        elif event_type.endswith("ChatSessionMessageBlockEvent"):
            text = (((payload.get("event") or {}).get("text")) or "").strip()
            if text:
                session["messages"].append({"role": "assistant", "text": text})
    if agent_id:
        session["agent"] = f"jetbrains-ai-{agent_id}"
    return finalize_session_summary(session)


def migrate_legacy_jetbrains_archives(archive_dir: Path, source_root: Optional[Path] = None) -> int:
    session_agents: Dict[str, str] = {}
    for path in iter_source_files("jetbrains-ai", source_root):
        session = parse_source_file("jetbrains-ai", path)
        if not session or not session.get("session_id"):
            continue
        session_agents[session["session_id"]] = session.get("agent", "jetbrains-ai")

    migrated = 0
    for legacy_file in sorted(archive_dir.glob("*-jetbrains-ai.md")):
        day = legacy_file.stem[:10]
        legacy_sections = parse_archive_sections(legacy_file.read_text(encoding="utf-8"), "jetbrains-ai", day)
        grouped_sessions: Dict[str, List[Dict]] = {}
        fallback_sessions: List[Dict] = []
        for session in legacy_sections["sessions"]:
            target_agent = session_agents.get(session["session_id"], "")
            if target_agent:
                grouped_sessions.setdefault(target_agent, []).append(session)
            else:
                fallback_sessions.append(session)

        if fallback_sessions:
            known_agents = [agent for agent in grouped_sessions if agent != "jetbrains-ai"]
            if len(known_agents) == 1:
                grouped_sessions.setdefault(known_agents[0], []).extend(fallback_sessions)
            else:
                grouped_sessions.setdefault("jetbrains-ai", []).extend(fallback_sessions)

        keep_legacy_file = False
        for target_agent, sessions in grouped_sessions.items():
            target_file = archive_dir / f"{day}-{target_agent}.md"
            target_sections = load_archive_sections(target_file, target_agent, day)
            target_sections["title"] = build_archive_title(day, target_agent)
            for session in sessions:
                merge_daily_summary(target_sections, session.get("summary", empty_summary()))
                merge_session_section(target_sections, session)
            write_archive_sections(target_file, target_sections)
            if target_file == legacy_file:
                keep_legacy_file = True

        if keep_legacy_file:
            legacy_sections["title"] = build_archive_title(day, "jetbrains-ai")
            write_archive_sections(legacy_file, legacy_sections)
        else:
            legacy_file.unlink()
        migrated += 1
    return migrated


def default_source_path(source: str) -> Path:
    home = Path.home()
    mapping = {
        "codex": home / ".codex" / "sessions",
        "claude-code": home / ".claude" / "projects",
        "jetbrains-ai": home / "Library" / "Application Support" / "JetBrains",
    }
    return mapping[source]


def iter_source_files(source: str, source_root: Optional[Path] = None) -> Iterable[Path]:
    if source_root is not None:
        base = source_root / source
        if source == "jetbrains-ai":
            yield from sorted(base.rglob("*.events"))
        else:
            yield from sorted(base.rglob("*.jsonl"))
        return

    base = default_source_path(source)
    if source == "codex":
        yield from sorted(base.rglob("*.jsonl"))
    elif source == "claude-code":
        yield from sorted(base.rglob("*.jsonl"))
    elif source == "jetbrains-ai":
        yield from sorted(base.rglob("*.events"))


def parse_source_file(source: str, path: Path) -> Optional[Dict]:
    if source == "codex":
        return parse_codex_session_file(path)
    if source == "claude-code":
        return parse_claude_session_file(path)
    if source == "jetbrains-ai":
        agent_session = path.with_suffix(".agentsession")
        raw_session_id = agent_session.read_text(encoding="utf-8").strip() if agent_session.exists() else path.stem
        return parse_jetbrains_events_file(path, raw_session_id)
    return None


def run_dream_harvest(archive_dir: Path, sources: List[str], source_root: Optional[Path] = None) -> Dict:
    state_dir = archive_dir / ".state"
    archive_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    results = {"processed": 0, "sources": {}}
    for source in sources:
        if source == "jetbrains-ai":
            migrate_legacy_jetbrains_archives(archive_dir, source_root)
        state_file = state_dir / f"{source}.json"
        state = load_scan_state(state_file)
        state.setdefault("files", {})
        processed = 0
        for path in iter_source_files(source, source_root):
            file_key = str(path)
            previous = state["files"].get(file_key)
            current = build_file_state(path)
            if previous and previous.get("size") == current["size"] and previous.get("mtime") == current["mtime"]:
                continue
            session = parse_source_file(source, path)
            if session and session.get("session_id") and session.get("messages"):
                upsert_archive_session(archive_dir, state_dir, session)
                processed += 1
            state["files"][file_key] = current
        save_scan_state(state_file, state)
        results["sources"][source] = processed
        results["processed"] += processed
    return results


def main_dream_harvest_args(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="采集本地 AI 会话并归档到 .dream")
    parser.add_argument("--archive-dir", type=Path, default=default_root() / ".dream")
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--source", action="append", dest="sources")
    args = parser.parse_args(argv)
    run_dream_harvest(
        archive_dir=args.archive_dir,
        sources=args.sources or ["codex", "claude-code", "jetbrains-ai"],
        source_root=args.source_root,
    )
    return 0


def main_dream_harvest() -> int:
    return main_dream_harvest_args()
