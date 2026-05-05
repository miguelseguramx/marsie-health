import { Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { CbcFlag, CbcResult } from "../types/api";

const FLAG_LABEL: Record<CbcFlag, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
  critical: "Critical",
};

const FLAG_COLOR: Record<CbcFlag, string> = {
  low: "blue",
  normal: "default",
  high: "orange",
  critical: "red",
};

const SECTIONS: ReadonlyArray<{ category: string; label: string }> = [
  { category: "red_cells", label: "Red blood cells" },
  { category: "red_indices", label: "Red cell indices" },
  { category: "white_cells", label: "White blood cells" },
  { category: "platelets", label: "Platelets" },
];

const columns: ColumnsType<CbcResult> = [
  {
    title: "Code",
    dataIndex: "analyte_code",
    key: "analyte_code",
    width: 120,
  },
  {
    title: "Analyte",
    dataIndex: "analyte_name",
    key: "analyte_name",
  },
  {
    title: "Value",
    dataIndex: "value",
    key: "value",
    align: "right",
    render: (value: string, row) => (
      <span className="cbc-table__cell--value">
        {value} {row.unit}
      </span>
    ),
  },
  {
    title: "Range",
    key: "range",
    align: "right",
    render: (_, row) => {
      if (!row.ref_range_low && !row.ref_range_high) return "—";
      return `${row.ref_range_low ?? "—"} – ${row.ref_range_high ?? "—"}`;
    },
  },
  {
    title: "Flag",
    dataIndex: "flag",
    key: "flag",
    width: 120,
    render: (flag: CbcFlag) => <Tag color={FLAG_COLOR[flag]}>{FLAG_LABEL[flag]}</Tag>,
  },
];

export function CbcTable({ rows }: { rows: CbcResult[] }) {
  return (
    <div className="cbc-table">
      {SECTIONS.map(({ category, label }) => {
        const sectionRows = rows.filter((r) => r.category === category);
        if (sectionRows.length === 0) return null;
        return (
          <section key={category}>
            <h3 className="cbc-table__section-header">{label}</h3>
            <Table<CbcResult>
              columns={columns}
              dataSource={sectionRows}
              rowKey={(r) => r.analyte_code}
              rowClassName={(r) => `cbc-table__row cbc-table__row--${r.flag}`}
              pagination={false}
              size="middle"
            />
          </section>
        );
      })}
    </div>
  );
}
