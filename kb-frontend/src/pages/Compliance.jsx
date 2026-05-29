import { useState } from 'react';
import { Card, Select, List, Typography, Row, Col, Statistic } from 'antd';
import StatusTag from '../components/StatusTag';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';

const STANDARDS = [
  { value: '等保2.0', label: '等保2.0' },
  { value: 'ISO27001', label: 'ISO 27001' },
  { value: 'SOC2', label: 'SOC 2' },
  { value: 'GDPR', label: 'GDPR' },
];

export default function CompliancePage() {
  const [standard, setStandard] = useState(null);
  const [data, setData] = useState(null);
  const [matrix, setMatrix] = useState(null);
  const navigate = useNavigate();

  useState(() => {
    api.get('/compliance/matrix').then((r) => setMatrix(r.data));
  }, []);

  const handleSelect = async (std) => {
    setStandard(std);
    const r = await api.get(`/compliance/${std}`);
    setData(r.data);
  };

  return (
    <div>
      <Typography.Title level={3}>合规查询</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Select
          placeholder="选择合规标准"
          style={{ width: 200 }}
          onChange={handleSelect}
          options={STANDARDS}
        />
      </Card>

      {matrix && (
        <Card title="合规标准概览" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            {Object.entries(matrix.summary || {}).map(([name, info]) => (
              <Col span={6} key={name}>
                <Statistic
                  title={name}
                  value={info.filled_files}
                  suffix={`/ ${info.total_files}`}
                />
                <Typography.Text type="secondary">填充率 {info.fill_percentage}%</Typography.Text>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {data && (
        <Card title={`${data.standard} — 文件列表`}>
          <List
            dataSource={data.files}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={<span>{item.title} <StatusTag status={item.fill_status} /></span>}
                  description={`${item.relative_path} ${item.source ? '| 来源: ' + item.source : ''}`}
                />
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  );
}