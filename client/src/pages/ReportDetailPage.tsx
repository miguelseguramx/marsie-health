import { Card, Descriptions, Typography, Spin, Result, Button } from "antd";
import { Link, useParams } from "react-router-dom";
import { AxiosError } from "axios";
import { useReport } from "../hooks/useReports";
import { CbcTable } from "../components/CbcTable";
import { formatDateTime } from "../utils/date";

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, error } = useReport(id);

  if (isLoading) return <Spin size="large" />;

  if (isError) {
    const status =
      error instanceof AxiosError ? error.response?.status : undefined;
    if (status === 404) {
      return (
        <Result
          status="404"
          title="Report not found"
          subTitle="This report does not exist or you do not have permission to view it."
          extra={
            <Link to="/results">
              <Button type="primary">Back to reports</Button>
            </Link>
          }
        />
      );
    }
    return (
      <Result
        status="error"
        title="Could not load report"
        subTitle={error?.message ?? "Unknown error"}
      />
    );
  }

  if (!data) return null;

  return (
    <div className="report-detail-page">
      <Card>
        <Typography.Title level={3}>{data.report_type.toUpperCase()} report</Typography.Title>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered size="small">
          <Descriptions.Item label="Patient">
            {data.patient_name || data.patient_filaxis_id}
          </Descriptions.Item>
          <Descriptions.Item label="Filaxis ID">{data.patient_filaxis_id}</Descriptions.Item>
          <Descriptions.Item label="Lab">{data.lab_name}</Descriptions.Item>
          <Descriptions.Item label="Status">{data.status}</Descriptions.Item>
          <Descriptions.Item label="Uploaded">
            {formatDateTime(data.uploaded_at)}
          </Descriptions.Item>
          <Descriptions.Item label="Processed">
            {formatDateTime(data.processed_at)}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Typography.Title level={4}>Complete blood count</Typography.Title>
        <CbcTable rows={data.cbc_results} />
      </Card>
    </div>
  );
}
