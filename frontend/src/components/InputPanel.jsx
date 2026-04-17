import { useState, useRef } from 'react'
import styles from './InputPanel.module.css'

export default function InputPanel({ onRun, isRunning, progress }) {
  const [problem, setProblem] = useState('')
  const [maxRetries, setMaxRetries] = useState(3)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!problem.trim() || isRunning) return
    onRun(problem, maxRetries)
  }

  const stepLabels = {
    architect: 'Architect',
    developer: 'Developer',
    test_engineer: 'Test Engineer',
    sandbox: 'Sandbox',
    evaluator: 'Evaluator',
  }

  return (
    <div className={styles.panel}>
      <form onSubmit={handleSubmit}>
        <div className={styles.label}>PROBLEM STATEMENT</div>
        <div className={styles.row}>
          <textarea
            className={styles.textarea}
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
            placeholder="Describe a DSA problem… e.g. Design an LFU Cache with O(1) get and put."
            disabled={isRunning}
          />
          <div className={styles.controls}>
            <label className={styles.retryLabel}>
              <span>Max Retries</span>
              <input
                type="number"
                className={styles.retryInput}
                value={maxRetries}
                min={1}
                max={5}
                onChange={(e) => setMaxRetries(parseInt(e.target.value) || 3)}
                disabled={isRunning}
              />
            </label>
            <button
              type="submit"
              className={`${styles.btn} ${isRunning ? styles.btnRunning : ''}`}
              disabled={isRunning}
            >
              {isRunning ? (
                <>
                  <span className={styles.spinner} />
                  Running…
                </>
              ) : 'Generate & Verify'}
            </button>
          </div>
        </div>
      </form>

      {/* Progress bar — always rendered, animated in when running */}
      <div className={`${styles.progressWrap} ${isRunning || progress.pct === 100 ? styles.progressVisible : ''}`}>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${progress.pct}%` }}
          />
        </div>
        <div className={styles.progressMeta}>
          <span>{progress.label}</span>
          <span className={styles.progressPct}>{progress.pct}%</span>
        </div>
      </div>
    </div>
  )
}
