import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for module_dir in (
    ROOT / "bin" / "doctor",
    ROOT / "bin" / "install-target",
    ROOT / "bin" / "publish-skills",
):
    sys.path.insert(0, str(module_dir))

from doctor import doctor
from install_target import install_target
from publish_skills import main_publish, sync_tool


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_sample_root(base: Path) -> None:
    write_text(base / "skills" / "superpowers" / "using-superpowers" / "SKILL.md", "# using-superpowers\n")
    write_text(base / "skills" / "superpowers" / "using-superpowers" / ".DS_Store", "ignored")
    write_text(base / "skills" / "iho-java" / "SKILL.md", "# iho-java\n")
    write_text(base / "skills" / "iho-java" / "agents" / "openai.yaml", "name: openai\n")
    write_text(base / "agents" / "global-agent.yaml", "name: reviewer\n")
    write_text(base / "adapters" / "bootstrap" / "AGENTS.md", "默认使用 `$wangjie-defaults` skill。\n")
    write_json_yaml(base / "registry.yaml", {
        "version": 1,
        "defaults": {
            "owner": "wangjie",
            "root": str(base),
        },
        "skills": [
            {
                "id": "using-superpowers",
                "path": "skills/superpowers/using-superpowers",
                "source": "codex-superpowers",
                "enabled": ["codex"],
            },
            {
                "id": "iho-java",
                "path": "skills/iho-java",
                "source": "local",
                "enabled": ["codex"],
            },
        ],
        "agents": [],
    })
    write_json_yaml(base / "adapters" / "codex.yaml", {
        "tool": "codex",
        "output_dir": "dist/codex",
        "skill_dir_name": "skills",
        "agent_dir_name": "agents",
        "bootstrap_file": "AGENTS.md",
        "bootstrap_source": "adapters/bootstrap/AGENTS.md",
        "preserve_skill_agents": True,
        "flatten_global_agents": False,
    })


class SkillsHubTest(unittest.TestCase):

    def test_no_legacy_shared_layer_remains(self) -> None:
        self.assertFalse((ROOT / "bin" / "skills_hub_lib.py").exists())
        self.assertFalse((ROOT / "bin" / "common").exists())

    def test_command_modules_are_split_by_command_directory(self) -> None:
        command_layout = {
            "doctor": ["doctor", "doctor.py"],
            "dream-harvest": ["dream-harvest", "dream_harvest.py"],
            "install-target": ["install-target", "install_target.py"],
            "publish-skills": ["publish-skills", "publish_skills.py"],
        }

        for directory, expected_files in command_layout.items():
            command_dir = ROOT / "bin" / directory
            self.assertTrue(command_dir.is_dir(), f"缺少命令目录: {command_dir}")
            for expected_file in expected_files:
                self.assertTrue(
                    (command_dir / expected_file).exists(),
                    f"缺少命令文件: {command_dir / expected_file}",
                )

    def test_sync_tool_generates_dist_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_sample_root(root)

            sync_tool(root, "codex")

            dist_root = root / "dist" / "codex"
            self.assertTrue((dist_root / "skills" / "superpowers" / "using-superpowers" / "SKILL.md").exists())
            self.assertFalse((dist_root / "skills" / "superpowers" / "using-superpowers" / ".DS_Store").exists())
            self.assertTrue((dist_root / "skills" / "iho-java" / "agents" / "openai.yaml").exists())
            self.assertTrue((dist_root / "agents" / "global-agent.yaml").exists())
            index = json.loads((dist_root / "index.json").read_text(encoding="utf-8"))
            self.assertEqual("codex", index["tool"])
            self.assertEqual(
                ["using-superpowers", "iho-java"],
                [item["id"] for item in index["skills"]],
            )

    def test_doctor_reports_duplicate_and_missing_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_sample_root(root)
            write_json_yaml(root / "registry.yaml", {
                "version": 1,
                "defaults": {
                    "owner": "wangjie",
                    "root": str(root),
                },
                "skills": [
                    {
                        "id": "dup-skill",
                        "path": "skills/not-exists",
                        "source": "local",
                        "enabled": ["codex"],
                    },
                    {
                        "id": "dup-skill",
                        "path": "skills/iho-java",
                        "source": "local",
                        "enabled": ["codex"],
                    },
                ],
                "agents": [],
            })

            issues = doctor(root)

            self.assertTrue(any("重复" in issue for issue in issues))
            self.assertTrue(any("skills/not-exists" in issue for issue in issues))

    def test_install_target_links_dist_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_sample_root(root)
            sync_tool(root, "codex")
            target = root / "target-home"

            install_target(root, "codex", target)

            self.assertTrue((target / "skills").is_symlink())
            self.assertEqual(
                str((root / "dist" / "codex" / "skills").resolve()),
                str((target / "skills").resolve()),
            )
            self.assertTrue((target / "AGENTS.md").is_symlink())

    def test_main_dispatches_publish_skills_script(self) -> None:
        with patch.object(sys, "argv", ["publish-skills"]), \
             patch("publish_skills.sync_tools", return_value=[] ) as sync_tools_mock, \
             patch("publish_skills.print_json") as print_json_mock:
            self.assertEqual(0, main_publish())
            sync_tools_mock.assert_called_once()
            print_json_mock.assert_called_once_with({"results": []})


if __name__ == "__main__":
    unittest.main()
