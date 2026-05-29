import { useEffect, useState } from 'react';
import { Layout, Select, Typography } from 'antd';
import CategoryTree from '../components/CategoryTree';
import FileTable from '../components/FileTable';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';

const { Sider, Content } = Layout;

export default function Browser() {
  const [categories, setCategories] = useState([]);
  const [selectedCode, setSelectedCode] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/categories').then((r) => setCategories(r.data.categories));
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = { page_size: 100 };
    if (selectedCode) {
      const top = selectedCode.split('/')[0];
      params.category = top;
      if (selectedCode.includes('/')) {
        params.subcategory = selectedCode.split('/')[1];
      }
    }
    if (statusFilter) params.fill_status = statusFilter;
    api.get('/files', { params }).then((r) => {
      setFiles(r.data.items);
      setLoading(false);
    });
  }, [selectedCode, statusFilter]);

  return (
    <Layout style={{ background: '#fff', minHeight: 500 }}>
      <Sider width={280} style={{ background: '#fff', padding: 16, borderRight: '1px solid #eee' }}>
        <Typography.Title level={5}>知识库分类</Typography.Title>
        <CategoryTree categories={categories} selectedCode={selectedCode} onSelect={setSelectedCode} />
      </Sider>
      <Content style={{ padding: 16 }}>
        <div style={{ marginBottom: 16 }}>
          <Select
            placeholder="筛选状态"
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
        <FileTable files={files} loading={loading} onRowClick={(record) => navigate(`/editor/${record.id}`)} />
      </Content>
    </Layout>
  );
}