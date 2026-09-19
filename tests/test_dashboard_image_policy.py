from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
PY_SOURCE = (REPO_ROOT / "多平台聚合转换器_v1.0.py").read_text(encoding="utf-8")
TEMPLATE_SOURCE = (REPO_ROOT / "web" / "template.html").read_text(encoding="utf-8")
JS_SOURCE = (REPO_ROOT / "web" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
ALL_SOURCE = PY_SOURCE + "\n" + TEMPLATE_SOURCE + "\n" + JS_SOURCE


class DashboardImagePolicyTests(unittest.TestCase):
    def test_generator_declares_a_no_referrer_policy(self):
        self.assertIn('<meta name="referrer" content="no-referrer">', ALL_SOURCE)

    def test_generated_images_override_the_referrer_policy(self):
        self.assertGreaterEqual(ALL_SOURCE.count('referrerpolicy="no-referrer"'), 3)


if __name__ == "__main__":
    unittest.main()
