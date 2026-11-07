import json


# OSM values mapped to our project's service groups and service types.

HEALTHCARE_TYPES = {
    "hospital": ("healthcare", "hospital"),
    "clinic": ("healthcare", "clinic"),
    "doctor": ("healthcare", "medical_practice"),
    "dentist": ("healthcare", "dental_clinic"),
    "pharmacy": ("healthcare", "pharmacy"),
    "laboratory": ("healthcare", "medical_laboratory"),
    "physiotherapist": ("healthcare", "physiotherapy"),
    "alternative": ("alternative_healthcare", "alternative_healthcare"),
    "blood_donation": ("healthcare", "blood_donation_centre"),
    "blood_bank": ("healthcare", "blood_bank"),
    "centre": ("healthcare", "health_centre"),
    "health_centre": ("healthcare", "health_centre"),
    "rehabilitation": ("healthcare", "rehabilitation_centre"),
    "optometrist": ("healthcare", "optometry"),
    "psychotherapist": ("healthcare", "mental_health_practice"),
    "counselling": ("healthcare", "counselling_service"),
}

EDUCATION_TYPES = {
    "school": ("education", "school"),
    "kindergarten": ("education", "kindergarten"),
    "college": ("education", "college"),
    "university": ("education", "university"),
    "music_school": ("education", "specialized_school"),
    "driving_school": ("education", "driving_school"),
    "language_school": ("education", "language_school"),
    "prep_school": ("education", "preparatory_school"),
    "art_school": ("education", "specialized_school"),
}

EMERGENCY_TYPES = {
    "police": ("emergency", "police_station"),
    "fire_station": ("emergency", "fire_station"),
    "ambulance_station": ("emergency", "ambulance_station"),
}

TRANSPORT_TYPES = {
    "bus_stop": ("transport", "bus_stop"),
    "stop_position": ("transport", "public_transport_stop"),
    "platform": ("transport", "transport_platform"),
    "bus_station": ("transport", "bus_station"),
    "taxi": ("transport", "taxi_stand"),
    "ferry_terminal": ("transport", "ferry_terminal"),
}

PUBLIC_AMENITY_TYPES = {
    "toilets": ("public_amenity", "public_toilet"),
    "drinking_water": ("public_amenity", "drinking_water"),
    "library": ("public_amenity", "library"),
    "bench": ("public_amenity", "public_bench"),
    "shelter": ("public_amenity", "public_shelter"),
    "fountain": ("public_amenity", "public_fountain"),
    "community_centre": ("community", "community_centre"),
    "social_facility": ("community", "social_facility"),
    "public_building": ("civic", "public_building"),
    "townhall": ("civic", "town_hall"),
    "courthouse": ("civic", "courthouse"),
    "post_office": ("public_service", "post_office"),
    "post_box": ("public_service", "post_box"),
    "recycling": ("public_amenity", "recycling_facility"),
    "waste_disposal": ("public_amenity", "waste_disposal"),
    "waste_basket": ("public_amenity", "waste_bin"),
}

FINANCIAL_TYPES = {
    "bank": ("financial", "bank"),
    "atm": ("financial", "atm"),
    "bureau_de_change": ("financial", "currency_exchange"),
    "money_transfer": ("financial", "money_transfer"),
}

COMMERCIAL_TYPES = {
    "restaurant": ("commercial", "restaurant"),
    "fast_food": ("commercial", "fast_food"),
    "cafe": ("commercial", "cafe"),
    "pub": ("commercial", "pub"),
    "bar": ("commercial", "bar"),
    "fuel": ("commercial", "fuel_station"),
    "parking": ("transport", "parking_facility"),
    "parking_entrance": ("transport", "parking_entrance"),
    "parking_space": ("transport", "parking_space"),
    "cinema": ("recreation", "cinema"),
    "theatre": ("recreation", "theatre"),
    "marketplace": ("commercial", "marketplace"),
    "veterinary": ("healthcare", "veterinary_clinic"),
    "childcare": ("education", "childcare"),
}


def _normalise(value):
    """Convert an optional value into a consistent lowercase string."""

    if value is None:
        return ""

    return str(value).strip().lower()


def _result(
    service_group,
    service_type,
    confidence,
    review_status,
    reason
):
    """Build a consistent classification result."""

    return {
        "service_group": service_group,
        "service_type": service_type,
        "confidence": confidence,
        "review_status": review_status,
        "classification_reason": reason
    }


def _classified(service_group, service_type, reason, confidence="high"):
    return _result(
        service_group,
        service_type,
        confidence,
        "classified",
        reason
    )


def _needs_review(service_type, reason, confidence="low"):
    return _result(
        "unclassified",
        service_type,
        confidence,
        "needs_review",
        reason
    )


def _parse_tags(tags_json):
    """Parse OSM tags without silently accepting malformed data."""

    if isinstance(tags_json, dict):
        return tags_json

    if not tags_json:
        return {}

    try:
        tags = json.loads(tags_json)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Invalid OSM tags JSON.")

    if not isinstance(tags, dict):
        raise ValueError("OSM tags JSON must contain an object.")

    return tags


def classify_component(
    category,
    component_type,
    tags_json,
    name=None
):
    """
    Classify one OSM geographical component.

    Original OSM fields are not modified.

    Returns:
        service_group
        service_type
        confidence
        review_status
        classification_reason
    """

    category = _normalise(category)
    component_type = _normalise(component_type)
    name = _normalise(name)

    try:
        tags = _parse_tags(tags_json)
    except ValueError as error:
        return _needs_review(
            "unknown",
            str(error)
        )

    # Normalise tag keys and values.
    tags = {
        _normalise(key): _normalise(value)
        for key, value in tags.items()
    }

    amenity = tags.get("amenity", "")
    healthcare = tags.get("healthcare", "")
    education = tags.get("education", "")
    public_transport = tags.get("public_transport", "")
    highway = tags.get("highway", "")
    description = _normalise(tags.get("description", ""))

    # 1. Explicitly uncertain OSM records must not be treated as verified.
    if amenity == "fixme":
        fixme_type = _normalise(tags.get("fixme:type", ""))

        return _needs_review(
            f"possible_{fixme_type or 'unknown'}",
            "OSM marks this amenity as fixme; its type requires verification."
        )

    # 2. Healthcare tags.
    if healthcare in HEALTHCARE_TYPES:
        group, service_type = HEALTHCARE_TYPES[healthcare]

        if healthcare == "centre":
            supporting_text = f"{name} {description}"

            if (
                "primary health centre" in supporting_text
                or "primary healthcare centre" in supporting_text
                or "primary healthcentre" in supporting_text
                or "phc" in supporting_text.split()
            ):
                service_type = "primary_health_centre"

        return _classified(
            group,
            service_type,
            f"Explicit OSM healthcare tag: healthcare={healthcare}."
        )

    if healthcare == "yes":
        return _needs_review(
            "unspecified_healthcare",
            "OSM identifies a healthcare facility but does not specify its type."
        )

    # 3. Explicit amenity tags.
    amenity_maps = (
        HEALTHCARE_TYPES,
        EDUCATION_TYPES,
        EMERGENCY_TYPES,
        PUBLIC_AMENITY_TYPES,
        FINANCIAL_TYPES,
        COMMERCIAL_TYPES,
    )

    for mapping in amenity_maps:
        if amenity in mapping:
            group, service_type = mapping[amenity]

            return _classified(
                group,
                service_type,
                f"Explicit OSM amenity tag: amenity={amenity}."
            )

    # 4. Other education and transport tags.
    if education in EDUCATION_TYPES:
        group, service_type = EDUCATION_TYPES[education]

        return _classified(
            group,
            service_type,
            f"Explicit OSM education tag: education={education}."
        )

    if public_transport in {"platform", "stop_position", "station"}:
        service_type = (
            "transport_platform"
            if public_transport == "platform"
            else "public_transport_stop"
        )

        return _classified(
            "transport",
            service_type,
            f"Explicit OSM public_transport tag: {public_transport}."
        )

    if highway == "bus_stop":
        return _classified(
            "transport",
            "bus_stop",
            "Explicit OSM highway=bus_stop tag."
        )

    # 5. Carefully limited fallbacks using the imported category and type.
    if category == "hospital" and component_type in HEALTHCARE_TYPES:
        group, service_type = HEALTHCARE_TYPES[component_type]

        return _classified(
            group,
            service_type,
            "Inferred from imported hospital category and component type.",
            confidence="medium"
        )

    if category == "school" and component_type in EDUCATION_TYPES:
        group, service_type = EDUCATION_TYPES[component_type]

        return _classified(
            group,
            service_type,
            "Inferred from imported school category and component type.",
            confidence="medium"
        )

    if category == "college" and component_type in EDUCATION_TYPES:
        group, service_type = EDUCATION_TYPES[component_type]

        return _classified(
            group,
            service_type,
            "Inferred from imported college category and component type.",
            confidence="medium"
        )

    if category == "transport" and component_type in TRANSPORT_TYPES:
        group, service_type = TRANSPORT_TYPES[component_type]

        return _classified(
            group,
            service_type,
            "Inferred from imported transport category and component type.",
            confidence="medium"
        )

    if category == "public_facility":
        known_types = (
            EMERGENCY_TYPES
            | PUBLIC_AMENITY_TYPES
            | FINANCIAL_TYPES
            | COMMERCIAL_TYPES
        )

        if component_type in known_types:
            group, service_type = known_types[component_type]

            return _classified(
                group,
                service_type,
                "Inferred from imported public_facility category and component type.",
                confidence="medium"
            )

    # 6. Do not guess when the available information is insufficient.
    return _needs_review(
        "unknown",
        "No sufficiently specific OSM tag or supported fallback rule."
    )