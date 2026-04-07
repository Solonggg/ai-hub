#!/usr/bin/env python3
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json_yaml(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_adapter(root: Path, tool: str) -> Dict:
    adapter_path = root / "adapters" / f"{tool}.yaml"
    if not adapter_path.exists():
        raise FileNotFoundError(f"adapter 不存在: {adapter_path}")
    return read_json_yaml(adapter_path)


def ignore_filter(_source: str, names: List[str]) -> List[str]:
    ignore_names = {".DS_Store", ".git", "__pycache__", ".pytest_cache"}
    return [name for name in names if name in ignore_names]


def copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        return
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignore_filter)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


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


def backup_existing(path: Path) -> Optional[Path]:
    if not path.exists() and not path.is_symlink():
        return None
    backup = path.with_name(f"{path.name}.bak.{timestamp()}")
    shutil.move(str(path), str(backup))
    return backup


def install_target(root: Path, tool: str, target_root: Path, copy_mode: bool = False) -> List[Dict]:
    target_root.mkdir(parents=True, exist_ok=True)
    operations = []
    for entry in install_entries(root, tool, target_root):
        source = entry["source"]
        target = entry["target"]
        if not source.exists():
            raise FileNotFoundError(f"安装源不存在: {source}")
        if target.is_symlink() and target.resolve() == source.resolve():
            operations.append({
                "target": str(target),
                "action": "skip",
            })
            continue

        backup = backup_existing(target)
        if backup is not None:
            operations.append({
                "target": str(target),
                "action": "backup",
                "backup": str(backup),
            })

        if copy_mode:
            if source.is_dir():
                copy_tree(source, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            action = "copy"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(source, target_is_directory=source.is_dir())
            action = "symlink"

        operations.append({
            "target": str(target),
            "source": str(source),
            "action": action,
        })
    return operations


def main_install() -> int:
    parser = argparse.ArgumentParser(description="把 dist 安装到目标工具目录")
    parser.add_argument("--root", default=default_root(), type=Path)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--copy", action="store_true", dest="copy_mode")
    args = parser.parse_args()

    operations = install_target(args.root, args.tool, args.target, args.copy_mode)
    print_json({"operations": operations})
    return 0
