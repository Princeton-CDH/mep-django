from django.core.exceptions import ValidationError


def verify_latlon(value):
    """Convenience validator to check that a latitude or longitude value is
    a valid deciaml degree between -180 and 180."""
    if not -180 <= value <= 180:
        raise ValidationError("Lat/Lon must be between -180 and 180 degrees.")
