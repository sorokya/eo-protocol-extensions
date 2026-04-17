"""Known eolib implementations and their repository URLs."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EolibTarget:
    language: str
    repo_url: str
    default_branch: str = "main"
    description: str = ""


KNOWN_LANGUAGES: dict[str, EolibTarget] = {
    "c": EolibTarget(
        language="c",
        repo_url="https://github.com/sorokya/eolib-c",
        description="C implementation (eolib-c)",
    ),
    "dotnet": EolibTarget(
        language="dotnet",
        repo_url="https://github.com/ethanmoffat/eolib-dotnet",
        description=".NET implementation (eolib-dotnet)",
    ),
    "go": EolibTarget(
        language="go",
        repo_url="https://github.com/ethanmoffat/eolib-go",
        description="Go implementation (eolib-go)",
    ),
    "java": EolibTarget(
        language="java",
        repo_url="https://github.com/Cirras/eolib-java",
        description="Java implementation (eolib-java)",
    ),
    "pas": EolibTarget(
        language="pas",
        repo_url="https://github.com/cirras/eolib-pas",
        description="Pascal implementation (eolib-pas)",
    ),
    "php": EolibTarget(
        language="php",
        repo_url="https://github.com/Cirras/eolib-php",
        description="PHP implementation (eolib-php)",
    ),
    "python": EolibTarget(
        language="python",
        repo_url="https://github.com/Cirras/eolib-python",
        description="Python implementation (eolib-python)",
    ),
    "rs": EolibTarget(
        language="rs",
        repo_url="https://github.com/sorokya/eolib-rs",
        description="Rust implementation (eolib-rs)",
    ),
    "ts": EolibTarget(
        language="ts",
        repo_url="https://github.com/Cirras/eolib-ts",
        description="TypeScript implementation (eolib-ts)",
    ),
}


def get_target(language: str) -> EolibTarget:
    key = language.lower()
    if key not in KNOWN_LANGUAGES:
        supported = "\n  ".join(
            f"{k:<10} {v.description}" for k, v in KNOWN_LANGUAGES.items()
        )
        raise ValueError(
            f"Unsupported language '{language}'.\n\n"
            f"Supported languages:\n  {supported}"
        )
    return KNOWN_LANGUAGES[key]
