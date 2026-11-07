
import unittest

from App.FacilityClassifier import classify_component


class TestFacilityClassifier(unittest.TestCase):

    def test_classifies_hospital(self):
        result = classify_component(
            "hospital",
            "hospital",
            '{"healthcare": "hospital"}'
        )

        self.assertEqual(result["service_group"], "healthcare")
        self.assertEqual(result["service_type"], "hospital")
        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["review_status"], "classified")

    def test_classifies_clinic_from_amenity(self):
        result = classify_component(
            "hospital",
            "yes",
            '{"amenity": "clinic"}'
        )

        self.assertEqual(result["service_type"], "clinic")

    def test_classifies_pharmacy_separately(self):
        result = classify_component(
            "hospital",
            "pharmacy",
            '{"healthcare": "pharmacy"}'
        )

        self.assertEqual(result["service_group"], "healthcare")
        self.assertEqual(result["service_type"], "pharmacy")
        self.assertNotEqual(result["service_type"], "hospital")

    def test_classifies_alternative_healthcare(self):
        result = classify_component(
            "hospital",
            "alternative",
            '{"healthcare": "alternative"}'
        )

        self.assertEqual(
            result["service_group"],
            "alternative_healthcare"
        )
        self.assertEqual(
            result["service_type"],
            "alternative_healthcare"
        )

    def test_classifies_primary_health_centre(self):
        result = classify_component(
            "hospital",
            "centre",
            '{"healthcare": "centre"}',
            "Yamluru Urban Primary Health Centre"
        )

        self.assertEqual(
            result["service_type"],
            "primary_health_centre"
        )
        self.assertEqual(result["confidence"], "high")

    def test_classifies_school(self):
        result = classify_component(
            "school",
            "yes",
            '{"amenity": "school"}'
        )

        self.assertEqual(result["service_group"], "education")
        self.assertEqual(result["service_type"], "school")

    def test_classifies_kindergarten(self):
        result = classify_component(
            "school",
            "yes",
            '{"amenity": "kindergarten"}'
        )

        self.assertEqual(
            result["service_type"],
            "kindergarten"
        )

    def test_classifies_college(self):
        result = classify_component(
            "college",
            "college",
            '{"amenity": "college"}'
        )

        self.assertEqual(result["service_type"], "college")

    def test_classifies_police_station(self):
        result = classify_component(
            "public_facility",
            "yes",
            '{"amenity": "police"}'
        )

        self.assertEqual(result["service_group"], "emergency")
        self.assertEqual(result["service_type"], "police_station")

    def test_classifies_bus_stop(self):
        result = classify_component(
            "transport",
            "yes",
            '{"highway": "bus_stop"}'
        )

        self.assertEqual(result["service_group"], "transport")
        self.assertEqual(result["service_type"], "bus_stop")

    def test_fixme_requires_review(self):
        result = classify_component(
            "public_facility",
            "fixme",
            '{"amenity": "fixme", "fixme:type": "dental"}'
        )

        self.assertEqual(result["service_group"], "unclassified")
        self.assertEqual(result["service_type"], "possible_dental")
        self.assertEqual(result["review_status"], "needs_review")

    def test_unspecified_healthcare_requires_review(self):
        result = classify_component(
            "hospital",
            "yes",
            '{"healthcare": "yes"}'
        )

        self.assertEqual(
            result["service_type"],
            "unspecified_healthcare"
        )
        self.assertEqual(result["review_status"], "needs_review")

    def test_unknown_amenity_requires_review(self):
        result = classify_component(
            "public_facility",
            "yes",
            '{"amenity": "yes"}'
        )

        self.assertEqual(result["service_group"], "unclassified")
        self.assertEqual(result["review_status"], "needs_review")

    def test_invalid_json_requires_review(self):
        result = classify_component(
            "hospital",
            "centre",
            '{"healthcare": centre}'
        )

        self.assertEqual(result["service_group"], "unclassified")
        self.assertEqual(result["review_status"], "needs_review")

    def test_fallback_uses_medium_confidence(self):
        result = classify_component(
            "school",
            "school",
            '{}'
        )

        self.assertEqual(result["service_group"], "education")
        self.assertEqual(result["service_type"], "school")
        self.assertEqual(result["confidence"], "medium")

    def test_does_not_guess_from_name(self):
        result = classify_component(
            "other",
            "yes",
            '{}',
            "Government Hospital"
        )

        self.assertEqual(result["service_group"], "unclassified")
        self.assertEqual(result["review_status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
