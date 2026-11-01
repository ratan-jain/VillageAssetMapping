
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "App"))

from DataValidator import validate_asset


class TestDataValidator(unittest.TestCase):

    def setUp(self):
        self.asset = {
            "id": "AST-000001",
            "name": "Government School",
            "village": "Kallur",
            "category": "school",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "owner_type": "government",
            "owner_name": "Department of Education",
            "managing_authority": None,
            "verification_status": "unverified",
        }

    def test_valid_asset(self):
        self.assertEqual(validate_asset(self.asset), [])

    def test_missing_name(self):
        self.asset["name"] = ""
        self.assertTrue(validate_asset(self.asset))

    def test_invalid_latitude(self):
        self.asset["latitude"] = 250
        self.assertTrue(validate_asset(self.asset))

    def test_invalid_category(self):
        self.asset["category"] = "airport"
        self.assertTrue(validate_asset(self.asset))

    def test_invalid_owner_type(self):
        self.asset["owner_type"] = "unknown"
        self.assertTrue(validate_asset(self.asset))

    def test_invalid_verification_status(self):
        self.asset["verification_status"] = "maybe"
        self.assertTrue(validate_asset(self.asset))

    def test_boolean_latitude_rejected(self):
        self.asset["latitude"] = True
        self.assertTrue(validate_asset(self.asset))


if __name__ == "__main__":
    unittest.main()
