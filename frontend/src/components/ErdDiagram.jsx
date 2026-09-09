// frontend/src/components/ErdDiagram.jsx

import { RelationshipDiagram } from "react-erd";
import "react-erd/dist/style.css";

const TABLE_COLORS = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2"];

const SCHEMA_NAME = "semantic_layer";

const PHYSICAL_TYPE_TO_DATA_TYPE = {
  integer: "number",
  int: "number",
  bigint: "number",
  smallint: "number",
  float: "number",
  double: "number",
  decimal: "number",
  numeric: "number",
  money: "money",
  boolean: "boolean",
  bool: "boolean",
  date: "datetime",
  datetime: "datetime",
  timestamp: "datetime",
  time: "datetime",
  text: "text",
  string: "text",
  varchar: "text",
  char: "text",
  binary: "binary",
  blob: "binary",
};

function mapDataType(physicalType) {
  return PHYSICAL_TYPE_TO_DATA_TYPE[(physicalType || "").toLowerCase()] || "other";
}

function buildSchema(tables, relationships) {
  const foreignKeysByTable = {};
  for (const rel of relationships) {
    if (!foreignKeysByTable[rel.from_table]) {
      foreignKeysByTable[rel.from_table] = [];
    }
    foreignKeysByTable[rel.from_table].push({
      columnName: rel.from_column,
      foreignTableName: rel.to_table,
      foreignColumnName: rel.to_column,
    });
  }

  return [
    {
      name: SCHEMA_NAME,
      tables: tables.map((table) => {
        const primaryKeyColumn = table.columns.find((c) => c.is_primary_key);
        const tableForeignKeys = foreignKeysByTable[table.name] || [];

        return {
          name: table.name,
          primaryKey: primaryKeyColumn ? primaryKeyColumn.name : "",
          columns: table.columns.map((col) => {
            const fk = tableForeignKeys.find((f) => f.columnName === col.name);
            return {
              name: col.name,
              type: mapDataType(col.physical_type),
              foreignKeys: fk
                ? [
                    {
                      foreignSchemaName: SCHEMA_NAME,
                      foreignTableName: fk.foreignTableName,
                      foreignColumnName: fk.foreignColumnName,
                      constrained: true,
                    },
                  ]
                : [],
            };
          }),
        };
      }),
    },
  ];
}

function ErdDiagram({ tables, relationships }) {
  if (!tables || tables.length === 0) {
    return <div style={{ color: "var(--color-muted)" }}>No tables to display.</div>;
  }

  const schemas = buildSchema(tables, relationships);

  return (
    <div
      style={{
        height: 440,
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        background: "var(--color-bg)",
        overflow: "hidden",
      }}
    >
      <RelationshipDiagram schemas={schemas} tableColors={TABLE_COLORS} />
    </div>
  );
}

export default ErdDiagram;