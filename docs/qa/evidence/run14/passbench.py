#!/usr/bin/env python3
"""Measure the ledger read path two ways, same file, same process start.

  14x-pass : what `lore audit` does today (one full readlines()+parse per class)
  1x-pass  : the same result from a single pass (newest record per class_id)

Pure measurement: reads the ledger, parses it, prints nothing else.
"""

import json
import sys
import time

CLASSES = 14


def read_once(path):
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    newest: dict = {}
    for line in lines:
        s = line.strip()
        if not s:
            continue
        try:
            rec = json.loads(s)
        except ValueError:
            continue
        if isinstance(rec, dict) and "class_id" in rec:
            newest[rec["class_id"]] = rec  # last one wins, same as today
    return newest


def read_n_times(path, n):
    last = None
    for _ in range(n):
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        found = None
        for line in lines:
            s = line.strip()
            if not s:
                continue
            try:
                rec = json.loads(s)
            except ValueError:
                continue
            if isinstance(rec, dict) and rec.get("class_id") == "gateway-drain-window":
                found = rec
        last = found
    return last


if __name__ == "__main__":
    path = sys.argv[1]
    mode = sys.argv[2]
    t0 = time.perf_counter()
    if mode == "14x":
        read_n_times(path, CLASSES)
    else:
        read_once(path)
    print(f"{mode} {path} {(time.perf_counter() - t0) * 1000:.1f} ms")
