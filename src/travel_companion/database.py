from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb

DATABASE_FILE_NAME = "travel_companion.duckdb"

SCHEMA_STATEMENTS = [
    "CREATE TABLE IF NOT EXISTS rate (id INTEGER PRIMARY KEY CHECK (id = 1), colones_per_dollar DOUBLE NOT NULL)",
]


def database_path_in(data_dir: Path) -> Path:
    return data_dir / DATABASE_FILE_NAME


@contextmanager
def connect(database_path: Path) -> Iterator[duckdb.DuckDBPyConnection]:
    connection = duckdb.connect(str(database_path))
    try:
        yield connection
    finally:
        connection.close()


def set_up_database(data_dir: Path) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    database_path = database_path_in(data_dir)
    with connect(database_path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
    return database_path
