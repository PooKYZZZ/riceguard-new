# tests/factories.py
"""Factory classes for generating test data following TDD principles."""
import datetime
from typing import Dict, Any, Optional
from factory import Factory, Faker, SubFactory, Trait, LazyAttribute
from factory.alchemy import SQLAlchemyModelFactory
from bson import ObjectId

from models import (
    ScanItem, DiseaseKey,
    RegisterIn, LoginIn,
    RecommendationOut,
    ScanListQuery
)

class UserFactory(Factory):
    """Factory for creating user test data."""

    class Meta:
        model = dict

    name = Faker("name")
    email = Faker("email")
    password = Faker("password", length=12, special_chars=True)

    class Params:
        # User variations for edge case testing
        long_name = Trait(name=Faker("pystr", max_chars=100))
        invalid_email = Trait(email="invalid-email")
        short_password = Trait(password=Faker("password", length=6))
        long_password = Trait(password=Faker("pystr", max_chars=150))

class ScanItemFactory(Factory):
    """Factory for creating scan item test data."""

    class Meta:
        model = ScanItem

    id = LazyAttribute(lambda _: str(ObjectId()))
    user_id = LazyAttribute(lambda _: str(ObjectId()))
    filename = Faker("file_name", extension="jpg")
    original_name = Faker("file_name", extension="jpg")
    file_size = Faker("random_int", min=1000, max=5000000)
    mime_type = Faker("mime_type", category="image")

    # ML prediction results
    prediction = Faker("random_element", elements=[d.value for d in DiseaseKey])
    confidence = Faker("pyfloat", left_digits=1, right_digits=3, min_value=0.0, max_value=1.0)
    confidence_level = Faker("random_element", elements=["high", "medium", "low"])
    calibrated_confidence = Faker("pyfloat", left_digits=1, right_digits=3, min_value=0.0, max_value=1.0)

    # Timestamps
    created_at = LazyAttribute(lambda _: datetime.datetime.now(datetime.timezone.utc))
    processed_at = LazyAttribute(lambda _: datetime.datetime.now(datetime.timezone.utc))

    # Image processing metadata
    image_metadata = LazyAttribute(lambda _: {
        "width": Faker("random_int", min=224, max=4096),
        "height": Faker("random_int", min=224, max=4096),
        "format": Faker("random_element", elements=["JPEG", "PNG"]),
        "color_space": Faker("random_element", elements=["RGB", "L"]),
        "has_alpha": Faker("boolean"),
        "exif": Faker("dict", allowed_types=[str, int, float])
    })

    class Params:
        # Predefined scenarios for comprehensive testing
        healthy_scan = Trait(
            prediction=DiseaseKey.HEALTHY,
            confidence=0.95,
            confidence_level="high",
            calibrated_confidence=0.94
        )

        blast_disease = Trait(
            prediction=DiseaseKey.LEAF_BLAST,
            confidence=0.87,
            confidence_level="high",
            calibrated_confidence=0.85
        )

        low_confidence_scan = Trait(
            prediction=DiseaseKey.UNCERTAIN,
            confidence=0.45,
            confidence_level="low",
            calibrated_confidence=0.42
        )

        large_file = Trait(
            file_size=Faker("random_int", min=8000000, max=10000000)  # 8-10MB
        )

        very_small_file = Trait(
            file_size=Faker("random_int", min=100, max=500)  # 100-500 bytes
        )

class RecommendationFactory(Factory):
    """Factory for creating recommendation test data."""

    class Meta:
        model = RecommendationOut

    disease = Faker("random_element", elements=[d.value for d in DiseaseKey])
    description = Faker("paragraph", nb_sentences=3)
    recommendations = LazyAttribute(lambda _: [
        Faker("sentence", nb_words=8) for _ in range(Faker("random_int", min=3, max=7).generate())
    ])

    class Params:
        # Specific disease recommendations
        bacterial_leaf_blight = Trait(
            disease=DiseaseKey.BACTERIAL_LEAF_BLIGHT,
            description="Bacterial leaf blight is a serious disease...",
            recommendations=[
                "Apply copper-based bactericides",
                "Use resistant rice varieties",
                "Ensure proper field drainage"
            ]
        )

        healthy_plant = Trait(
            disease=DiseaseKey.HEALTHY,
            description="Your rice plant appears healthy...",
            recommendations=[
                "Continue current farming practices",
                "Monitor for early disease symptoms",
                "Maintain proper irrigation"
            ]
        )

class RegisterInFactory(Factory):
    """Factory for creating registration request data."""

    class Meta:
        model = RegisterIn

    name = Faker("name")
    email = Faker("email")
    password = Faker("password", length=12, special_chars=True)

class LoginInFactory(Factory):
    """Factory for creating login request data."""

    class Meta:
        model = LoginIn

    email = Faker("email")
    password = Faker("password", length=12, special_chars=True)

class BulkDeleteInFactory(Factory):
    """Factory for creating bulk delete request data."""

    class Meta:
        model = dict

    ids = LazyAttribute(lambda _: [str(ObjectId()) for _ in range(Faker("random_int", min=1, max=5).generate())])

    class Params:
        large_batch = Trait(
            ids=LazyAttribute(lambda _: [str(ObjectId()) for _ in range(50)])
        )

        max_batch = Trait(
            ids=LazyAttribute(lambda _: [str(ObjectId()) for _ in range(100)])
        )

        oversized_batch = Trait(
            ids=LazyAttribute(lambda _: [str(ObjectId()) for _ in range(150)])
        )

class ScanListQueryFactory(Factory):
    """Factory for creating scan list query parameters."""

    class Meta:
        model = ScanListQuery

    page = Faker("random_int", min=1, max=10)
    page_size = Faker("random_int", min=5, max=50)

    class Params:
        first_page = Trait(page=1)
        large_page_size = Trait(page_size=100)
        invalid_page = Trait(page=0)
        invalid_page_size = Trait(page_size=0)

# Edge case test data generators
class EdgeCaseDataFactory:
    """Factory for generating edge case test data for comprehensive testing."""

    @staticmethod
    def invalid_emails() -> list:
        """Generate various invalid email formats for testing validation."""
        return [
            "plainaddress",
            "@missing-local.com",
            "missing-at-sign.com",
            "spaces.in@address.com",
            "email@.com",
            "email@domain.",
            "email..double.dot@domain.com",
            ".email@domain.com",
            "email@domain..com",
            "email@domain-with-dash.com",
            "email@domain_with_underscore.com",
            "email@domain.com-",
            "email@-domain.com",
            "email@111.222.333.44444",  # Invalid IP
            "email@[123.123.123.123]",
            "very.long.email.address@" + "a" * 250 + ".com",
            "email@domain." + "a" * 250  # Too long TLD
        ]

    @staticmethod
    def weak_passwords() -> list:
        """Generate weak passwords for security testing."""
        return [
            "12345678",  # Only numbers
            "password",  # Common word
            "qwerty",    # Sequential keyboard
            "abcabcab",  # Repeating pattern
            "short",     # Too short
            "UPPERCASE",  # No lowercase or numbers
            "lowercase",  # No uppercase or numbers
            "NumbersOnly123",  # No letters
            "Special!@#",  # No alphanumeric
            "a" * 150,  # Too long
            "password with spaces",  # Contains spaces
            "🚀🔥💯",  # Only emojis
        ]

    @staticmethod
    def malicious_filenames() -> list:
        """Generate potentially malicious filenames for security testing."""
        return [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "file.exe",
            "script.js",
            "style.css",
            "document.pdf",
            "archive.zip",
            "file.php",
            "shell.jsp",
            "exploit.asp",
            "null\x00byte.jpg",
            "very_long_filename_" + "a" * 250 + ".jpg",
            "file|pipe.jpg",
            "file\0null.jpg",
            "file?query.jpg",
            "file#fragment.jpg",
            "file%00.jpg",
            "con.jpg",  # Windows reserved name
            "prn.jpg",  # Windows reserved name
            "aux.jpg",  # Windows reserved name
            "nul.jpg",  # Windows reserved name
        ]

    @staticmethod
    def oversized_files() -> list:
        """Generate file size data for testing upload limits."""
        return [
            {"size": 2_097_152, "description": "Exactly 2MB"},  # boundary
            {"size": 2_097_153, "description": "Just over 2MB"},
            {"size": 10_485_760, "description": "10MB"},
            {"size": 104_857_600, "description": "100MB"},
            {"size": 1_073_741_824, "description": "1GB"},
        ]

# Test data fixtures for BDD scenarios
class BDDDataFactory:
    """Factory for generating BDD-style test scenarios."""

    @staticmethod
    def happy_path_user_journey():
        """Complete happy path user journey test data."""
        return {
            "registration": RegisterInFactory(),
            "login": LoginInFactory(),
            "scan": {
                "image": "test_images/healthy_rice_plant.jpg",
                "expected_prediction": DiseaseKey.HEALTHY,
                "expected_confidence_level": "high"
            },
            "history": ScanListQueryFactory(page=1, page_size=10)
        }

    @staticmethod
    def disease_detection_scenarios():
        """Various disease detection scenarios."""
        return [
            {
                "image": "test_images/leaf_blight_symptoms.jpg",
                "expected_prediction": DiseaseKey.BACTERIAL_LEAF_BLIGHT,
                "min_confidence": 0.7,
                "scenario": "Clear bacterial leaf blight symptoms"
            },
            {
                "image": "test_images/leaf_blast_lesions.jpg",
                "expected_prediction": DiseaseKey.LEAF_BLAST,
                "min_confidence": 0.8,
                "scenario": "Classic leaf blast lesions"
            },
            {
                "image": "test_images/brown_spot_spots.jpg",
                "expected_prediction": DiseaseKey.BROWN_SPOT,
                "min_confidence": 0.6,
                "scenario": "Early brown spot development"
            },
            {
                "image": "test_images/multiple_symptoms.jpg",
                "expected_prediction": DiseaseKey.UNCERTAIN,
                "min_confidence": 0.4,
                "scenario": "Multiple overlapping symptoms"
            }
        ]