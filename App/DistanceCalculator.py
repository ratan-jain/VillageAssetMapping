
from math import asin, cos, isfinite, radians, sin, sqrt


EARTH_RADIUS_KM = 6371.0088


def _validate_coordinate(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")

    if not isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two coordinates.

    Returns:
        Distance in kilometres as a float.

    Raises:
        ValueError: If any coordinate is invalid.
    """
    _validate_coordinate(lat1, "Latitude 1", -90, 90)
    _validate_coordinate(lon1, "Longitude 1", -180, 180)
    _validate_coordinate(lat2, "Latitude 2", -90, 90)
    _validate_coordinate(lon2, "Longitude 2", -180, 180)

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad)
        * cos(lat2_rad)
        * sin(delta_lon / 2) ** 2
    )

    # Protect against tiny floating-point rounding errors.
    a = max(0.0, min(1.0, a))

    central_angle = 2 * asin(sqrt(a))

    return EARTH_RADIUS_KM * central_angle
