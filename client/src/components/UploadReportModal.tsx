import { useState } from "react";
import { Modal, Form, Input, Upload, Button, message } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd/es/upload/interface";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { uploadReport } from "../api/labAdmin";
import type { UploadReportResponse } from "../types/api";

interface FormValues {
  patient_email: string;
  patient_first_name: string;
  patient_last_name: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function UploadReportModal({ open, onClose }: Props) {
  const [form] = Form.useForm<FormValues>();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const queryClient = useQueryClient();

  const mutation = useMutation<UploadReportResponse, AxiosError<{ detail?: string }>, FormValues>({
    mutationFn: (values) =>
      uploadReport({
        ...values,
        file: (fileList[0]?.originFileObj as File | undefined) ?? null,
      }),
    onSuccess: (data) => {
      const text = data.email_sent
        ? `Onboarding email sent to ${data.patient_email}`
        : `Report added to ${data.patient_email}'s account`;
      message.success(text);
      form.resetFields();
      setFileList([]);
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      onClose();
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      message.error(detail ?? "Could not upload report. Please try again.");
    },
  });

  const handleClose = () => {
    if (mutation.isPending) return;
    form.resetFields();
    setFileList([]);
    onClose();
  };

  return (
    <Modal
      open={open}
      title="Upload report"
      onCancel={handleClose}
      onOk={() => form.submit()}
      okText="Send"
      confirmLoading={mutation.isPending}
      destroyOnClose
    >
      <Form<FormValues>
        form={form}
        layout="vertical"
        onFinish={(values) => mutation.mutate(values)}
        requiredMark={false}
      >
        <Form.Item
          label="Patient email"
          name="patient_email"
          rules={[
            { required: true, message: "Please enter the patient's email" },
            { type: "email", message: "Please enter a valid email" },
          ]}
        >
          <Input autoComplete="off" />
        </Form.Item>
        <Form.Item
          label="First name"
          name="patient_first_name"
          rules={[{ required: true, message: "Please enter the patient's first name" }]}
        >
          <Input autoComplete="off" />
        </Form.Item>
        <Form.Item
          label="Last name"
          name="patient_last_name"
          rules={[{ required: true, message: "Please enter the patient's last name" }]}
        >
          <Input autoComplete="off" />
        </Form.Item>
        <Form.Item label="Report file (PDF)">
          <Upload
            beforeUpload={() => false}
            maxCount={1}
            accept=".pdf"
            fileList={fileList}
            onChange={({ fileList: next }) => setFileList(next)}
          >
            <Button icon={<UploadOutlined />}>Select PDF</Button>
          </Upload>
        </Form.Item>
      </Form>
    </Modal>
  );
}
