from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect

from app.core.schema_compatibility import (
    BASELINE_SCHEMA,
    MILESTONE_1_SCHEMA,
    baseline_schema_issues,
    milestone_1_schema_issues,
)


def migrate_database(engine: Engine, config: Config) -> str:
    """Safely migrate empty, legacy baseline, or legacy M1 databases."""
    tables = set(inspect(engine).get_table_names())
    if "alembic_version" in tables:
        command.upgrade(config, "head")
        return "upgraded_versioned_database"

    application_tables = tables & set(BASELINE_SCHEMA)
    if not application_tables:
        command.upgrade(config, "head")
        return "upgraded_empty_database"

    baseline_issues = baseline_schema_issues(engine)
    if baseline_issues:
        raise RuntimeError(
            "Unversioned database is not baseline-compatible: "
            + "; ".join(baseline_issues)
        )

    milestone_1_issues = milestone_1_schema_issues(engine)
    if not milestone_1_issues:
        command.stamp(config, "0002_milestone1_core")
        command.upgrade(config, "head")
        return "upgraded_compatible_milestone_1_database"

    inspector = inspect(engine)
    new_table_names = set(MILESTONE_1_SCHEMA) - set(BASELINE_SCHEMA)
    has_milestone_1_changes = bool(tables & new_table_names)
    for table_name in set(MILESTONE_1_SCHEMA) & set(BASELINE_SCHEMA):
        actual_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        if actual_columns & MILESTONE_1_SCHEMA[table_name]:
            has_milestone_1_changes = True

    if not has_milestone_1_changes:
        command.stamp(config, "0001_baseline")
        command.upgrade(config, "head")
        return "upgraded_compatible_baseline_database"

    existing_new_tables = tables & new_table_names
    baseline_m1_tables = set(MILESTONE_1_SCHEMA) & set(BASELINE_SCHEMA)
    has_added_baseline_columns = False
    for table_name in baseline_m1_tables:
        actual_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        if actual_columns & MILESTONE_1_SCHEMA[table_name]:
            has_added_baseline_columns = True

    new_table_issues = [
        issue
        for issue in milestone_1_issues
        if any(table_name in issue for table_name in new_table_names)
    ]
    if (
        existing_new_tables == new_table_names
        and not new_table_issues
        and not has_added_baseline_columns
    ):
        command.stamp(config, "0001_baseline")
        command.upgrade(config, "head")
        return "repaired_create_all_partial_database"

    raise RuntimeError(
        "Unversioned database contains a partial Milestone 1 schema: "
        + "; ".join(milestone_1_issues)
    )
