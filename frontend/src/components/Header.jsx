import styles from './Header.module.css'

export default function Header({ isRunning }) {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <div className={styles.icon}>🧪</div>
        <div>
          <div className={styles.title}>Agentic Trust Laboratory</div>
          <div className={styles.subtitle}>Verifying AI-Generated Code Through Multi-Agent Systems</div>
        </div>
      </div>
      <div className={styles.badge}>
        <span className={`${styles.dot} ${isRunning ? styles.dotRunning : styles.dotIdle}`} />
        {isRunning ? 'Running pipeline…' : 'Groq · llama-3.3-70b'}
      </div>
    </header>
  )
}
