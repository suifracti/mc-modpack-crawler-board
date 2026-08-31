from pathlib import Path
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / "多平台聚合转换器_v1.0.py").read_text(
    encoding="utf-8"
)


class DashboardImagePolicyTests(unittest.TestCase):
    def test_generator_declares_a_no_referrer_policy(self):
        self.assertIn('<meta name="referrer" content="no-referrer">', SOURCE)

    def test_generated_images_override_the_referrer_policy(self):
        self.assertGreaterEqual(SOURCE.count('referrerpolicy="no-referrer"'), 3)


if __name__ == "__main__":
    unittest.main()
