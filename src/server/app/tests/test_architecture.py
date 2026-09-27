import ast
import os
import subprocess
import sys
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.database import Base, register_models

SERVER = Path(__file__).resolve().parents[2]
MODULES = {"api_keys", "token_feed", "streaming", "token_prices", "token_images"}


def test_independent_sdk_import_without_backend_or_resources() -> None:
    code = """
import sys, logging
sys.path.insert(0, sys.argv[1])
import curl_cffi
def forbidden(*args, **kwargs):
    raise AssertionError('network resources created during import')
curl_cffi.AsyncSession = forbidden
before = list(logging.getLogger().handlers)
import axiom_trade_api
assert 'app' not in sys.modules
assert logging.getLogger().handlers == before
assert axiom_trade_api.AxiomTradeClient
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(SERVER / "third_party_apis")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_domain_application_and_public_package_boundaries() -> None:
    forbidden = {"fastapi", "sqlalchemy", "httpx", "third_party_apis"}
    edges: dict[str, set[str]] = {name: set() for name in MODULES}
    for path in (SERVER / "app").rglob("*.py"):
        relative = path.relative_to(SERVER / "app")
        if relative.parts[0] not in MODULES or "tests" in relative.parts:
            continue
        owner = relative.parts[0]
        transport = (
            path.name
            in {"router.py", "schemas.py", "dependencies.py", "serialization.py"}
            or "adapters" in relative.parts
        )
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                assert all(alias.name != "*" for alias in node.names), path
                names = [node.module or ""] if node.level == 0 else []
                if node.level == 0 and node.module == "app":
                    edges[owner].update(
                        alias.name
                        for alias in node.names
                        if alias.name in MODULES and alias.name != owner
                    )
            else:
                continue
            for name in names:
                if not transport:
                    assert name.split(".")[0] not in forbidden, (path, name)
                if name.startswith("app.") and name.split(".")[1] in MODULES:
                    assert name.split(".")[1] == owner or len(name.split(".")) == 2, (
                        path,
                        name,
                    )
    for owner in edges:

        def visit(module: str, seen: set[str]) -> None:
            assert module not in seen, (owner, module)
            for target in edges[module]:
                visit(target, seen | {module})

        visit(owner, set())
    for path in (SERVER / "third_party_apis").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                assert (node.module or "").split(".")[0] not in {
                    "app",
                    "fastapi",
                    "sqlalchemy",
                }, path


def test_alembic_existing_schema_matches_single_registered_model(
    tmp_path: Path,
) -> None:
    database = tmp_path / "schema.db"
    environment = dict(
        os.environ,
        DATABASE_URL=f"sqlite:///{database}",
        DATABASE_ASYNC_URL=f"sqlite+aiosqlite:///{database}",
    )
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=SERVER,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    register_models()
    register_models()
    assert list(Base.metadata.tables) == ["api_keys"]
    engine = create_engine(f"sqlite:///{database}")
    try:
        with engine.connect() as connection:
            differences = compare_metadata(
                MigrationContext.configure(connection), Base.metadata
            )
        assert differences == []
    finally:
        engine.dispose()
