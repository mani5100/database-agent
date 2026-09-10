# src/database_agent/services/sql_compiler.py

import sqlglot
from sqlglot import exp

from database_agent.models.query_context import QueryContext


class UnknownIdentifierError(Exception):
    """Raised when the LLM's SQL references a table or column not present
    in the provided QueryContext, either a hallucination or an attempt to
    access something outside what was authorized for this question."""
    pass


class UnqualifiedColumnError(Exception):
    """Raised when a column reference isn't qualified with its table name.
    The LLM is required to always write table.column, never a bare column."""
    pass


class TableAliasError(Exception):
    """Raised when the SQL uses a table alias. Aliases are forbidden here,
    the LLM must always reference tables by their full business name."""
    pass

class NonSelectStatementError(Exception):
    """Raised when the SQL is not a SELECT statement. Only read queries
    are permitted, the agent must never modify data."""
    pass


def _build_lookup(context: QueryContext) -> dict[str, dict]:
    lookup = {}
    for table in context.tables:
        lookup[table.business_name] = {
            "physical_name": table.physical_name,
            "columns": {col.business_name: col.physical_name for col in table.columns},
        }
    return lookup


def compile_to_physical_sql(
    business_sql: str,
    context: QueryContext,
    dialect: str,  # "postgres" or "mysql"
) -> str:
    """
    Parses business_sql (written using business table/column names, fully
    qualified columns, no table aliases), validates every reference against
    context, and returns the equivalent SQL using physical names.

    Raises TableAliasError, UnqualifiedColumnError, or UnknownIdentifierError
    if the SQL violates any of these constraints.
    """
    lookup = _build_lookup(context)

    tree = sqlglot.parse_one(business_sql, dialect=dialect)

    if not isinstance(tree, exp.Select):
        raise NonSelectStatementError(
            f"Only SELECT statements are allowed, got: {type(tree).__name__}. "
            "The agent cannot modify data."
        )

    # Step 0: reject any table alias before doing anything else.
    for table_node in tree.find_all(exp.Table):
        if table_node.alias:
            raise TableAliasError(
                f"Table alias '{table_node.alias}' found on '{table_node.name}'. "
                "Table aliases are not allowed, always use the full business table name."
            )

    # Collect SELECT-clause aliases (e.g. "month" in "EXTRACT(...) AS month").
    # References to these in GROUP BY/HAVING/ORDER BY are legitimate and
    # never qualified, since they refer to an output expression, not a
    # real table column.
    select_aliases = {
        alias_node.alias for alias_node in tree.find_all(exp.Alias) if alias_node.alias
    }

    # Collect CTE names (WITH x AS (...)). These are query-local, not real
    # tables, so they and their output columns should never be validated
    # against the schema lookup or renamed.
    cte_names = {cte.alias for cte in tree.find_all(exp.CTE) if cte.alias}

    # Step 1: replace table references.
    for table_node in tree.find_all(exp.Table):
        business_table_name = table_node.name
        if business_table_name in cte_names:
            continue  # CTE reference, not a real table, leave untouched
        if business_table_name not in lookup:
            raise UnknownIdentifierError(
                f"Unknown table '{business_table_name}', not part of the available schema for this query"
            )
        physical_table_name = lookup[business_table_name]["physical_name"]
        table_node.set("this", exp.to_identifier(physical_table_name))

    # Step 2: replace column references. Resolved against the ORIGINAL
    # business names in `lookup`, since aliases are already forbidden,
    # every column qualifier here is guaranteed to be either a real
    # business table name or a CTE name.
    for column_node in tree.find_all(exp.Column):
        table_qualifier = column_node.table
        business_column_name = column_node.name

        if table_qualifier in cte_names:
            continue  # column from a CTE's own output, not a real table column

        if not table_qualifier:
            if business_column_name in select_aliases:
                continue
            raise UnqualifiedColumnError(
                f"Column '{business_column_name}' must be qualified with its table name "
                f"(e.g. 'orders.{business_column_name}'), unqualified columns are not allowed"
            )

        if table_qualifier not in lookup:
            raise UnknownIdentifierError(
                f"Unknown table '{table_qualifier}' referenced by column '{business_column_name}'"
            )

        table_columns = lookup[table_qualifier]["columns"]
        if business_column_name not in table_columns:
            raise UnknownIdentifierError(
                f"Unknown column '{business_column_name}' on table '{table_qualifier}', "
                "not part of the available schema for this query"
            )

        physical_column_name = table_columns[business_column_name]
        column_node.set("this", exp.to_identifier(physical_column_name))
        physical_table_name = lookup[table_qualifier]["physical_name"]
        column_node.set("table", exp.to_identifier(physical_table_name))

    return tree.sql(dialect=dialect)