from ai_librarian_apis.core.logger import logger
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def get_injected_openapi_schema(app: FastAPI) -> dict:
    """Gets the OpenAPI schema with examples dynamically injected.

    This function dynamically injects examples into the OpenAPI schema, 
    especially for endpoints where response examples depend on runtime application state
    (e.g., `app.state.tools`).

    A common issue arises when defining Pydantic schemas with `Field` examples
    that directly reference the main FastAPI application instance (`app`) or
    its state (e.g., `Field(example=app.state.some_attribute)`).

    For instance, if `main.py` imports a router, and that router's schema
    imports `app` from `main.py` to define an example, a circular dependency
    occurs:

    `main.py` -> `router.py` -> `schemas.py` -> `main.py` (for `app.state.some_attribute`)

    To avoid this circular import, schema definitions should not directly import
    `app`. Instead, this function is called within the FastAPI `lifespan` event.
    At this point, `app.state` attributes are guaranteed to be initialized. 
    The function then generates the base OpenAPIschema and programmatically injects 
    the dynamic examples based on the available `app.state` data. 
    The generated schema is then assigned to `app.openapi_schema` for caching.

    Args:
        app: The FastAPI app instance.

    Returns:
        dict: The OpenAPI schema with injected examples.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    try:
        schema["paths"]["/v1/tools/list"]["get"]["responses"]["200"]["content"]["application/json"]["example"] = {
            "tools": [{"name": t.name, "description": t.description} for t in app.state.tools]
        }
        schema["paths"]["/v1/tools/run"]["post"]["responses"]["200"]["content"]["application/json"]["example"] = {
            "output": "The output of the tool.",
            "tool_calls": [{"name": t.name, "args": t.args} for t in app.state.tools],
        }
    except Exception as e:
        logger.error(f"Error injecting openapi schema: {e}")

    return schema
