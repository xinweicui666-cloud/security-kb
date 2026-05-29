import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  FolderOutlined,
  SearchOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Browser from './pages/Browser';
import Editor from './pages/Editor';
import SearchPage from './pages/Search';
import Compliance from './pages/Compliance';

const { Sider, Content } = Layout;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/browser', icon: <FolderOutlined />, label: '知识库浏览' },
  { key: '/search', icon: <SearchOutlined />, label: '搜索' },
  { key: '/compliance', icon: <SafetyOutlined />, label: '合规查询' },
];

function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="light">
        <div style={{ padding: '16px', textAlign: 'center', fontWeight: 'bold', fontSize: 16 }}>
          安全合规知识库
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Content style={{ margin: 16, padding: 16, background: '#fff', borderRadius: 8 }}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/browser" element={<Browser />} />
            <Route path="/editor/:id" element={<Editor />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/compliance" element={<Compliance />} />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}