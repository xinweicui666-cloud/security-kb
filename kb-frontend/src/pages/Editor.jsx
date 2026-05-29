import { useEffect, useState } from 'react';
import { Card, Descriptions, Button, Select, message, Space, Spin } from 'antd';
import MdEditor from '../components/MdEditor';
import StatusTag from '../components/StatusTag';
import api from '../api/client';
import { useParams, useNavigate } from 'react-router-dom';

export default function EditorPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get(`/files/${id}`).then((r) => {
      setFile(r.data);
      setContent(r.data.content || '');
    });
  }, [id]);

  if (!file) return <Spin />;

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/files/${id}`, { content, source: file.source });
      message.success('保存成功');
      const r = await api.get(`/files/${id}`);
      setFile(r.data);
    } catch (e) {
      message.error('保存失败: ' + (e.response?.data?.detail || e.message));
    }
    setSaving(false);
  };

  const handleStatusChange = async (status) => {
    try {
      await api.patch(`/files/${id}/status`, { fill_status: status });
      message.success('状态已更新');
      const r = await api.get(`/files/${id}`);
      setFile(r.data);
    } catch (e) {
      message.error('更新失败');
    }
  };

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={3} size="small">
          <Descriptions.Item label="标题">{file.title}</Descriptions.Item>
          <Descriptions.Item label="路径">{file.relative_path}</Descriptions.Item>
          <Descriptions.Item label="分类">{file.category_code}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Space>
              <StatusTag status={file.fill_status} />
              <Select
                size="small"
                value={file.fill_status}
                onChange={handleStatusChange}
                options={[
                  { value: 'placeholder', label: '占位符' },
                  { value: 'partial', label: '部分填充' },
                  { value: 'filled', label: '已填充' },
                ]}
                style={{ width: 120 }}
              />
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="来源">{file.source || '无'}</Descriptions.Item>
          <Descriptions.Item label="行数">{file.line_count} (内容行: {file.content_line_count})</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="编辑内容" extra={<Button type="primary" loading={saving} onClick={handleSave}>保存</Button>}>
        <MdEditor value={content} onChange={setContent} />
      </Card>
    </div>
  );
}