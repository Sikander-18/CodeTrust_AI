import { useState, useEffect, useRef } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import styles from './TabsSection.module.css'

const AGENT_CLASS = {
  'Architect':     styles.agentArchitect,
  'Developer':     styles.agentDeveloper,
  'Test Engineer': styles.agentTestEng,
  'Sandbox':       styles.agentSandbox,
  'Evaluator':     styles.agentEvaluator,
  'Orchestrator':  styles.agentOrchestrator,
}

const TABS = ['🔬 Test Suite', '📋 Execution Output', '📊 Final Verdict', '📜 Agent Logs']

export default function TabsSection({ tests, execution, report, logs, metrics }) {
  const [active, setActive] = useState(3) // default: Agent Logs
  const logsRef = useRef(null)

  // Auto-scroll logs when new ones arrive
  useEffect(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight
    }
  }, [logs])

  // Switch to Agent Logs when pipeline starts (first log arrives)
  useEffect(() => {
    if (logs.length === 1) setActive(3)
  }, [logs.length])

  return (
    <div className={styles.section}>
      {/* Tab bar */}
      <div className={styles.tabBar}>
        {TABS.map((tab, i) => (
          <button
            key={i}
            className={`${styles.tabBtn} ${active === i ? styles.tabActive : ''}`}
            onClick={() => setActive(i)}
          >
            {tab}
            {i === 3 && logs.length > 0 && (
              <span className={styles.badge}>{logs.length}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab: Test Suite */}
      {active === 0 && (
        <div className={styles.tabContent}>
          {tests ? (
            <SyntaxHighlighter
              language="python"
              style={vscDarkPlus}
              customStyle={{
                margin: 0, borderRadius: '8px',
                background: 'var(--surface-container-lowest)',
                fontSize: '12.5px', maxHeight: '360px',
                overflowY: 'auto', padding: '16px',
              }}
              showLineNumbers
              lineNumberStyle={{ color: '#414752', minWidth: '2.5em' }}
            >
              {tests}
            </SyntaxHighlighter>
          ) : <EmptyTab icon="🔬" text="Test suite will appear after the pipeline runs." />}
        </div>
      )}

      {/* Tab: Execution Output */}
      {active === 1 && (
        <div className={styles.tabContent}>
          <div className={styles.execOutput}>
            {execution.stderr || execution.stdout ? (
              <>
                {execution.stdout && (
                  <div>
                    <span className={styles.logSection}>STDOUT</span>
                    <pre className={styles.logPre}>{execution.stdout || '(empty)'}</pre>
                  </div>
                )}
                <div>
                  <span className={styles.logSection}>STDERR</span>
                  <pre className={styles.logPre}>
                    {execution.stderr.split('\n').map((line, i) => {
                      const cls = /FAIL|ERROR|AssertionError/.test(line) ? styles.lineFail
                                : /^ok|passed|\.+$/.test(line) ? styles.linePass
                                : ''
                      return <span key={i} className={cls}>{line}{'\n'}</span>
                    })}
                  </pre>
                </div>
              </>
            ) : <EmptyTab icon="📋" text="Execution output will stream here during the run." />}
          </div>
        </div>
      )}

      {/* Tab: Final Verdict */}
      {active === 2 && (
        <div className={styles.tabContent}>
          {report ? (
            <div className={styles.verdict}>
              <div className={`${styles.verdictHeader} ${report.verdict === 'APPROVED' ? styles.verdictOk : styles.verdictBad}`}>
                <span>{report.verdict === 'APPROVED' ? '✅' : '❌'}</span>
                <span>{report.verdict}</span>
              </div>
              <p className={styles.verdictBody}>{report.feedback}</p>
              <div className={styles.verdictGrid}>
                <VerdictItem label="Edge Case Resilience" value={report.edge_case_resilience} />
                <VerdictItem label="Time Complexity" value={report.time_complexity} />
                <VerdictItem label="Space Complexity" value={report.space_complexity} />
                <VerdictItem label="Pylint Score" value={`${metrics?.pylint_score ?? '--'}/10`} highlight />
              </div>
            </div>
          ) : <EmptyTab icon="📊" text="Final verdict will appear after evaluation completes." />}
        </div>
      )}

      {/* Tab: Agent Logs */}
      {active === 3 && (
        <div className={styles.tabContent}>
          <div className={styles.logList} ref={logsRef}>
            {logs.length === 0 ? (
              <EmptyTab icon="📜" text="Agent logs will stream here in real time." />
            ) : logs.map((log, i) => (
              <div key={i} className={styles.logRow}>
                <span className={styles.logTime}>{log.timestamp}</span>
                <span className={`${styles.agentBadge} ${AGENT_CLASS[log.agent] ?? styles.agentOrchestrator}`}>
                  {log.agent}
                </span>
                <span className={styles.logMsg}>{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function VerdictItem({ label, value, highlight }) {
  return (
    <div className={styles.verdictItem}>
      <div className={styles.verdictItemLabel}>{label}</div>
      <div className={`${styles.verdictItemValue} ${highlight ? styles.verdictItemHighlight : ''}`}>
        {value ?? '--'}
      </div>
    </div>
  )
}

function EmptyTab({ icon, text }) {
  return (
    <div className={styles.emptyTab}>
      <span className={styles.emptyIcon}>{icon}</span>
      <p>{text}</p>
    </div>
  )
}
