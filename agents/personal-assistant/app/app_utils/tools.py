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

import datetime
import logging
from typing import Any, Dict, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class WeatherInput(BaseModel):
    """Input parameters for querying weather information."""

    location: str = Field(
        ...,
        description="The city or location name to query weather for (e.g., 'San Francisco', 'Tokyo', 'London', 'New York').",
        min_length=1,
        max_length=100,
    )
    units: Literal["fahrenheit", "celsius"] = Field(
        default="fahrenheit",
        description="Temperature units requested by the user ('fahrenheit' or 'celsius').",
    )

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Location name cannot be empty or whitespace.")
        return s


class CurrentTimeInput(BaseModel):
    """Input parameters for querying current time in a city or location."""

    location: str = Field(
        ...,
        description="The city or location name to query current time for (e.g., 'San Francisco', 'Tokyo', 'London', 'New York').",
        min_length=1,
        max_length=100,
    )

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Location name cannot be empty or whitespace.")
        return s


def build_guided_error_response(
    error_code: str, message: str, suggestion: str
) -> Dict[str, Any]:
    """Generates a structured error response that guides the LLM to recover gracefully."""
    return {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "suggestion": suggestion,
    }


def get_weather(location: str, units: str = "fahrenheit") -> Dict[str, Any]:
    """Simulates getting weather information for a specified location.

    Args:
        location: The city or location name to query weather for (e.g., 'San Francisco', 'Tokyo', 'London', 'New York').
        units: Temperature units requested by the user ('fahrenheit' or 'celsius'). Defaults to 'fahrenheit'.

    Returns:
        A structured JSON dictionary containing weather data on success, or a guided error recovery response on failure.
    """
    try:
        validated_input = WeatherInput(location=location, units=units)
    except Exception as e:
        logger.warning(f"WeatherInput validation failed: {e}")
        return build_guided_error_response(
            error_code="INVALID_PARAMETER",
            message=f"Invalid parameter(s) provided for weather query: {e}",
            suggestion="Check the parameters provided. Ensure 'location' is a non-empty location name and 'units' is either 'fahrenheit' or 'celsius'. Ask the user for clarification if necessary.",
        )

    loc = validated_input.location.lower()

    # Supported locations mapping
    if "sf" in loc or "san francisco" in loc:
        temp_f = 60
        condition = "foggy"
    elif "tokyo" in loc:
        temp_f = 68
        condition = "clear"
    elif "london" in loc:
        temp_f = 55
        condition = "drizzly"
    elif "new york" in loc or "nyc" in loc:
        temp_f = 72
        condition = "partly cloudy"
    else:
        return build_guided_error_response(
            error_code="LOCATION_NOT_FOUND",
            message=f"Weather data is currently unavailable for location '{validated_input.location}'.",
            suggestion=f"Location '{validated_input.location}' is not recognized in simulated weather records. Please inform the user politely and offer to check weather for major supported cities such as San Francisco, Tokyo, London, or New York.",
        )

    # Convert temperature if celsius is requested
    temp = (
        temp_f
        if validated_input.units == "fahrenheit"
        else round((temp_f - 32) * 5 / 9, 1)
    )

    return {
        "status": "success",
        "location": validated_input.location,
        "temperature": temp,
        "units": validated_input.units,
        "condition": condition,
        "summary": f"It's {temp}° {'F' if validated_input.units == 'fahrenheit' else 'C'} and {condition} in {validated_input.location}.",
    }


def get_current_time(location: str) -> Dict[str, Any]:
    """Simulates getting the current time for a city or location.

    Args:
        location: The name of the city to get the current time for (e.g., 'San Francisco', 'Tokyo', 'London', 'New York').

    Returns:
        A structured JSON dictionary containing time information on success, or a guided error recovery response on failure.
    """
    try:
        validated_input = CurrentTimeInput(location=location)
    except Exception as e:
        logger.warning(f"CurrentTimeInput validation failed: {e}")
        return build_guided_error_response(
            error_code="INVALID_PARAMETER",
            message=f"Invalid location parameter provided: {e}",
            suggestion="Ensure 'location' is a valid non-empty string representing a city name (e.g., 'San Francisco', 'Tokyo', 'London', 'New York'). Ask the user for clarification if needed.",
        )

    loc = validated_input.location.lower()

    if "sf" in loc or "san francisco" in loc:
        tz_identifier = "America/Los_Angeles"
    elif "tokyo" in loc:
        tz_identifier = "Asia/Tokyo"
    elif "london" in loc:
        tz_identifier = "Europe/London"
    elif "new york" in loc or "nyc" in loc:
        tz_identifier = "America/New_York"
    elif "utc" in loc:
        tz_identifier = "UTC"
    else:
        return build_guided_error_response(
            error_code="LOCATION_NOT_FOUND",
            message=f"City '{validated_input.location}' was not found in supported time zone mappings.",
            suggestion=f"City '{validated_input.location}' could not be mapped to a timezone. Ask the user for clarification or suggest major cities like San Francisco, Tokyo, London, or New York.",
        )

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
    except Exception as e:
        logger.error(f"Error computing time for timezone {tz_identifier}: {e}")
        return build_guided_error_response(
            error_code="TIMEZONE_ERROR",
            message=f"Failed to retrieve current time for timezone {tz_identifier}.",
            suggestion="An internal timezone resolution error occurred. Ask the user to try another location.",
        )

    return {
        "status": "success",
        "location": validated_input.location,
        "timezone": tz_identifier,
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
        "summary": f"The current time in {validated_input.location} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}.",
    }


__all__ = [
    "WeatherInput",
    "CurrentTimeInput",
    "get_weather",
    "get_current_time",
    "build_guided_error_response",
]
