import os
from dataclasses import dataclass
from warnings import deprecated

import httpx
from langchain_core.tools import tool


@dataclass
class OpenWeatherMapError(Exception):
    """Base exception for errors related to the OpenWeatherMap service."""

    message: str
    status_code: int | None = None
    _message_prefix: str = "OpenWeatherMap service error"

    def __post_init__(self) -> None:
        """Initializes the exception with a formatted message."""
        super().__init__(f"{self._message_prefix}: {self.message}")


@dataclass
class OpenWeatherMapLimitError(OpenWeatherMapError):
    """Exception raised when a tool request is rejected due to rate limiting."""

    message: str = "Rate limit exceeded"
    status_code: int = 429
    _message_prefix: str = "Rate limit exceeded"


@dataclass
class OpenWeatherMapApiKeyMissingError(OpenWeatherMapError):
    """Raised when the OpenWeatherMap API key is missing."""

    message: str = "OpenWeatherMap API Key is not configured."
    status_code: int = 500
    _message_prefix: str = "OpenWeatherMap API Key is not configured"


@dataclass
class OpenWeatherMapApiKeyInvalidError(OpenWeatherMapError):
    """Raised when the OpenWeatherMap API key is invalid."""

    message: str = "OpenWeatherMap API Key is invalid."
    status_code: int = 401
    _message_prefix: str = "OpenWeatherMap API Key is invalid"


@dataclass
class OpenWeatherMapRequestError(OpenWeatherMapError):
    """Raised for network or client-side errors during weather API calls."""

    message: str = "Failed to connect to weather API."
    status_code: int = 503
    _message_prefix: str = "Failed to connect to weather API"


@dataclass
class OpenWeatherMapResponseError(OpenWeatherMapError):
    """Raised for non-successful responses from the weather API (e.g., 4xx, 5xx)."""

    message: str
    status_code: int
    _message_prefix: str = "Weather API response error"


@deprecated("use langchain_tools.open_weather_map.weather.get_current_weather instead")
@tool("weather", parse_docstring=True)
async def get_current_weather(
    lat: float,
    lon: float,
    api_key: str | None = None,
) -> str:
    """Gets the current weather for a given geographical location using the OpenWeatherMap API.

    Args:
        lat: Required. The latitude of the location.
        lon: Required. The longitude of the location.

    Returns:
        A string containing the weather data in XML format as requested from the API.
        Example structure:
        <?xml version="1.0" encoding="UTF-8"?>
        <current>
            <city id="..." name="...">...</city>
            <temperature value="..." min="..." max="..." unit="kelvin"></temperature>
            <feels_like value="..." unit="kelvin"></feels_like>
            <humidity value="..." unit="%"></humidity>
            <pressure value="..." unit="hPa"></pressure>
            <wind>...</wind>
            <clouds value="..." name="..."></clouds>
            <visibility value="..."></visibility>
            <precipitation mode="..."></precipitation>
            <weather number="..." value="..." icon="..."></weather>
            <lastupdate value="..."></lastupdate>
        </current>
    """
    if api_key is None:
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            raise OpenWeatherMapApiKeyMissingError()

    try:
        async with httpx.AsyncClient() as client:
            result = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": api_key,
                    "mode": "xml",
                },
            )
            result.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise OpenWeatherMapApiKeyInvalidError(e)
        elif e.response.status_code == 429:
            raise OpenWeatherMapLimitError(e)
        else:
            raise OpenWeatherMapResponseError(e, e.response.status_code, e.response.text)
    except httpx.RequestError as e:
        raise OpenWeatherMapRequestError(e)
    except httpx.TimeoutException as e:
        raise OpenWeatherMapRequestError(e)
    except httpx.HTTPError as e:
        raise OpenWeatherMapResponseError(e, e.response.status_code, e.response.text)

    return result.text
