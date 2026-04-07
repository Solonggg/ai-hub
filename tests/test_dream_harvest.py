import sys
import tempfile
import unittest
from base64 import b64encode
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin" / "dream-harvest"))

from dream_harvest import (
    build_file_state,
    load_scan_state,
    main_dream_harvest_args,
    migrate_legacy_jetbrains_archives,
    parse_claude_session_file,
    parse_codex_session_file,
    parse_jetbrains_events_file,
    read_appended_lines,
    run_dream_harvest,
    save_scan_state,
    should_rescan_from_start,
    upsert_archive_session,
)


def build_session_payload(session_id: str, conclusion: str, assistant_text: str) -> dict:
    return {
        "agent": "codex",
        "session_id": session_id,
        "started_at": "2026-04-03T08:00:00Z",
        "ended_at": "2026-04-03T08:30:00Z",
        "project": "/tmp/demo",
        "summary": {
            "topics": ["归档设计"],
            "conclusions": [conclusion],
            "todos": ["实现脚本"],
            "risks": ["JetBrains 格式不稳定"],
        },
        "messages": [
            {"role": "user", "text": "先给出方案"},
            {"role": "assistant", "text": assistant_text},
        ],
    }


def create_codex_sample(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"timestamp":"2026-04-03T05:45:55.956Z","type":"session_meta","payload":{"id":"codex-1","timestamp":"2026-04-03T05:45:49.022Z","cwd":"/tmp/demo"}}\n'
        '{"timestamp":"2026-04-03T05:45:55.958Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"你好"}]}}\n'
        '{"timestamp":"2026-04-03T05:45:56.958Z","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"你好，我来归档"}]}}\n',
        encoding="utf-8",
    )


class DreamHarvestTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_write_session_creates_daily_markdown_and_summary(self) -> None:
        archive_dir = self.root / ".dream"
        state_dir = archive_dir / ".state"

        result = upsert_archive_session(
            archive_dir,
            state_dir,
            build_session_payload("codex-session-1", "采用增量续扫", "采用方案3"),
        )

        daily_file = archive_dir / "2026-04-03-codex.md"
        self.assertEqual(daily_file, result["archive_file"])
        content = daily_file.read_text(encoding="utf-8")
        self.assertIn("## 当日摘要", content)
        self.assertIn("## 会话 01", content)
        self.assertIn("- session_id：codex-session-1", content)
        self.assertIn("#### User", content)
        self.assertIn("#### Assistant", content)

    def test_write_session_updates_existing_session_section(self) -> None:
        archive_dir = self.root / ".dream"
        state_dir = archive_dir / ".state"

        upsert_archive_session(
            archive_dir,
            state_dir,
            build_session_payload("codex-session-1", "原始结论", "第一版回答"),
        )
        upsert_archive_session(
            archive_dir,
            state_dir,
            build_session_payload("codex-session-1", "更新结论", "第二版回答"),
        )

        content = (archive_dir / "2026-04-03-codex.md").read_text(encoding="utf-8")
        self.assertEqual(1, content.count("## 会话 01"))
        self.assertNotIn("## 会话 02", content)
        self.assertIn("更新结论", content)
        self.assertIn("第二版回答", content)

    def test_scan_state_resumes_from_previous_offset(self) -> None:
        source_file = self.root / "codex" / "sample.jsonl"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("line-1\nline-2\n", encoding="utf-8")
        state_file = self.root / ".dream" / ".state" / "codex.json"
        save_scan_state(state_file, {"files": {str(source_file): {"offset": len("line-1\n")}}})

        lines = list(read_appended_lines(source_file, load_scan_state(state_file)["files"][str(source_file)]))

        self.assertEqual(["line-2"], lines)

    def test_rewritten_file_forces_full_rescan(self) -> None:
        source_file = self.root / "jetbrains" / "events.log"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("old\n", encoding="utf-8")
        original = build_file_state(source_file)
        source_file.write_text("new\n", encoding="utf-8")

        self.assertTrue(should_rescan_from_start(source_file, original))

    def test_parse_codex_session_jsonl(self) -> None:
        source_file = self.root / "codex" / "rollout.jsonl"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(
            '{"timestamp":"2026-04-03T05:45:55.956Z","type":"session_meta","payload":{"id":"codex-1","timestamp":"2026-04-03T05:45:49.022Z","cwd":"/tmp/demo"}}\n'
            '{"timestamp":"2026-04-03T05:45:55.958Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"你好"}]}}\n'
            '{"timestamp":"2026-04-03T05:45:56.958Z","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"你好，我来归档"}]}}\n',
            encoding="utf-8",
        )

        session = parse_codex_session_file(source_file)

        self.assertEqual("codex-1", session["session_id"])
        self.assertEqual("codex", session["agent"])
        self.assertEqual("你好", session["messages"][0]["text"])
        self.assertEqual("你好，我来归档", session["messages"][1]["text"])

    def test_parse_claude_session_jsonl(self) -> None:
        source_file = self.root / "claude" / "sample.jsonl"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(
            '{"type":"user","sessionId":"claude-1","timestamp":"2026-04-03T01:00:00Z","cwd":"/tmp/demo","message":{"role":"user","content":"先给方案"}}\n'
            '{"type":"assistant","sessionId":"claude-1","timestamp":"2026-04-03T01:01:00Z","message":{"role":"assistant","content":[{"type":"text","text":"采用方案3"}]}}\n',
            encoding="utf-8",
        )

        session = parse_claude_session_file(source_file)

        self.assertEqual("claude-1", session["session_id"])
        self.assertEqual("claude-code", session["agent"])
        self.assertEqual("先给方案", session["messages"][0]["text"])
        self.assertEqual("采用方案3", session["messages"][1]["text"])

    def test_parse_jetbrains_events_file(self) -> None:
        source_file = self.root / "jetbrains" / "sample.events"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        encoded_user = b64encode(
            '{"type":"com.intellij.ml.llm.chat.shared.ChatSessionUserPromptEvent","id":{"id":1},"prompt":"你好，帮我归档"}'.encode("utf-8")
        ).decode("utf-8")
        encoded_assistant = b64encode(
            '{"type":"com.intellij.ml.llm.chat.shared.ChatSessionMessageBlockEvent","id":{"id":2},"agentId":{"id":"codex"},"event":{"kind":"com.intellij.ml.llm.aui.events.api.MarkdownBlockUpdatedEvent","stepId":"1","text":"收到，我来归档"}}'.encode("utf-8")
        ).decode("utf-8")
        source_file.write_text(f"AUI_EVENTS_V1\n{encoded_user}\n{encoded_assistant}\n", encoding="utf-8")

        session = parse_jetbrains_events_file(source_file, "codex:jb-1")

        self.assertEqual("jb-1", session["session_id"])
        self.assertEqual("jetbrains-ai-codex", session["agent"])
        self.assertEqual("你好，帮我归档", session["messages"][0]["text"])
        self.assertEqual("收到，我来归档", session["messages"][1]["text"])
        self.assertTrue(session["started_at"].startswith("20"))

    def test_migrate_legacy_jetbrains_archives_renames_files_by_agent(self) -> None:
        archive_dir = self.root / ".dream"
        state_dir = archive_dir / ".state"
        source_root = self.root / "sources"
        source_file = source_root / "jetbrains-ai" / "sample.events"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(
            "AUI_EVENTS_V1\n"
            + b64encode(
                '{"type":"com.intellij.ml.llm.chat.shared.ChatSessionUserPromptEvent","id":{"id":1},"prompt":"你好，帮我归档","agentId":{"id":"codex"}}'.encode("utf-8")
            ).decode("utf-8")
            + "\n"
            + b64encode(
                '{"type":"com.intellij.ml.llm.chat.shared.ChatSessionMessageBlockEvent","id":{"id":2},"agentId":{"id":"codex"},"event":{"kind":"com.intellij.ml.llm.aui.events.api.MarkdownBlockUpdatedEvent","stepId":"1","text":"收到，我来归档"}}'.encode("utf-8")
            ).decode("utf-8")
            + "\n",
            encoding="utf-8",
        )
        source_file.with_suffix(".agentsession").write_text("codex:jb-1", encoding="utf-8")

        legacy_file = archive_dir / "2026-04-03-jetbrains-ai.md"
        archive_dir.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        legacy_file.write_text(
            "# 2026-04-03-jetbrains jetbrains-ai 对话归档\n\n"
            "## 当日摘要\n"
            "- 今日主题：你好，帮我归档\n"
            "- 关键结论：收到，我来归档\n"
            "- 待办事项：\n"
            "- 风险与未决问题：\n\n"
            "## 会话 01\n"
            "### 元信息\n"
            "- session_id：jb-1\n"
            "- 开始时间：2026-04-03T08:00:00Z\n"
            "- 结束时间：2026-04-03T08:01:00Z\n"
            "- 项目：\n"
            "- 标签：\n\n"
            "### 会话摘要\n"
            "- 主题：你好，帮我归档\n"
            "- 结论：收到，我来归档\n"
            "- 待办：\n"
            "- 风险：\n\n"
            "### 完整对话\n"
            "#### User\n"
            "你好，帮我归档\n"
            "#### Assistant\n"
            "收到，我来归档\n",
            encoding="utf-8",
        )

        migrate_legacy_jetbrains_archives(archive_dir, source_root)

        migrated_file = archive_dir / "2026-04-03-jetbrains-ai-codex.md"
        self.assertFalse(legacy_file.exists())
        self.assertTrue(migrated_file.exists())
        content = migrated_file.read_text(encoding="utf-8")
        self.assertIn("# 2026-04-03 jetbrains-ai-codex 对话归档", content)
        self.assertIn("- session_id：jb-1", content)

    def test_migrate_legacy_jetbrains_archives_merges_blank_session_ids_into_single_agent(self) -> None:
        archive_dir = self.root / ".dream"
        source_root = self.root / "sources"
        source_file = source_root / "jetbrains-ai" / "sample.events"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(
            "AUI_EVENTS_V1\n"
            + b64encode(
                '{"type":"com.intellij.ml.llm.chat.shared.ChatSessionUserPromptEvent","id":{"id":1},"prompt":"你好，帮我归档","agentId":{"id":"codex"}}'.encode("utf-8")
            ).decode("utf-8")
            + "\n",
            encoding="utf-8",
        )
        source_file.with_suffix(".agentsession").write_text("codex:jb-1", encoding="utf-8")

        legacy_file = archive_dir / "2026-04-03-jetbrains-ai.md"
        archive_dir.mkdir(parents=True, exist_ok=True)
        legacy_file.write_text(
            "# 2026-04-03-jetbrains jetbrains-ai 对话归档\n\n"
            "## 当日摘要\n"
            "- 今日主题：你好，帮我归档\n"
            "- 关键结论：收到，我来归档\n"
            "- 待办事项：\n"
            "- 风险与未决问题：\n\n"
            "## 会话 01\n"
            "### 元信息\n"
            "- session_id：jb-1\n"
            "- 开始时间：2026-04-03T08:00:00Z\n"
            "- 结束时间：2026-04-03T08:01:00Z\n"
            "- 项目：\n"
            "- 标签：\n\n"
            "### 会话摘要\n"
            "- 主题：你好，帮我归档\n"
            "- 结论：收到，我来归档\n"
            "- 待办：\n"
            "- 风险：\n\n"
            "### 完整对话\n"
            "#### User\n"
            "你好，帮我归档\n"
            "#### Assistant\n"
            "收到，我来归档\n\n"
            "## 会话 02\n"
            "### 元信息\n"
            "- session_id：\n"
            "- 开始时间：2026-04-03T09:00:00Z\n"
            "- 结束时间：2026-04-03T09:01:00Z\n"
            "- 项目：\n"
            "- 标签：\n\n"
            "### 会话摘要\n"
            "- 主题：继续追问\n"
            "- 结论：继续处理\n"
            "- 待办：\n"
            "- 风险：\n\n"
            "### 完整对话\n"
            "#### User\n"
            "继续追问\n"
            "#### Assistant\n"
            "继续处理\n",
            encoding="utf-8",
        )

        migrate_legacy_jetbrains_archives(archive_dir, source_root)

        migrated_file = archive_dir / "2026-04-03-jetbrains-ai-codex.md"
        self.assertFalse(legacy_file.exists())
        content = migrated_file.read_text(encoding="utf-8")
        self.assertIn("## 会话 01", content)
        self.assertIn("## 会话 02", content)
        self.assertIn("继续追问", content)

    def test_main_dream_harvest_processes_requested_sources(self) -> None:
        source_root = self.root / "sources"
        archive_root = self.root / ".dream"
        create_codex_sample(source_root / "codex" / "sample.jsonl")

        result = main_dream_harvest_args([
            "--archive-dir", str(archive_root),
            "--source-root", str(source_root),
            "--source", "codex",
        ])

        self.assertEqual(0, result)
        self.assertTrue((archive_root / "2026-04-03-codex.md").exists())

    def test_run_dream_harvest_skips_unchanged_file_on_second_run(self) -> None:
        source_root = self.root / "sources"
        archive_root = self.root / ".dream"
        create_codex_sample(source_root / "codex" / "sample.jsonl")

        first = run_dream_harvest(archive_root, ["codex"], source_root)
        second = run_dream_harvest(archive_root, ["codex"], source_root)

        self.assertEqual(1, first["processed"])
        self.assertEqual(0, second["processed"])


if __name__ == "__main__":
    unittest.main()
