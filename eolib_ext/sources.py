from __future__ import annotations

"""
Resolves Extension objects to local directories.

Git extensions are cached in ~/.cache/eolib-ext/<repo-slug>/ and updated on each run.
File extensions are validated to exist on disk.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

import git

from .models import Extension, ResolvedExtension

OFFICIAL_REPO = "https://github.com/sorokya/eo-protocol-extensions"
BASE_PROTOCOL_REPO = "https://github.com/Cirras/eo-protocol"
CACHE_DIR = Path.home() / ".cache" / "eolib-ext"


def _cache_path(repo_url: str) -> Path:
    slug = hashlib.sha1(repo_url.encode()).hexdigest()[:12]
    safe = repo_url.replace("https://", "").replace("/", "_").replace(".", "-")[:40]
    return CACHE_DIR / f"{safe}-{slug}"


def resolve(extension: Extension, config_dir: Path) -> ResolvedExtension:
    """
    Resolve an Extension to a local path, fetching/cloning as needed.
    config_dir is the directory containing extensions.xml (for relative file paths).
    """
    if extension.type == "git":
        return _resolve_git(extension)
    elif extension.type == "file":
        return _resolve_file(extension, config_dir)
    else:
        raise ValueError(f"Unknown extension type '{extension.type}' for '{extension.name}'")


def _resolve_git(extension: Extension) -> ResolvedExtension:
    repo_url = extension.repo or OFFICIAL_REPO
    cache = _cache_path(repo_url)

    if cache.exists():
        repo = git.Repo(cache)
        repo.remotes.origin.fetch()
    else:
        cache.parent.mkdir(parents=True, exist_ok=True)
        repo = git.Repo.clone_from(repo_url, cache)

    if extension.ref:
        repo.git.checkout(extension.ref)
    else:
        default_branch = repo.remotes.origin.refs[0].remote_head
        repo.git.checkout(default_branch)
        repo.remotes.origin.pull()

    ext_path = cache / "extensions" / extension.name
    if not ext_path.exists():
        available = sorted(
            p.name for p in (cache / "extensions").iterdir() if p.is_dir()
        ) if (cache / "extensions").exists() else []
        avail_str = "\n    ".join(available) if available else "(none)"
        raise ValueError(
            f"Extension '{extension.name}' not found in {repo_url}.\n"
            f"  Available extensions:\n    {avail_str}"
        )

    return ResolvedExtension(name=extension.name, local_path=str(ext_path))


def _resolve_file(extension: Extension, config_dir: Path) -> ResolvedExtension:
    if not extension.path:
        raise ValueError(f"File extension '{extension.name}' has no 'path' attribute.")

    raw = Path(extension.path)
    ext_path = raw if raw.is_absolute() else (config_dir / raw).resolve()

    if not ext_path.exists():
        raise ValueError(
            f"File extension '{extension.name}': path does not exist: {ext_path}"
        )
    if not ext_path.is_dir():
        raise ValueError(
            f"File extension '{extension.name}': path is not a directory: {ext_path}"
        )

    return ResolvedExtension(name=extension.name, local_path=str(ext_path))


def fetch_base_protocol() -> list[Path]:
    """
    Clone or update the base eo-protocol repo and return its protocol.xml files.
    Cached at ~/.cache/eolib-ext/ like extension repos.
    """
    cache = _cache_path(BASE_PROTOCOL_REPO)
    if cache.exists():
        repo = git.Repo(cache)
        repo.remotes.origin.fetch()
        default_branch = repo.remotes.origin.refs[0].remote_head
        repo.git.checkout(default_branch)
        repo.remotes.origin.pull()
    else:
        cache.parent.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(BASE_PROTOCOL_REPO, cache)

    xml_dir = cache / "xml"
    return sorted(xml_dir.rglob("protocol.xml"))


def resolve_extension_files(resolved: ResolvedExtension) -> list[Path]:
    """
    Return all protocol.xml files inside the extension directory, in a stable order
    matching the eo-protocol xml/ hierarchy (root first, then subdirectories).
    """
    root = Path(resolved.local_path)
    files: list[Path] = []

    root_proto = root / "protocol.xml"
    if root_proto.exists():
        files.append(root_proto)

    for proto in sorted(root.rglob("protocol.xml")):
        if proto != root_proto:
            files.append(proto)

    return files
