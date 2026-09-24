import json
import unittest
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


if __name__ == "__main__":
    unittest.main()
