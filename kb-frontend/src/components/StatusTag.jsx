import { Tag } from 'antd';

const STATUS_MAP = {
  filled: { color: 'success', label: '已填充' },
  partial: { color: 'warning', label: '部分填充' },
  placeholder: { color: 'error', label: '占位符' },
};

export default function StatusTag({ status }) {
  const cfg = STATUS_MAP[status] || { color: 'default', label: status };
  return <Tag color={cfg.color}>{cfg.label}</Tag>;
}