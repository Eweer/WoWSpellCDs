import argparse
import csv
import json
from pathlib import Path
import re

import sys
from typing import Final
import urllib.request


WAGO_TOOLS_URL: Final[str] = "https://wago.tools/db2/SpellCooldowns/csv"


def normalize(name: str):
    return re.sub("[^a-z0-9]", "", name.lower())


def send_request(url: str = WAGO_TOOLS_URL, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw_data = response.read()
    return raw_data.decode("utf-8-sig", errors="replace")


def to_camel_case(s: str) -> str:
    post = re.sub("[^a-zA-Z]", "", s)
    return s[0].lower() + post[1:]


def fetch_data(is_debug: bool = False):
    if not is_debug:
        return send_request()

    if not Path('./raw_data.csv').resolve().exists():
        with open('raw_data.csv', 'w', encoding="utf-8") as f:
            data = send_request()
            f.write(data)
    with open('raw_data.csv', 'r', encoding="utf-8") as f:
        return f.read()


def to_json(response: str, is_debug: bool = False):
    reader = csv.DictReader(response.splitlines())

    csv_headers = (reader.fieldnames or [])[:-1]
    dict_keys = [to_camel_case(k) if k != "ID" else "id" for k in reader.fieldnames or []][:-1]

    result: dict[int, dict[str, int]] = {}
    for row in reader:
        if int(row['RecoveryTime']) != 0:
            spellId = int(row['SpellID'])
            result[spellId] = {}
            for header, key in zip(csv_headers, dict_keys):
                if int(row[header]) != 0:
                    result[spellId].update({key: int(row[header])})

    if is_debug:
        print(f"Available columns: {csv_headers}", file=sys.stderr)
        with open('output.json', 'w', encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=True, indent=4)

    with open('spell_cds.json', 'w', encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))


def to_csv(response: str):
    result: list[str] = []
    for row in response.splitlines():
        result.append(f"{re.sub(",0", ",", row)}\n")
    with open('spell_cds.csv', 'w', encoding="utf-8") as f:
        f.writelines(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action='store_true')
    parser.add_argument("--csv", action='store_true')
    parser.add_argument("--debug", action='store_true')
    args = parser.parse_args()
    data = fetch_data(args.debug)
    if args.json:
        to_json(data, args.debug)
    if args.csv:
        to_csv(data)
