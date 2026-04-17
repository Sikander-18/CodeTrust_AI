import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import styles from './CodePanel.module.css'

export default function CodePanel({ code }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    if (!code) return
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.title}>
          <span>🧬</span>
          <span>GENERATED CODE</span>
          <span className={styles.tag}>Python</span>
        </div>
        <button className={styles.copyBtn} onClick={handleCopy} disabled={!code}>
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>

      <div className={styles.body}>
        {code ? (
          <SyntaxHighlighter
            language="python"
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              borderRadius: '8px',
              background: 'var(--surface-container-lowest)',
              fontSize: '13px',
              maxHeight: '520px',
              overflowY: 'auto',
              padding: '16px',
            }}
            showLineNumbers
            lineNumberStyle={{ color: '#414752', minWidth: '2.5em' }}
          >
            {code}
          </SyntaxHighlighter>
        ) : (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>⌛</span>
            <p>Generated code will appear here once the pipeline runs.</p>
          </div>
        )}
      </div>
    </div>
  )
}
