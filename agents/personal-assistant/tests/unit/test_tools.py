# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from pydantic import ValidationError

from app.app_utils.tools import (
    CurrentTimeInput,
    WeatherInput,
    get_current_time,
    get_weather,
)


def test_weather_input_validation():
    """Tests Pydantic validation for WeatherInput schema."""
    valid_input = WeatherInput(location="San Francisco", units="fahrenheit")
    assert valid_input.location == "San Francisco"
    assert valid_input.units == "fahrenheit"

    # Test celsius units
    valid_celsius = WeatherInput(location="Tokyo", units="celsius")
    assert valid_celsius.units == "celsius"

    # Blank location should raise ValidationError
    with pytest.raises(ValidationError):
        WeatherInput(location="   ")

    # Invalid unit choice should raise ValidationError
    with pytest.raises(ValidationError):
        WeatherInput(location="London", units="kelvin")  # type: ignore


def test_current_time_input_validation():
    """Tests Pydantic validation for CurrentTimeInput schema."""
    valid_input = CurrentTimeInput(location="Tokyo")
    assert valid_input.location == "Tokyo"

    # Blank location should raise ValidationError
    with pytest.raises(ValidationError):
        CurrentTimeInput(location="")


def test_get_weather_success():
    """Tests get_weather execution for supported cities."""
    res_sf = get_weather("San Francisco")
    assert res_sf["status"] == "success"
    assert res_sf["location"] == "San Francisco"
    assert res_sf["temperature"] == 60
    assert "foggy" in res_sf["condition"]

    res_tokyo = get_weather("Tokyo", units="celsius")
    assert res_tokyo["status"] == "success"
    assert res_tokyo["units"] == "celsius"
    assert res_tokyo["temperature"] == 20.0  # (68 - 32) * 5 / 9 = 20.0


def test_get_weather_guided_error_handling():
    """Tests that get_weather returns guided error responses for invalid or unknown locations."""
    # Unknown location
    res_unknown = get_weather("Atlantis")
    assert res_unknown["status"] == "error"
    assert res_unknown["error_code"] == "LOCATION_NOT_FOUND"
    assert "unavailable" in res_unknown["message"]
    assert "suggestion" in res_unknown
    assert "San Francisco" in res_unknown["suggestion"]

    # Invalid empty location parameter
    res_invalid = get_weather("")
    assert res_invalid["status"] == "error"
    assert res_invalid["error_code"] == "INVALID_PARAMETER"
    assert "suggestion" in res_invalid


def test_get_current_time_success():
    """Tests get_current_time execution for supported cities."""
    res_tokyo = get_current_time("Tokyo")
    assert res_tokyo["status"] == "success"
    assert res_tokyo["timezone"] == "Asia/Tokyo"
    assert "Tokyo" in res_tokyo["summary"]

    res_nyc = get_current_time("New York")
    assert res_nyc["status"] == "success"
    assert res_nyc["timezone"] == "America/New_York"


def test_get_current_time_guided_error_handling():
    """Tests that get_current_time returns guided error responses for invalid or unknown cities."""
    # Unknown city
    res_unknown = get_current_time("Gotham")
    assert res_unknown["status"] == "error"
    assert res_unknown["error_code"] == "LOCATION_NOT_FOUND"
    assert "suggestion" in res_unknown

    # Invalid empty city
    res_invalid = get_current_time("   ")
    assert res_invalid["status"] == "error"
    assert res_invalid["error_code"] == "INVALID_PARAMETER"
