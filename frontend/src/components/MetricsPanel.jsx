import styles from './MetricsPanel.module.css'

/* ── Sub-components ──────────────────────────────────────────────── */

function TrustHero({ report }) {
  const score = report?.trust_score ?? null
  const grade = report?.trust_grade ?? null
  const verdict = report?.verdict ?? null
  const approved = verdict === 'APPROVED'

  const color =
    score === null ? 'var(--outline)' :
    score >= 90    ? 'var(--tertiary)' :
    score >= 75    ? 'var(--primary-container)' :
    score >= 60    ? 'var(--amber)' :
                    'var(--error)'

  return (
    <div className={styles.trustCard}>
      <div className={styles.trustGlow} style={{ background: `radial-gradient(circle at 50% 0%, ${color}10 0%, transparent 70%)` }} />
      <div className={styles.trustLabel}>TRUST SCORE</div>
      <div className={styles.trustScore} style={{ color }}>
        {score ?? '--'}<span className={styles.trustMax}>/100</span>
      </div>
      {grade && (
        <div className={styles.trustGrade} style={{ borderColor: color, color }}>
          {grade}
        </div>
      )}
      <div className={styles.trustBarTrack}>
        <div
          className={styles.trustBarFill}
          style={{ width: `${score ?? 0}%`, background: `linear-gradient(90deg, ${color}, color-mix(in srgb, ${color} 70%, transparent))` }}
        />
      </div>
      {verdict && (
        <div className={`${styles.verdictPill} ${approved ? styles.verdictApproved : styles.verdictFail}`}>
          {approved ? '✅ APPROVED' : '❌ NEEDS REFINEMENT'}
        </div>
      )}
      {!verdict && (
        <div className={styles.verdictPill} style={{ color: 'var(--outline)', borderColor: 'var(--outline-variant)', background: 'transparent' }}>
          — awaiting result —
        </div>
      )}
    </div>
  )
}

function MetricCard({ label, value, color }) {
  return (
    <div className={styles.metricCard}>
      <div className={styles.metricLabel}>{label}</div>
      <div className={styles.metricValue} style={color ? { color } : {}}>
        {value ?? '--'}
      </div>
    </div>
  )
}

function AdvCard({ report, metrics }) {
  const passed = report?.passed_tests ?? metrics?.passed ?? null
  const total = report?.total_tests ?? metrics?.total ?? null
  const secure = passed !== null && total !== null && passed / Math.max(total, 1) > 0.8

  return (
    <div className={styles.advCard}>
      <div className={`${styles.advIcon} ${secure ? styles.advSecure : styles.advVuln}`}>
        {passed === null ? '⏳' : secure ? '🛡️' : '❌'}
      </div>
      <div>
        <div className={styles.advLabel}>ADVERSARIAL DEFENSE</div>
        <div className={`${styles.advValue} ${secure ? styles.advSecure : styles.advVuln} ${passed === null ? styles.advPending : ''}`}>
          {passed === null
            ? 'Awaiting result…'
            : secure
              ? 'Secure — all adversarial tests passed'
              : `Vulnerable — ${total - passed} edge case(s) failed`}
        </div>
      </div>
    </div>
  )
}

function LoopProgress({ iterations }) {
  const { current, total } = iterations
  return (
    <div className={styles.loopCard}>
      <div className={styles.loopLabel}>LOOP PROGRESS</div>
      <div className={styles.dots}>
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            className={`${styles.dot} ${i < current - 1 ? styles.dotDone : i === current - 1 ? styles.dotActive : styles.dotPending}`}
          />
        ))}
      </div>
    </div>
  )
}

/* ── Main export ─────────────────────────────────────────────────── */
export default function MetricsPanel({ report, metrics, iterations }) {
  return (
    <div className={styles.panel}>
      <TrustHero report={report} />

      <div className={styles.grid}>
        <MetricCard
          label="Tests Passed"
          value={metrics ? `${metrics.passed}/${metrics.total}` : null}
          color="var(--tertiary)"
        />
        <MetricCard
          label="Pylint Score"
          value={metrics ? `${metrics.pylint_score}/10` : null}
          color="var(--primary-container)"
        />
        <MetricCard
          label="Time Complexity"
          value={report?.time_complexity ?? null}
          color="var(--secondary)"
        />
        <MetricCard
          label="Space Complexity"
          value={report?.space_complexity ?? null}
          color={null}
        />
        <MetricCard
          label="Complexity Grade"
          value={metrics?.complexity_grade ?? null}
          color="var(--tertiary)"
        />
        <MetricCard
          label="Iterations"
          value={`${iterations.current}/${iterations.total}`}
          color={null}
        />
      </div>

      <AdvCard report={report} metrics={metrics} />
      <LoopProgress iterations={iterations} />
    </div>
  )
}
