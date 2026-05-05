import { useState } from "react";
import { Card, Typography, Tag, Alert, Table, Tooltip, Button } from "antd";
import type { ColumnsType, TablePaginationConfig } from "antd/es/table";
import type { FilterValue, SorterResult } from "antd/es/table/interface";
import { useNavigate } from "react-router-dom";
import { useReports } from "../hooks/useReports";
import { useAuth } from "../hooks/useAuth";
import type { ReportListItem } from "../types/api";
import { formatDate } from "../utils/date";
import { UploadReportModal } from "../components/UploadReportModal";

type SortOrder = "ascend" | "descend" | null | undefined;

const SORT_FIELD_MAP: Record<string, string> = {
  patient_filaxis_id: "patient__filaxis_id",
  lab_name: "lab__name",
  status: "status",
  uploaded_at: "uploaded_at",
};

function buildOrdering(field: string | undefined, order: SortOrder): string {
  if (!field || !order) return "-uploaded_at";
  const apiField = SORT_FIELD_MAP[field] ?? field;
  return order === "ascend" ? apiField : `-${apiField}`;
}

export function ReportListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isPhysician = user?.role === "Physician";
  const isLabAdmin = user?.role === "LabAdmin";
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortField, setSortField] = useState<string>("uploaded_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("descend");
  const [uploadOpen, setUploadOpen] = useState(false);

  const ordering = buildOrdering(sortField, sortOrder);
  const { data, isLoading, isError, error } = useReports({
    page,
    pageSize,
    ordering,
  });

  const handleTableChange = (
    pagination: TablePaginationConfig,
    _filters: Record<string, FilterValue | null>,
    sorter: SorterResult<ReportListItem> | SorterResult<ReportListItem>[],
  ) => {
    const nextPage = pagination.current ?? 1;
    const nextPageSize = pagination.pageSize ?? 20;
    setPage(nextPage);
    setPageSize(nextPageSize);

    const activeSorter = Array.isArray(sorter) ? sorter[0] : sorter;
    if (activeSorter && activeSorter.order) {
      setSortField(String(activeSorter.field ?? "uploaded_at"));
      setSortOrder(activeSorter.order);
    } else {
      setSortField("uploaded_at");
      setSortOrder("descend");
    }
  };

  const columns: ColumnsType<ReportListItem> = [
    {
      title: "Patient",
      key: "patient",
      render: (_value, record) => record.patient_name || record.patient_filaxis_id,
    },
    {
      title: "Filaxis ID",
      dataIndex: "patient_filaxis_id",
      key: "patient_filaxis_id",
      sorter: true,
      sortOrder: sortField === "patient_filaxis_id" ? sortOrder : null,
    },
    {
      title: "Lab",
      dataIndex: "lab_name",
      key: "lab_name",
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      sorter: true,
      sortOrder: sortField === "status" ? sortOrder : null,
      render: (_value, record) => (
        <Tag color={record.status === "processed" ? "green" : "blue"}>
          {record.status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: "Uploaded",
      dataIndex: "uploaded_at",
      key: "uploaded_at",
      sorter: true,
      defaultSortOrder: "descend",
      sortOrder: sortField === "uploaded_at" ? sortOrder : null,
      render: (_value, record) => formatDate(record.uploaded_at),
    },
    ...(isPhysician
      ? [
          {
            title: "WBC",
            key: "wbc",
            render: (_value: unknown, record: ReportListItem) =>
              record.wbc_low ? (
                <Tooltip title={`WBC ${record.wbc_value ?? "?"} ×10³/µL — below 4.5`}>
                  <Tag color="red">Low WBC</Tag>
                </Tooltip>
              ) : null,
          },
        ]
      : []),
  ];

  return (
    <div className="report-list-page">
      <Card>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 16,
            gap: 16,
          }}
        >
          <Typography.Title level={3} style={{ margin: 0 }}>
            Reports
          </Typography.Title>
          {isLabAdmin && (
            <Button type="primary" onClick={() => setUploadOpen(true)}>
              Upload report
            </Button>
          )}
        </div>
        {isError && (
          <Alert
            type="error"
            message="Could not load reports"
            description={error.message}
            showIcon
          />
        )}
        <Table<ReportListItem>
          rowKey="id"
          columns={columns}
          dataSource={data?.results ?? []}
          loading={isLoading}
          locale={{ emptyText: "No reports available" }}
          pagination={{
            current: page,
            pageSize,
            total: data?.count ?? 0,
            showSizeChanger: true,
          }}
          onChange={handleTableChange}
          onRow={(record) => ({
            onClick: () => navigate(`/results/${record.id}`),
            style: { cursor: "pointer" },
          })}
        />
      </Card>
      <UploadReportModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </div>
  );
}
