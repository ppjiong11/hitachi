import unittest

from hitachi_cn.config import DEFAULT_CONFIG, clone_config


class ConfigTests(unittest.TestCase):
    def test_clone_config_overrides_values(self) -> None:
        cfg = clone_config(USERNAME="demo", RUN_TRIP_TEST=False)
        self.assertEqual(cfg["USERNAME"], "demo")
        self.assertFalse(cfg["RUN_TRIP_TEST"])

    def test_clone_config_does_not_mutate_defaults(self) -> None:
        clone_config(USERNAME="other")
        self.assertEqual(DEFAULT_CONFIG["USERNAME"], "WVCOND")


if __name__ == "__main__":
    unittest.main()
