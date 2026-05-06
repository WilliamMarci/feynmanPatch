# feynmanPatch/utils.py

import datetime
import json
import os
import re


def safe_process_name(text):
    if not text:
        return "unknown_process"
    text = text.strip()
    text = text.replace(">", "_to_")
    text = text.replace(" ", "_")
    text = re.sub(r"[^A-Za-z0-9_\-\.]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_") or "process"


def now_tag():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def write_text(path, content):
    parent = os.path.dirname(path)
    if parent:
        ensure_dir(parent)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_json(path, data):
    parent = os.path.dirname(path)
    if parent:
        ensure_dir(parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=False)


def normalize_xy(x, y, width, height, margin=30):
    px = margin + x * max(1, width - 2 * margin)
    py = margin + (1.0 - y) * max(1, height - 2 * margin)
    return px, py
