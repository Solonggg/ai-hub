#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


REQUIRED_ADAPTER_KEYS = {
    "tool",
    "output_dir",
    "skill_dir_name",
    "agent_dir_name",
    "bootstrap_file",
    "preserve_skill_agents",
    "flatten_global_agents",
}


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json_yaml(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(root: Path) -> Dict:
    return read_json_yaml(root / "registry.yaml")


def list_adapter_files(root: Path) -> List[Path]:
    adapters_dir = root / "adapters"
    if not adapters_dir.exists():
        return []
    return sorted(path for path in adapters_dir.glob("*.yaml") if path.is_file())


def enabled_skills(registry: Dict, tool: str) -> List[Dict]:
    return [skill for skill in registry.get("skills", []) if tool in skill.get("enabled", [])]


def relative_skill_path(skill: Dict) -> Path:
    path = Path(skill["path"])
    if not path.parts or path.parts[0] != "skills":
        raise ValueError(f"skill path 必须以 skills/ 开头: {skill['path']}")
    return Path(*path.parts[1:])


def load_adapter(root: Path, tool: str) -> Dict:
    adapter_path = root / "adapters" / f"{tool}.yaml"
    if not adapter_path.exists():
        raise FileNotFoundError(f"adapter 不存在: {adapter_path}")
    return read_json_yaml(adapter_path)


def print_json(payload: Dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def install_entries(root: Path, tool: str, target_root: Path) -> List[Dict]:
    adapter = load_adapter(root, tool)
    output_dir = root / adapter["output_dir"]
    entries = [
        {
            "source": output_dir / adapter["skill_dir_name"],
            "target": target_root / adapter["skill_dir_name"],
        },
        {
            "source": output_dir / adapter["bootstrap_file"],
            "target": target_root / adapter["bootstrap_file"],
        },
    ]
    agent_source = output_dir / adapter["agent_dir_name"]
    if agent_source.exists():
        entries.append({
            "source": agent_source,
            "target": target_root / adapter["agent_dir_name"],
        })
    return entries


def doctor(root: Path, tool: Optional[str] = None, target_root: Optional[Path] = None) -> List[str]:
    issues: List[str] = []
    registry_path = root / "registry.yaml"
    if not registry_path.exists():
        return [f"缺少 registry.yaml: {registry_path}"]

    try:
        registry = load_registry(root)
    except json.JSONDecodeError as exc:
        return [f"registry.yaml 解析失败: {exc}"]

    seen_ids = set()
    for skill in registry.get("skills", []):
        skill_id = skill.get("id")
        if skill_id in seen_ids:
            issues.append(f"重复 skill id: {skill_id}")
        else:
            seen_ids.add(skill_id)

        path = skill.get("path")
        if not path:
            issues.append(f"skill 缺少 path: {skill}")
            continue
        skill_root = root / path
        if not skill_root.exists():
            issues.append(f"skill 路径不存在: {path}")
            continue
        if not (skill_root / "SKILL.md").exists():
            issues.append(f"缺少 SKILL.md: {path}")

    adapter_files = [root / "adapters" / f"{tool}.yaml"] if tool else list_adapter_files(root)
    if not adapter_files:
        issues.append(f"未找到 adapter: {tool or 'adapters/*.yaml'}")
        return issues

    for adapter_path in adapter_files:
        if not adapter_path.exists():
            issues.append(f"缺少 adapter 文件: {adapter_path}")
            continue
        try:
            adapter = read_json_yaml(adapter_path)
        except json.JSONDecodeError as exc:
            issues.append(f"adapter 解析失败 {adapter_path.name}: {exc}")
            continue

        missing_keys = sorted(REQUIRED_ADAPTER_KEYS - set(adapter.keys()))
        if missing_keys:
            issues.append(f"adapter 缺少字段 {adapter_path.name}: {', '.join(missing_keys)}")
            continue

        bootstrap_source = adapter.get("bootstrap_source")
        if bootstrap_source and not (root / bootstrap_source).exists():
            issues.append(f"bootstrap_source 不存在: {bootstrap_source}")

        output_dir = root / adapter["output_dir"]
        skill_output_root = output_dir / adapter["skill_dir_name"]
        if not output_dir.exists():
            issues.append(f"缺少产物目录: {output_dir}")
        else:
            if not (output_dir / "index.json").exists():
                issues.append(f"缺少索引文件: {output_dir / 'index.json'}")
            for skill in enabled_skills(registry, adapter["tool"]):
                expected = skill_output_root / relative_skill_path(skill)
                if not expected.exists():
                    issues.append(f"dist 缺少 skill 产物: {expected}")

        if target_root is not None:
            for entry in install_entries(root, adapter["tool"], target_root):
                target = entry["target"]
                if not target.exists() and not target.is_symlink():
                    issues.append(f"未安装目标: {target}")
                    continue
                if target.is_symlink():
                    real_path = Path(os.path.realpath(target))
                    if not real_path.exists():
                        issues.append(f"软链接失效: {target}")
    return issues


def main_doctor() -> int:
    parser = argparse.ArgumentParser(description="诊断 registry、adapter、dist 与安装状态")
    parser.add_argument("--root", default=default_root(), type=Path)
    parser.add_argument("--tool")
    parser.add_argument("--target", type=Path)
    args = parser.parse_args()

    issues = doctor(args.root, args.tool, args.target)
    if issues:
        print_json({"ok": False, "issues": issues})
        return 1
    print_json({"ok": True, "issues": []})
    return 0
