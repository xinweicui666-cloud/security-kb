import { useEffect, useState } from 'react';
import { Card, Row, Col, Progress, Typography, Collapse, Tag } from 'antd';
import api from '../api/client';

const PRIORITY_COLORS = { P0: 'red', P1: 'orange', P2: 'gold', P3: 'blue' };

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [gaps, setGaps] = useState([]);

  useEffect(() => {
    api.get('/status/summary').then((r) => setSummary(r.data));
    api.get('/status/gaps').then((r) => setGaps(r.data.gaps));
  }, []);

  if (!summary) return <div>加载中...</div>;

  return (
    <div>
      <Typography.Title level={3}>安全合规知识库总览</Typography.Title>
      <Card style={{ marginBottom: 16 }}>
        <Typography.Text>总文件数: {summary.total_files} | 已填充: {summary.filled_files} | 填充率:</Typography.Text>
        <Progress percent={summary.fill_percentage} style={{ marginTop: 8 }} />
      </Card>

      <Row gutter={[16, 16]}>
        {summary.modules.map((m) => (
          <Col span={6} key={m.category_code}>
            <Card size="small" title={m.category_name}>
              <Progress percent={m.fill_percentage} size="small" />
              <div style={{ marginTop: 8, fontSize: 12 }}>
                总数: {m.total_files} | 已填充: {m.filled_files} | 占位符: {m.placeholder_files}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Typography.Title level={4} style={{ marginTop: 24 }}>缺失项优先级</Typography.Title>
      <Collapse items={gaps.map((g) => ({
        key: g.priority,
        label: <span><Tag color={PRIORITY_COLORS[g.priority]}>{g.priority}</Tag> {g.description} ({g.files.length}项)</span>,
        children: g.files.map((f) => (
          <div key={f.relative_path} style={{ marginBottom: 4 }}>
            <Tag color="error">占位符</Tag> {f.relative_path} — {f.title}
          </div>
        )),
      }))} />
    </div>
  );
}