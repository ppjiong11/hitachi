import unittest

from hitachi_cn.parsers import single_liftstatus


class ParserTests(unittest.TestCase):
    def test_single_liftstatus_accepts_dict(self) -> None:
        payload = {"liftstatus": {"liftID": 1, "door1Opened": 0}}
        self.assertEqual(single_liftstatus(payload)["liftID"], 1)

    def test_single_liftstatus_picks_matching_lift(self) -> None:
        payload = {
            "liftstatus": [
                {"liftID": 2, "door1Opened": 0},
                {"liftID": 1, "door1Opened": 1},
            ]
        }
        self.assertEqual(single_liftstatus(payload, lift_id=1)["door1Opened"], 1)


if __name__ == "__main__":
    unittest.main()
