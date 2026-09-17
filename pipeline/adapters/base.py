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
from pipeline.models.canonical import CanonicalPackBundle, CanonicalEnvironmentClaim

# Common regular expressions for Phase 1.1 semantic classification
SERVER_FILE_REGEX = re.compile(
    r'(?:服务端|服务器端|开服包|server\s*pack|serverpack|server-pack|dedicated\s*server\s*files?)',
    re.I,
)

# Negative declarations: explicitly unsupported / client only
SERVER_TEXT_NEG_REGEX = re.compile(
    r'(?:仅(?:限)?客户端|纯客户端|不支持服务端|(?:不提供|未提供|不包含|未包含|暂无|没有|无)服务端|'
    r'不能(?:用于)?开服|不可用于服务端|禁止开服|无法开服|单人限定|'
    r'client\s*only|no\s*server\s*(?:pack|support)|server\s*(?:not\s*supported|unsupported)|singleplayer\s*only)',
    re.I,
)

# Positive declarations: explicitly supported
SERVER_TEXT_POS_REGEX = re.compile(
    r'(?<!不)(?<!未)(?<!无)(?<!没有)(?<!暂无)(?:(?:已)?提供服务端|包含服务端|支持开服|提供开服端|包含开服包|官方开服端|服务端下载|附带服务端|'
    r'server\s*pack\s*(?:is|included|available|download)|official\s*server\s*pack|server\s*files\s*(?:included|available))',
    re.I,
)


class BaseAdapter(abc.ABC):
    platform_name: str = ""
    SERVER_FILE_REGEX = SERVER_FILE_REGEX
    SERVER_TEXT_NEG_REGEX = SERVER_TEXT_NEG_REGEX
    SERVER_TEXT_POS_REGEX = SERVER_TEXT_POS_REGEX

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
        s = re.sub(r'^[\[【\(（][^】\]\)）]+[】\]\)）]\s*', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip() or title.strip().lower()

    @staticmethod
    def extract_snippet(text: str, match: re.Match, window: int = 30) -> str:
        if not text or not match:
            return ""
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        snippet = text[start:end].replace('\n', ' ').strip()
        return snippet

    @staticmethod
    def create_unknown_claim(
        pack_id: str,
        source_item_id: str,
        side: str,
        evidence_text: str,
        url: str,
        observed_at: str,
    ) -> CanonicalEnvironmentClaim:
        return CanonicalEnvironmentClaim(
            pack_id=pack_id,
            source_item_id=source_item_id,
            side=side,
            status="unknown",
            certainty="unknown",
            evidence_type="platform_field",
            evidence_text=evidence_text,
            raw_value=None,
            source_field=None,
            source_url=url,
            observed_at=observed_at,
        )
