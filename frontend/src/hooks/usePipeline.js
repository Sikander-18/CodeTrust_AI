import { useState, useCallback, useRef } from 'react'

const API_BASE = ''  // proxied by Vite to http://localhost:8000

const INITIAL_STATE = {
  isRunning: false,
  code: '',
  tests: '',
  execution: { stdout: '', stderr: '' },
  metrics: null,
  report: null,
  logs: [],
  iterations: { current: 1, total: 3 },
  progress: { pct: 0, label: 'Ready' },
  done: false,
}

const STEP_PCT = {
  architect: 15, developer: 35, test_engineer: 55, sandbox: 70, evaluator: 90,
}

export function usePipeline() {
  const [state, setState] = useState(INITIAL_STATE)
  const abortRef = useRef(null)

  const update = useCallback((patch) =>
    setState(prev => ({ ...prev, ...patch })), [])

  const run = useCallback(async (problem, maxRetries) => {
    // Cancel any existing stream
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({
      ...INITIAL_STATE,
      isRunning: true,
      iterations: { current: 1, total: maxRetries },
      progress: { pct: 2, label: 'Connecting to pipeline…' },
    })

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem, max_retries: maxRetries }),
        signal: controller.signal,
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue
          let event
          try { event = JSON.parse(raw) } catch { continue }
          handleEvent(event, maxRetries, setState)
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setState(prev => ({
          ...prev,
          isRunning: false,
          logs: [...prev.logs, {
            timestamp: new Date().toTimeString().slice(0, 8),
            agent: 'Orchestrator',
            message: `❌ Connection error: ${err.message}`,
          }],
          progress: { pct: 0, label: 'Connection failed — is backend running?' },
        }))
      }
    }
  }, [])

  const stop = useCallback(() => {
    abortRef.current?.abort()
    setState(prev => ({ ...prev, isRunning: false }))
  }, [])

  return { state, run, stop }
}

function handleEvent(event, maxRetries, setState) {
  switch (event.type) {
    case 'log':
      setState(prev => ({
        ...prev,
        logs: [...prev.logs, {
          timestamp: event.timestamp,
          agent: event.agent,
          message: event.message,
        }],
      }))
      break

    case 'progress': {
      const basePct = STEP_PCT[event.step] ?? 50
      const iterOffset = (event.iteration - 1) / maxRetries
      const pct = Math.min(Math.round((iterOffset + basePct / 100 / maxRetries) * 100), 95)
      setState(prev => ({
        ...prev,
        iterations: { current: event.iteration, total: maxRetries },
        progress: { pct, label: `Iteration ${event.iteration}/${maxRetries} — ${event.step.replace('_', ' ')}…` },
      }))
      break
    }

    case 'code':
      setState(prev => ({ ...prev, code: event.content }))
      break

    case 'tests':
      setState(prev => ({ ...prev, tests: event.content }))
      break

    case 'execution':
      setState(prev => ({ ...prev, execution: { stdout: event.stdout, stderr: event.stderr } }))
      break

    case 'metrics':
      setState(prev => ({ ...prev, metrics: event.data }))
      break

    case 'report':
      setState(prev => ({ ...prev, report: event.data }))
      break

    case 'done':
      setState(prev => ({
        ...prev,
        isRunning: false,
        done: true,
        progress: { pct: 100, label: 'Analysis complete ✓' },
      }))
      break

    case 'error':
      setState(prev => ({
        ...prev,
        logs: [...prev.logs, {
          timestamp: new Date().toTimeString().slice(0, 8),
          agent: 'Orchestrator',
          message: `⚠️ ${event.message}`,
        }],
      }))
      break

    default:
      break
  }
}
