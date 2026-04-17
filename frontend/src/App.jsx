import { usePipeline } from './hooks/usePipeline'
import Header from './components/Header'
import InputPanel from './components/InputPanel'
import CodePanel from './components/CodePanel'
import MetricsPanel from './components/MetricsPanel'
import TabsSection from './components/TabsSection'
import styles from './App.module.css'

export default function App() {
  const { state, run } = usePipeline()

  return (
    <div className={styles.root}>
      <Header isRunning={state.isRunning} />

      <main className={styles.main}>
        {/* Input */}
        <InputPanel
          onRun={run}
          isRunning={state.isRunning}
          progress={state.progress}
        />

        {/* Split: Code + Metrics */}
        <div className={styles.split}>
          <CodePanel code={state.code} />
          <MetricsPanel
            report={state.report}
            metrics={state.metrics}
            iterations={state.iterations}
          />
        </div>

        {/* Tabs */}
        <TabsSection
          tests={state.tests}
          execution={state.execution}
          report={state.report}
          logs={state.logs}
          metrics={state.metrics}
        />
      </main>

      <footer className={styles.footer}>
        Agentic Trust Laboratory &nbsp;·&nbsp; Powered by Groq llama-3.3-70b ⚡
      </footer>
    </div>
  )
}
