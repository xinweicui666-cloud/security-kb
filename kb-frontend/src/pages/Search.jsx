import { useState } from 'react';
import { Input, Select, Card, List, Typography } from 'antd';
import StatusTag from '../components/StatusTag';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [category, setCategory] = useState(null);
  const [statusFilter, setStatusFilter] = useState(null);
  const [searched, setSearched] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async () => {
    if (!query) return;
    const params = { q: query, limit: 30 };
    if (category) params.category = category;
    if (statusFilter) params.fill_status = statusFilter;
    const r = await api.get('/search', { params });
    setResults(r.data.results);
    setSearched(true);
  };

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索关键词..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onSearch={handleSearch}
          enterButton
          size="large"
        />
        <div style={{ marginTop: 8 }}>
          <Select
            placeholder="分类过滤"
            allowClear
            style={{ width: 200, marginRight: 8 }}
            onChange={setCategory}
            options={[
              { value: '01-制度体系', label: '制度体系' },
              { value: '02-技术基线', label: '技术基线' },
              { value: '03-合规框架', label: '合规框架' },
              { value: '04-审计与整改', label: '审计与整改' },
              { value: '05-风险案例', label: '风险案例' },
              { value: '06-应急响应', label: '应急响应' },
              { value: '07-FAQ', label: 'FAQ' },
              { value: '08-模板中心', label: '模板中心' },
            ]}
          />
          <Select
            placeholder="状态过滤"
            allowClear
            style={{ width: 150 }}
            onChange={setStatusFilter}
            options={[
              { value: 'filled', label: '已填充' },
              { value: 'partial', label: '部分填充' },
              { value: 'placeholder', label: '占位符' },
            ]}
          />
        </div>
      </Card>

      {searched && (
        <Typography.Text>找到 {results.length} 个结果</Typography.Text>
      )}

      <List
        dataSource={results}
        renderItem={(item) => (
          <List.Item
            onClick={() => navigate(`/editor/${item.id || 0}`)}
            style={{ cursor: 'pointer' }}
          >
            <List.Item.Meta
              title={<span>{item.title} <StatusTag status={item.fill_status} /></span>}
              description={item.relative_path}
            />
            <div style={{ maxWidth: 400, fontSize: 12, color: '#888' }}>{item.snippet}</div>
          </List.Item>
        )}
      />
    </div>
  );
}