import { Table } from 'antd';
import StatusTag from './StatusTag';

export default function FileTable({ files, loading, onRowClick }) {
  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '路径', dataIndex: 'relative_path', key: 'path', ellipsis: true, width: 300 },
    { title: '状态', dataIndex: 'fill_status', key: 'status', width: 100, render: (s) => <StatusTag status={s} /> },
    { title: '行数', dataIndex: 'line_count', key: 'lines', width: 80 },
    { title: '来源', dataIndex: 'source', key: 'source', ellipsis: true, width: 200 },
  ];

  return (
    <Table
      columns={columns}
      dataSource={files}
      loading={loading}
      rowKey="id"
      size="small"
      onRow={(record) => ({
        onClick: () => onRowClick(record),
        style: { cursor: 'pointer' },
      })}
      pagination={{ pageSize: 20 }}
    />
  );
}