"""
Base Adapter class for Architecture V2 pipeline.
All platform adapters inherit from this class and implement load_and_adapt().
"""
import abc
import hashlib
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple, Iterator
from pipeline.models.canonical import CanonicalPackBundle

class BaseAdapter(abc.ABC):
    platform_name: str = ""

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    @abc.abstractmethod
    def get_source_file_path(self) -> str:
        """Return the path to the primary raw JSON file in crawler_output/."""
        pass

    @abc.abstractmethod
    def adapt_item(self, raw_item: Dict[str, Any], idx: int) -> CanonicalPackBundle:
        """Transform a raw JSON item into a CanonicalPackBundle."""
        pass

    def get_snapshot_provenance(self) -> Tuple[str, int, str, int]:
        """Returns (file_path, file_size_bytes, content_hash, record_count)."""
        fp = self.get_source_file_path()
        if not os.path.exists(fp):
            raise FileNotFoundError(f"Source file not found: {fp}")
        size = os.path.getsize(fp)
        h = hashlib.sha256()
        with open(fp, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        content_hash = h.hexdigest()
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
            rec_count = len(data) if isinstance(data, list) else len(data.keys())
        return fp, size, content_hash, rec_count

    def load_raw_items(self) -> List[Dict[str, Any]]:
        fp = self.get_source_file_path()
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_and_adapt(self) -> Iterator[CanonicalPackBundle]:
        raw_items = self.load_raw_items()
        for idx, item in enumerate(raw_items):
            yield self.adapt_item(item, idx)

    @staticmethod
    def normalize_title(title: str) -> str:
        """Strip redundant whitespace, brackets, marketing buzzwords for fuzzy normalization."""
        if not title:
            return ""
        s = title.strip().lower()
        # Remove typical bracket wrappers for sorting/matching
        s = re.sub(r'^[\[【\(（][^】\]\)）]+[】\]\)）]\s*', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip() or title.strip().lower()
