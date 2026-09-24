import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bilibili_crawler


class JsonResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def make_crawler():
    crawler = bilibili_crawler.BiliModpackCrawler.__new__(bilibili_crawler.BiliModpackCrawler)
    crawler.stats = {"requests": 0, "successful": 0, "failed": 0, "errors": [], "pages_completed": 0}
    crawler.img_key = ""
    crawler.sub_key = ""
    crawler.headers = {}
    return crawler


class BilibiliLinkObservationTest(unittest.TestCase):
    def test_empty_pinned_comment_is_observed_only_after_successful_response(self):
        crawler = make_crawler()
        with patch.object(bilibili_crawler.urllib.request, "urlopen", return_value=JsonResponse({"code": 0, "data": {"top": {}}})):
            empty = crawler.get_pinned_comment(123)
        self.assertEqual(empty["message"], "")
        self.assertIs(empty["observed"], True)

        with patch.object(bilibili_crawler.urllib.request, "urlopen", side_effect=OSError("fixture network failure")):
            unavailable = crawler.get_pinned_comment(123)
        self.assertIs(unavailable["observed"], False)

    def test_no_subtitles_and_failed_subtitle_read_have_distinct_observation_states(self):
        crawler = make_crawler()
        empty_result = {"code": 0, "data": {"subtitle": {"subtitles": []}}}
        with patch.object(bilibili_crawler, "enc_wbi", side_effect=lambda params, *_args: params), patch.object(
            bilibili_crawler.urllib.request,
            "urlopen",
            side_effect=[JsonResponse(empty_result), JsonResponse(empty_result)],
        ):
            no_captions = crawler.get_video_subtitle(123, 456, "BV-test")
        self.assertIs(no_captions["has_subtitle"], False)
        self.assertIs(no_captions["observed"], True)

        with patch.object(bilibili_crawler, "enc_wbi", side_effect=lambda params, *_args: params), patch.object(
            bilibili_crawler.urllib.request, "urlopen", side_effect=OSError("fixture network failure")
        ):
            unavailable = crawler.get_video_subtitle(123, 456, "BV-test")
        self.assertIs(unavailable["observed"], False)

    def test_description_sync_recovers_source_state_before_accepting_link_changes(self):
        bvid = "BV-sync-observation"
        plans = [
            {
                "desc": "测试整合包发布 https://pan.baidu.com/s/abc123",
                "pinned": {"message": "", "time": "", "observed": False},
                "subtitle": {"has_subtitle": False, "subtitle_text": "", "subtitle_summary": "", "observed": False},
            },
            {
                "desc": "测试整合包发布，暂无下载地址",
                "pinned": {"message": "", "time": "", "observed": True},
                "subtitle": {"has_subtitle": False, "subtitle_text": "", "subtitle_summary": "", "observed": True},
            },
            {
                "desc": "测试整合包发布 https://pan.baidu.com/s/new222",
                "pinned": {"message": "", "time": "", "observed": True},
                "subtitle": {"has_subtitle": False, "subtitle_text": "", "subtitle_summary": "", "observed": True},
            },
        ]
        subtitle_reads = []
        extracted_subtitle_texts = []
        real_extractor = bilibili_crawler.BiliModpackCrawler.extract_modpack_info

        class PlannedCrawler:
            def __init__(self):
                self.plan = plans.pop(0)

            def get_video_detail(self, _bvid):
                return {
                    "aid": 123,
                    "cid": 456,
                    "title": "测试整合包发布",
                    "desc": self.plan["desc"],
                    "owner": {"name": "测试作者"},
                    "stat": {},
                    "pic": "",
                    "pubdate": 0,
                }

            def get_pinned_comment(self, _aid):
                return self.plan["pinned"]

            def get_video_subtitle(self, _aid, _cid, source_bvid):
                subtitle_reads.append(source_bvid)
                return self.plan["subtitle"]

            def extract_modpack_info(self, title, desc, pinned_comment, subtitle_text="", author="", duration=""):
                extracted_subtitle_texts.append(subtitle_text)
                return real_extractor(title, desc, pinned_comment, subtitle_text, author=author, duration=duration)

        with tempfile.TemporaryDirectory(prefix="bili-sync-observation-") as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "crawler_output"
            output_dir.mkdir()
            raw_path = output_dir / "bilibili_modpacks.json"
            sidecar_path = root / "converted_output" / "data" / "bili_data.js"
            raw_path.write_text(json.dumps([{
                "platform": "bilibili",
                "bvid": bvid,
                "title": "测试整合包发布",
                "author": "测试作者",
                "url": f"https://www.bilibili.com/video/{bvid}",
                "desc": "旧简介",
                "pinned_comment": "",
                "subtitle_text": "旧字幕（来源状态未知）",
                "download_links": [],
            }], ensure_ascii=False), encoding="utf-8")

            snapshots = []
            with patch.object(bilibili_crawler, "BiliModpackCrawler", PlannedCrawler), patch.dict(
                os.environ, {"MC_DESKTOP_WORKSPACE": str(root)}
            ):
                for _ in range(3):
                    bilibili_crawler.sync_descriptions(target_bv=bvid)
                    sidecar_payload = sidecar_path.read_text(encoding="utf-8").split("=", 1)[1].strip().removesuffix(";")
                    snapshots.append(json.loads(sidecar_payload)[0])

        failed = snapshots[0]
        self.assertIs(failed["desc_observed"], True)
        self.assertIs(failed["pinned_comment_observed"], False)
        self.assertIs(failed["subtitle_observed"], False)
        self.assertIs(failed["download_links_observed"], False)
        self.assertEqual(failed["subtitle_text"], "旧字幕（来源状态未知）")
        self.assertEqual(failed["download_links"], [])

        recovered = snapshots[1]
        self.assertIs(recovered["desc_observed"], True)
        self.assertIs(recovered["pinned_comment_observed"], True)
        self.assertIs(recovered["subtitle_observed"], True)
        self.assertIs(recovered["download_links_observed"], True)
        self.assertEqual(recovered["download_links"], [])

        changed = snapshots[2]
        self.assertIs(changed["download_links_observed"], True)
        self.assertEqual([item["url"] for item in changed["download_links"]], ["https://pan.baidu.com/s/new222"])
        self.assertEqual(subtitle_reads, [bvid, bvid])
        self.assertEqual(extracted_subtitle_texts, ["", "", ""])


if __name__ == "__main__":
    unittest.main()
