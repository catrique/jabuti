"""Lightweight CQRS layout and rules of each generated component."""

from dataclasses import dataclass

from jabuti.project.config import Backend, Database, Framework, Frontend
from jabuti.project.planner import ComponentPlan

CQRS_SUMMARY = (
    "Lightweight CQRS: Commands are operations that may change application "
    "state; Queries are read-only operations. Routes, controllers, pages and "
    "components only handle their own concerns and delegate application "
    "behavior to a Command or a Query."
)

BACKEND_RULES = (
    "Commands change state; Queries only read. Name them after the use case "
    "(`Create...Command`, `List...Query`).",
    "Routes/controllers handle transport only: read the request, call a "
    "Command or Query through its handler and turn the result into a "
    "response. Never put business rules, SQL or external calls in them.",
    "The CQRS primitives know nothing about the web framework, HTTP, the ORM "
    "or the database. HTTP status mapping lives only in the HTTP adapter.",
    "Database access belongs to `infrastructure/database`; communication with "
    "external systems belongs to `infrastructure/integrations` (create it with "
    "the first integration).",
    "Handlers never commit, open generic transactions or publish events. "
    "Transactions belong to the Command (or the infrastructure it uses) that "
    "needs them.",
    "Raise `ApplicationError` with the right `ErrorCode` (`NOT_FOUND`, "
    "`CONFLICT`, `FORBIDDEN`...) for known failures. Do not let them become "
    "`INTERNAL_ERROR` when the caller must tell them apart.",
    "Unexpected exceptions are logged by the handlers and returned as a "
    "generic `INTERNAL_ERROR`; never expose stack traces to clients.",
    "Never log passwords, tokens, `Authorization` headers, credentials or "
    "other sensitive data.",
)

FRONTEND_RULES = (
    "Pages and components never call `fetch`, `HttpClient` or any HTTP "
    "library directly for application operations.",
    "Reads go through Queries; state-changing operations go through Commands.",
    "HTTP transport lives only in `infrastructure/api`; Commands and Queries "
    "depend on `ApiClient`, not on the HTTP implementation.",
    "The API base URL is configured in one place; never duplicate base URL "
    "logic nor hardcode production URLs.",
    "Never put secrets in the frontend: everything in it reaches the browser.",
    "Keep framework-specific behavior out of the generic CQRS primitives.",
)

GENERAL_RULES = (
    "Do not introduce repositories, mediators, buses, factories, managers, "
    "services or additional layers without a concrete, current need.",
    "Prefer simple, explicit code over premature abstractions.",
    "Do not create empty folders in advance; create a module when a feature "
    "needs it.",
    "`shared/` holds only code really shared by several modules; code that "
    "belongs to one domain stays in that module. Avoid catch-all `utils` "
    "files.",
)


@dataclass(frozen=True, slots=True)
class ArchitectureGuide:
    """Where things live in a component and how it grows."""

    layout: tuple[str, ...]
    rules: tuple[str, ...]
    new_feature: tuple[str, ...]


def architecture_guide(component: ComponentPlan) -> ArchitectureGuide:
    """Layout, stack-specific rules and growth steps of a component."""
    return _GUIDES[component.framework](component)


def _python(component: ComponentPlan) -> ArchitectureGuide:
    flask = component.framework is Backend.FLASK
    entry = (
        "app/__init__.py              Flask app factory, blueprint registration"
        if flask
        else "app/main.py                  FastAPI app, middleware and routers"
    )
    routes = "routes.py (Blueprint)" if flask else "router.py (APIRouter)"
    layout = [
        entry,
        *(["app/routes.py                Pages and /health"] if flask else []),
        "app/http.py                  ErrorCode -> HTTP status (HTTP adapter)",
        "app/application/cqrs/        Command, Query, handlers, results, ErrorCode",
        *_python_database(component),
        f"app/modules/<domain>/        On demand: commands/, queries/, {routes}",
        *(["templates/ static/           Jinja templates and static files"]
          if flask else []),
        "tests/",
    ]
    handler = (
        "Flask views are synchronous: run operations with "
        "`CommandHandler().handle(...)` / `QueryHandler().handle(...)`."
        if flask
        else "In `async def` routes use `await CommandHandler().handle_async(...)` "
        "/ `await QueryHandler().handle_async(...)`; it accepts both sync and "
        "async `execute()`."
    )
    response = (
        "After a Command, respond with `redirect`; after a Query, with "
        "`render_template` (pages) or `jsonify` (JSON). Use `unwrap()` from "
        "`app/http.py` to turn failures into HTTP errors."
        if flask
        else "Use `unwrap()` from `app/http.py` to return the data or raise the "
        "`HTTPException` for the result's `ErrorCode`."
    )
    return ArchitectureGuide(
        layout=tuple(layout),
        rules=(handler, response),
        new_feature=(
            "Create `app/modules/<domain>/` only when the feature is requested.",
            "Add one file per use case in `commands/` or `queries/`, subclassing "
            "`Command[T]` / `Query[T]` and implementing `execute()`; override "
            "`validate()` / `has_permission()` only when needed.",
            f"Expose it in `{routes.split()[0]}` and register it in "
            f"`{entry.split()[0]}`.",
            "Add tests for the new operations and routes.",
        ),
    )


def _python_database(component: ComponentPlan) -> list[str]:
    if component.database is Database.NONE:
        return []
    return [
        "app/config.py                Settings read from environment variables",
        "app/infrastructure/database.py  SQLAlchemy engine, sessions and Base",
    ]


def _express(component: ComponentPlan) -> ArchitectureGuide:
    database = (
        ["src/infrastructure/database.js  MySQL pool (mysql2)"]
        if component.database is not Database.NONE
        else []
    )
    views = (
        ["views/ public/               EJS views and static files"]
        if component.serves_frontend
        else []
    )
    return ArchitectureGuide(
        layout=(
            "src/server.js                Loads .env and starts the server",
            "src/app.js                   Express app, middleware and routes",
            "src/http.js                  ErrorCode -> HTTP status (HTTP adapter)",
            "src/application/cqrs/        Command, Query, handlers, results, "
            "ErrorCode",
            *database,
            "src/modules/<domain>/        On demand: commands/, queries/, routes.js",
            *views,
            "tests/",
        ),
        rules=(
            "Operations are `async`; run them with `await handleCommand(...)` / "
            "`await handleQuery(...)`.",
            "Use `sendResult()` from `src/http.js` for JSON responses, or "
            "`httpStatus()` when rendering views.",
        ),
        new_feature=(
            "Create `src/modules/<domain>/` only when the feature is requested.",
            "Add one file per use case in `commands/` or `queries/`, extending "
            "`Command` / `Query` and implementing `async execute()`.",
            "Expose it in the module's `routes.js` (an `express.Router`) and "
            "mount it in `src/app.js`.",
            "Add `node:test` tests for the new operations and routes.",
        ),
    )


def _react(_component: ComponentPlan) -> ArchitectureGuide:
    return ArchitectureGuide(
        layout=(
            "src/application/cqrs.ts      Command, Query and optional result types",
            "src/infrastructure/api/      config.ts (base URL), client.ts "
            "(ApiClient over fetch)",
            "src/modules/<domain>/        On demand: commands/, queries/, "
            "components/",
            "src/shared/                  Only code shared by several modules",
        ),
        rules=(
            "React uses Promise/async idiomatically. Do not add RxJS, state "
            "libraries, TanStack Query or Axios unless the project decides to.",
            "The API base URL comes from `VITE_API_BASE_URL` "
            "(`src/infrastructure/api/config.ts`).",
            "Components and hooks call `query.execute(...)` / "
            "`command.execute(...)`; failed responses arrive as `ApiError`.",
        ),
        new_feature=(
            "Create `src/modules/<domain>/` only when the feature is requested.",
            "Implement each use case as a class implementing `Command` / `Query` "
            "that receives an `ApiClient` (default: `apiClient`).",
            "Keep components focused on rendering and user interaction.",
        ),
    )


def _angular(_component: ComponentPlan) -> ArchitectureGuide:
    return ArchitectureGuide(
        layout=(
            "src/app/application/cqrs.ts  Command, Query and optional result types",
            "src/app/infrastructure/api/  api-client.ts (ApiClient over HttpClient)",
            "src/environments/            apiBaseUrl per build configuration",
            "src/app/modules/<domain>/    On demand: commands/, queries/, "
            "components",
            "src/app/shared/              Only code shared by several modules",
        ),
        rules=(
            "Angular uses `Observable`, `HttpClient` and dependency injection "
            "idiomatically; do not convert operations to Promises.",
            "The API base URL comes from `environment.apiBaseUrl` "
            "(`src/environments/`).",
            "Only `ApiClient` injects `HttpClient`.",
        ),
        new_feature=(
            "Create `src/app/modules/<domain>/` only when the feature is "
            "requested.",
            "Implement each use case as an `@Injectable({ providedIn: 'root' })` "
            "class implementing `Command` / `Query` that injects `ApiClient`.",
            "Components inject the Command/Query and subscribe to `execute()`.",
        ),
    )


_GUIDES = {
    Backend.FASTAPI: _python,
    Backend.FLASK: _python,
    Backend.EXPRESS: _express,
    Frontend.REACT: _react,
    Frontend.ANGULAR: _angular,
}


def is_frontend(framework: Framework) -> bool:
    """Whether a framework is a browser frontend."""
    return isinstance(framework, Frontend)
