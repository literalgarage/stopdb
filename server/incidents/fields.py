import datetime
import typing as t
from dataclasses import dataclass

from django import forms
from django.core.exceptions import ValidationError
from django.db import models


def _check_int(value: str, expected_length: int) -> int:
    """Ensure that `value` is a valid integer of length `expected_length`."""
    if not value.isdigit():
        raise ValidationError("Invalid integer")
    if len(value) != expected_length:
        raise ValidationError(f"Invalid integer length; expected {expected_length}")
    return int(value)


def _check_optional_int(value: str | None, expected_length: int) -> int | None:
    """Ensure that `value` is a valid integer of length `expected_length`, or None."""
    if value is None:
        return None
    return _check_int(value, expected_length)


@dataclass(frozen=True)
class PartialDate:
    """
    A partial date, with support for:

    - Year
    - Year and month
    - Year, month, and day

    No other combinations are allowed.
    """

    year: int
    month: int | None
    day: int | None

    def __post_init__(self):
        """Validate the partial date."""
        if self.month is None and self.day is not None:
            raise ValidationError("Day requires month")
        if self.month is not None and not (1 <= self.month <= 12):
            raise ValidationError("Invalid month")
        if self.day is not None and not (1 <= self.day <= 31):
            raise ValidationError("Invalid day")
        if not (1900 <= self.year <= 9999):
            raise ValidationError("Invalid year")
        if self.day is not None:
            assert self.month is not None
            try:
                datetime.date(self.year, self.month, self.day)
            except ValueError:
                raise ValidationError("Invalid date")

    @classmethod
    def from_str(cls, value: str) -> t.Self:
        """
        Convert a string to a PartialDate.

        The string should be in the format "YYYY", "YYYY-MM", or "YYYY-MM-DD".
        """
        parts = value.split("-")
        y_str, m_str, d_str = parts[0], None, None
        if len(parts) > 1:
            m_str = parts[1]
        if len(parts) > 2:
            d_str = parts[2]
        if len(parts) > 3:
            raise ValidationError("Invalid date format")
        y, m, d = (
            _check_int(y_str, 4),
            _check_optional_int(m_str, 2),
            _check_optional_int(d_str, 2),
        )
        return cls(year=y, month=m, day=d)

    @classmethod
    def from_date(cls, date: datetime.date) -> t.Self:
        """Convert a datetime.date to a PartialDate."""
        return cls(year=date.year, month=date.month, day=date.day)

    def __str__(self) -> str:
        """
        Convert the PartialDate to a string.

        The string will be in the format "YYYY", "YYYY-MM", or "YYYY-MM-DD".
        """
        if self.month is None:
            return f"{self.year:04}"
        if self.day is None:
            return f"{self.year:04}-{self.month:02}"
        return f"{self.year:04}-{self.month:02}-{self.day:02}"


class PartialDateFormField(forms.CharField):
    """A custom form field for the PartialDate model."""

    def clean(self, value: str) -> PartialDate:
        return PartialDate.from_str(value)

    def to_python(self, value: PartialDate) -> str:
        return str(value)

    def prepare_value(self, value: PartialDate) -> str:
        return str(value)


class PartialDateWidget(forms.TextInput):
    """A custom widget for the PartialDateFormField."""

    def __init__(self, attrs=None):
        final_attrs = {"placeholder": "YYYY, YYYY-MM, or YYYY-MM-DD"}
        if attrs is not None:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs)


class PartialDateField(models.CharField):
    """A custom database field that allows for storage of a PartialDate."""

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 10
        super().__init__(*args, **kwargs)

    def to_python(self, value: str) -> PartialDate:
        return PartialDate.from_str(value)

    def from_db_value(self, value: str, expression, connection) -> PartialDate:
        return self.to_python(value)

    def get_prep_value(self, value: PartialDate) -> str:
        return str(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        kwargs["form_class"] = PartialDateFormField
        kwargs["widget"] = PartialDateWidget
        return super().formfield(**kwargs)
