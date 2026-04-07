#!/usr/bin/env python3
import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional


IGNORE_NAMES = {".DS_Store", ".git", "__pycache__", ".pytest_cache"}


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json_yaml(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_yaml(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_registry(root: Path) -> Dict:
    return read_json_yaml(root / "registry.yaml")


def list_adapter_files(root: Path) -> List[Path]:
    adapters_dir = root / "adapters"
    if not adapters_dir.exists():
        return []
    return sorted(path for path in adapters_dir.glob("*.yaml") if path.is_file())


def load_adapter(root: Path, tool: str) -> Dict:
    adapter_path = root / "adapters" / f"{tool}.yaml"
    if not adapter_path.exists():
        raise FileNotFoundError(f"adapter 不存在: {adapter_path}")
    return read_json_yaml(adapter_path)


def enabled_skills(registry: Dict, tool: str) -> List[Dict]:
    return [skill for skill in registry.get("skills", []) if tool in skill.get("enabled", [])]


def relative_skill_path(skill: Dict) -> Path:
    path = Path(skill["path"])
    if not path.parts or path.parts[0] != "skills":
        raise ValueError(f"skill path 必须以 skills/ 开头: {skill['path']}")
    return Path(*path.parts[1:])


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.exists():
        shutil.rmtree(path)


def ignore_filter(_source: str, names: List[str]) -> List[str]:
    return [name for name in names if name in IGNORE_NAMES]


def copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        return
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignore_filter)


def print_json(payload: Dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_index(tool: str, adapter: Dict, skills: List[Dict]) -> Dict:
    return {
        "tool": tool,
        "output_dir": adapter["output_dir"],
        "skills": [
            {
                "id": skill["id"],
                "path": str(Path(adapter["skill_dir_name"]) / relative_skill_path(skill)),
                "source": skill["source"],
            }
            for skill in skills
        ],
        "agents": [],
    }


def load_bootstrap_content(root: Path, adapter: Dict) -> str:
    bootstrap_source = adapter.get("bootstrap_source")
    if bootstrap_source:
        return (root / bootstrap_source).read_text(encoding="utf-8")
    return ""


def sync_tool(root: Path, tool: str) -> Dict:
    registry = load_registry(root)
    adapter = load_adapter(root, tool)
    output_dir = root / adapter["output_dir"]
    remove_path(output_dir)
    (output_dir / adapter["skill_dir_name"]).mkdir(parents=True, exist_ok=True)

    skills = enabled_skills(registry, tool)
    for skill in skills:
        source = root / skill["path"]
        target = output_dir / adapter["skill_dir_name"] / relative_skill_path(skill)
        copy_tree(source, target)

    global_agents = root / "agents"
    if global_agents.exists() and any(global_agents.iterdir()):
        target_agents = output_dir / adapter["agent_dir_name"]
        if adapter.get("flatten_global_agents"):
            target_agents.mkdir(parents=True, exist_ok=True)
            for child in sorted(global_agents.rglob("*")):
                if child.is_dir() or child.name in IGNORE_NAMES:
                    continue
                write_text(target_agents / child.name, child.read_text(encoding="utf-8"))
        else:
            copy_tree(global_agents, target_agents)

    bootstrap_file = output_dir / adapter["bootstrap_file"]
    write_text(bootstrap_file, load_bootstrap_content(root, adapter))
    write_json_yaml(output_dir / "index.json", build_index(tool, adapter, skills))
    return {
        "tool": tool,
        "output_dir": str(output_dir),
        "skill_count": len(skills),
    }


def sync_tools(root: Path, tools: Optional[Iterable[str]] = None) -> List[Dict]:
    selected_tools = list(tools) if tools else [path.stem for path in list_adapter_files(root)]
    return [sync_tool(root, tool) for tool in selected_tools]


def main_publish() -> int:
    parser = argparse.ArgumentParser(description="发布 skills 真源到 dist 目录")
    parser.add_argument("--root", default=default_root(), type=Path)
    parser.add_argument("--tool", action="append", dest="tools")
    args = parser.parse_args()

    results = sync_tools(args.root, args.tools)
    print_json({"results": results})
    return 0
