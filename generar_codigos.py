from __future__ import annotations

import csv
import secrets
import string
from pathlib import Path

from jubilacion.access_control import hash_code


PROJECT_DIR = Path(__file__).resolve().parent
PRIVATE_CODES = PROJECT_DIR / "private" / "codigos_acceso_100.csv"
HASHES = PROJECT_DIR / "data" / "access_code_hashes.csv"
ALPHABET = string.ascii_uppercase + string.digits


def generate_codes(total: int = 100) -> list[str]:
    codes: set[str] = set()
    while len(codes) < total:
        codes.add("".join(secrets.choice(ALPHABET) for _ in range(8)))
    return sorted(codes)


def main() -> None:
    codes = generate_codes()
    PRIVATE_CODES.parent.mkdir(exist_ok=True)
    HASHES.parent.mkdir(exist_ok=True)

    with PRIVATE_CODES.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["codigo", "estado", "trabajador_asignado", "informes_usados", "observacion"],
        )
        writer.writeheader()
        for code in codes:
            writer.writerow(
                {
                    "codigo": code,
                    "estado": "disponible",
                    "trabajador_asignado": "",
                    "informes_usados": 0,
                    "observacion": "Entregar un codigo por trabajador. Cada codigo permite hasta 10 informes.",
                }
            )

    with HASHES.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["code_hash", "max_reports"])
        writer.writeheader()
        for code in codes:
            writer.writerow({"code_hash": hash_code(code), "max_reports": 10})

    print(f"Codigos para entregar: {PRIVATE_CODES}")
    print(f"Hashes para la app: {HASHES}")


if __name__ == "__main__":
    main()
