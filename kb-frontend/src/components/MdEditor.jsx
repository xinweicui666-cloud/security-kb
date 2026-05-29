import { useRef } from 'react';
import Editor from '@monaco-editor/react';

export default function MdEditor({ value, onChange }) {
  const editorRef = useRef(null);

  return (
    <Editor
      height="600px"
      language="markdown"
      theme="vs"
      value={value}
      onChange={(v) => onChange(v || '')}
      onMount={(editor) => { editorRef.current = editor; }}
      options={{
        minimap: { enabled: false },
        wordWrap: 'on',
        fontSize: 14,
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
      }}
    />
  );
}