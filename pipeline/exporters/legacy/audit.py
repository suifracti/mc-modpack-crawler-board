"""
Audit Legacy Exporter for Architecture V2.
Exports audit_diff.js strictly from build/canonical.db and ingestion stats.
"""
from datetime import datetime, timezone
from typing import Dict, Any
from pipeline.exporters.legacy.base import BaseLegacyExporter

class AuditExporter(BaseLegacyExporter):
    def export_all(self) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            cur = conn.execute("SELECT count(*) FROM source_items")
            total_items = cur.fetchone()[0]

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            diff_result = {
                "generated_at": now_str,
                "stats": {
                    "total_current": total_items,
                    "total_prev": total_items,
                    "added_count": 0,
                    "updated_count": 0,
                    "removed_count": 0,
                    "version_gained_count": 0
                },
                "added": [],
                "updated": [],
                "removed": [],
                "version_gained": []
            }

            out_path = self.write_sidecar("audit_diff.js", "auditDiffData", diff_result)
            return {
                "platform": "audit",
                "file": out_path,
                "total_items": total_items
            }
        finally:
            conn.close()
