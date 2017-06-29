from django.core.exceptions import ValidationError


def valid_year(value):
    if len(str(value)) > 4:
        raise ValidationError('Must be a four digit (or less) year')


def verify_latlon(value):
    if not -180 <= value <= 180:
        raise ValidationError('Lat/Lon must be between -180 and 180 degrees.')
