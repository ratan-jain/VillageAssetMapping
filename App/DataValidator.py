
import re
from math import isfinite


SUPPORTED_CATEGORIES = {
    "school",
    "college",
    "hospital",
    "forest",
    "river",
    "lake",
    "water_tank",
    "road",
}

SUPPORTED_OWNER_TYPES = {
    "government",
    "private",
    "community",
    "religious_institution",
    "other",
}

SUPPORTED_VERIFICATION_STATUSES = {
    "unverified",
    "verified",
    "disputed",
}


def validate_asset(asset):
    errors = []

    if not isinstance(asset, dict):
        return ["Asset must be a dictionary."]

    asset_id = asset.get("id")

    if not isinstance(asset_id, str) or not re.fullmatch(
        r"AST-\d{6,}", asset_id
    ):
        errors.append("Asset ID must use the format AST-000001.")

    for field in ("name", "village", "owner_name"):
        value = asset.get(field)

        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be non-empty text.")

    category = asset.get("category")

    if (
        not isinstance(category, str)
        or category not in SUPPORTED_CATEGORIES
    ):
        errors.append("Category is not supported.")

    owner_type = asset.get("owner_type")

    if (
        not isinstance(owner_type, str)
        or owner_type not in SUPPORTED_OWNER_TYPES
    ):
        errors.append("Owner type is not supported.")

    for field, minimum, maximum in (
        ("latitude", -90, 90),
        ("longitude", -180, 180),
    ):
        value = asset.get(field)

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{field} must be a number.")
        elif not isfinite(value) or not minimum <= value <= maximum:
            errors.append(f"{field} is outside the valid range.")

    authority = asset.get("managing_authority")

    if authority is not None and (
        not isinstance(authority, str) or not authority.strip()
    ):
        errors.append(
            "Managing authority must be non-empty text or None."
        )

    status = asset.get("verification_status")

    if (
        not isinstance(status, str)
        or status not in SUPPORTED_VERIFICATION_STATUSES
    ):
        errors.append("Verification status is not supported.")

    return errors
