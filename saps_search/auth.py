from __future__ import annotations

from dataclasses import dataclass, field
from getpass import getpass


@dataclass(frozen=True, repr=False)
class SAPSCredentials:
    username: str
    password: str = field(repr=False)

    def __repr__(self) -> str:
        return "SAPSCredentials(<redacted>)"


def prompt_credentials() -> SAPSCredentials:
    import sys

    if not sys.stdin.isatty():
        raise ValueError(
            "Login interativo exige terminal; em automação, use um secret manager "
            "aprovado com --env-credentials."
        )
    username = input("Matrícula SAPS: ").strip()
    password = getpass("Senha SAPS (entrada oculta): ")
    if not username or not password:
        raise ValueError("Matrícula e senha são obrigatórias.")
    return SAPSCredentials(username=username, password=password)


def credentials_from_environment() -> SAPSCredentials:
    import os

    username = os.environ.get("SAPS_USERNAME", "")
    password = os.environ.get("SAPS_PASSWORD", "")
    if not username or not password:
        raise ValueError(
            "Defina SAPS_USERNAME e SAPS_PASSWORD via secret manager; "
            "nenhum valor foi exibido."
        )
    return SAPSCredentials(username=username, password=password)
