"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys

from .selftest import run as run_selftest
from .vault import decrypt_file, encrypt_file, list_entries


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest()

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_enc = sub.add_parser("encrypt")
    p_enc.add_argument("path")
    p_enc.add_argument("--password", required=True)
    p_enc.add_argument("--vault", default=".vault")

    p_dec = sub.add_parser("decrypt")
    p_dec.add_argument("entry_id")
    p_dec.add_argument("--password", required=True)
    p_dec.add_argument("--out", default=None)
    p_dec.add_argument("--vault", default=".vault")

    p_list = sub.add_parser("list")
    p_list.add_argument("--vault", default=".vault")

    args = parser.parse_args()

    if args.command == "encrypt":
        entry_id = encrypt_file(args.vault, args.path, args.password)
        print(f"encrypted: {entry_id}")
    elif args.command == "decrypt":
        destination = decrypt_file(args.vault, args.entry_id, args.password, args.out)
        print(f"decrypted: {destination}")
    elif args.command == "list":
        print(json.dumps(list_entries(args.vault)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
