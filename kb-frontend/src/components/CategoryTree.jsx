import { Tree } from 'antd';

export default function CategoryTree({ categories, selectedCode, onSelect }) {
  const treeData = (categories || []).map((cat) => ({
    key: cat.code,
    title: `${cat.name} (${cat.filled_count}/${cat.file_count})`,
    children: (cat.subcategories || []).map((sub) => ({
      key: sub.code,
      title: `${sub.name} (${sub.filled_count}/${sub.file_count})`,
    })),
  }));

  return (
    <Tree
      treeData={treeData}
      selectedKeys={selectedCode ? [selectedCode] : []}
      onSelect={(keys) => onSelect(keys[0] || null)}
      defaultExpandAll
    />
  );
}