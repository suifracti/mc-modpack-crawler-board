"""
Base Legacy Exporter for Architecture V2.
Provides connection management and JS sidecar formatting.
STRICT RULE: Exporters read ONLY from build/canonical.db.
"""
import os
import json
import sqlite3
from typing import Any, Optional, Dict

class BaseLegacyExporter:
    def __init__(self, db_path: str, output_data_dir: str):
        self.db_path = db_path
        self.output_data_dir = output_data_dir
        os.makedirs(self.output_data_dir, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def write_sidecar(self, filename: str, global_var: str, data: Any) -> str:
        target_path = os.path.join(self.output_data_dir, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        payload = f"window.{global_var} = " + json.dumps(data, ensure_ascii=False) + ";\n"
        with open(target_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
        return target_path

    def write_register_script(self, sub_dir: str, filename: str, register_fn: str, arg1: Any, arg2: Any) -> str:
        target_dir = os.path.join(self.output_data_dir, sub_dir)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, filename)
        body = f"window.{register_fn}(" + json.dumps(arg1, ensure_ascii=False) + "," + json.dumps(arg2, ensure_ascii=False, separators=(",", ":")) + ");\n"
        with open(target_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        return target_path

    @staticmethod
    def derive_legacy_has_server(status: Optional[str], certainty: Optional[str]) -> bool:
        """
        Legacy UI compatibility only.
        Do not use as canonical server-support truth.
        """
        if not status or not certainty:
            return False
        if status in ("supported", "required", "optional") and certainty in ("confirmed", "inferred", "strong_inferred"):
            return True
        return False
