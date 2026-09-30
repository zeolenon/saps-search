from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from .auth import credentials_from_environment, prompt_credentials
from .batch import search_rows
from .client import SAPSClient, SAPSError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="saps-search",
        description="Consultas SAPS de clientes e edificações, somente leitura.",
    )
    parser.add_argument(
        "--env-credentials",
        action="store_true",
        help="Ler SAPS_USERNAME/SAPS_PASSWORD do ambiente (use apenas secret manager aprovado).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    client = subparsers.add_parser("client", help="Pesquisar cliente.")
    client_query = client.add_mutually_exclusive_group(required=True)
    client_query.add_argument("--cnpj")
    client_query.add_argument("--name")
    client_query.add_argument("--redesim")

    building = subparsers.add_parser("building", help="Pesquisar edificação.")
    building_query = building.add_mutually_exclusive_group(required=True)
    building_query.add_argument("--cnpj")
    building_query.add_argument("--name")
    building.add_argument("--client-id")
    building.add_argument("--classification")
    building.add_argument("--address")
    building.add_argument("--uf")
    building.add_argument("--city")
    building.add_argument("--neighborhood")

    batch = subparsers.add_parser("batch", help="Pesquisar lote de CSV.")
    batch.add_argument("csv_path", help="CSV com target, cnpj_cpf e name.")

    return parser


def _read_csv(path: str) -> list[dict[str, str]]:
    if path == "-":
        reader = csv.DictReader(sys.stdin)
        return [dict(row) for row in reader]
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _batch_needs_search(rows: list[dict[str, str]]) -> bool:
    valid_targets = {
        "client", "cliente", "clientes", "building", "edificacao", "edificacoes"
    }
    for row in rows:
        target = (row.get("target") or "").strip().casefold()
        document = row.get("cnpj_cpf") or row.get("cpf_cnpj") or ""
        name = (row.get("name") or row.get("nome") or "").strip()
        if target in valid_targets and (
            any(char.isdigit() for char in document) or bool(name)
        ):
            return True
    return False


def main() -> None:
    args = _parser().parse_args()
    try:
        batch_rows = _read_csv(args.csv_path) if args.command == "batch" else None
        if batch_rows is not None and not _batch_needs_search(batch_rows):
            _emit(search_rows(None, batch_rows))
            return

        if args.command == "client":
            if args.cnpj is not None and not any(char.isdigit() for char in args.cnpj):
                raise ValueError("CPF/CNPJ sem dígitos.")
            if args.name is not None and not args.name.strip():
                raise ValueError("Nome vazio.")
            if args.redesim is not None and not args.redesim.strip():
                raise ValueError("Protocolo REDESIM vazio.")
        if args.command == "building":
            if args.cnpj is not None and not any(char.isdigit() for char in args.cnpj):
                raise ValueError("CPF/CNPJ sem dígitos.")
            if args.name is not None and not args.name.strip():
                raise ValueError("Nome vazio.")

        credentials = (
            credentials_from_environment()
            if args.env_credentials
            else prompt_credentials()
        )
        with SAPSClient(credentials) as client:
            client.login()
            if args.command == "client":
                result = client.search_client(
                    cnpj=args.cnpj,
                    name=args.name,
                    redesim=args.redesim,
                )
            elif args.command == "building":
                result = client.search_building(
                    cnpj=args.cnpj,
                    name=args.name,
                    client_id=args.client_id,
                    classification=args.classification,
                    address=args.address,
                    uf=args.uf,
                    city=args.city,
                    neighborhood=args.neighborhood,
                )
            else:
                result = search_rows(client, batch_rows or [])
            _emit(result)
    except (ValueError, OSError, SAPSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
