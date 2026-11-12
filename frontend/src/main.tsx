import { useEffect, useRef, useState, type FormEvent } from 'react'
import { createRoot } from 'react-dom/client'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './style.css'

type Source = { rank: number; title: string; url: string; status: 'Reviewed' | 'Snippet only' | 'Unavailable' }
type Article = { title: string; body: string; seo_title: string; meta_description: string }
type Config = { demo: boolean; demo_topic: string }
const stages = [
  ['search', 'Search Google'],
  ['review', 'Review sources'],
  ['draft', 'Draft article'],
  ['verify', 'Verify article'],
] as const
type StreamEvent =
  | { type: 'stage'; stage: typeof stages[number][0] }
  | { type: 'sources'; sources: Source[] }
  | { type: 'error'; message: string }
  | { type: 'result'; article: Article; count: number; within_target: boolean }
type Result = Extract<StreamEvent, { type: 'result' }>

function webUrl(value: string) {
  try {
    const parsed = new URL(value)
    return ['http:', 'https:'].includes(parsed.protocol) && !parsed.username && !parsed.password ? parsed.href : undefined
  } catch {
    return undefined
  }
}

function App() {
  const [config, setConfig] = useState<Config>()
  const [configError, setConfigError] = useState('')
  const [topic, setTopic] = useState('')
  const [running, setRunning] = useState(false)
  const busy = useRef(false)
  const [stage, setStage] = useState(-1)
  const [sources, setSources] = useState<Source[]>([])
  const [result, setResult] = useState<Result>()
  const [error, setError] = useState('')
  const [copyStatus, setCopyStatus] = useState('')
  const form = useRef<HTMLFormElement>(null)

  async function loadConfig() {
    setConfigError('')
    try {
      const response = await fetch('/api/config')
      if (!response.ok) throw new Error()
      setConfig(await response.json())
    } catch {
      setConfigError('Could not connect to the backend. Start FastAPI and reconnect.')
    }
  }
  useEffect(() => { void loadConfig() }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy.current || !config) return
    const data = Object.fromEntries(new FormData(event.currentTarget))
    const brief = { ...data, topic: (config.demo ? config.demo_topic : topic).trim() }
    if (brief.topic.length < 2) {
      setError('Enter a topic with at least two characters.')
      return
    }
    busy.current = true
    setRunning(true)
    setStage(0)
    setError('')
    setCopyStatus('')
    setSources([])
    setResult(undefined)
    try {
      const response = await fetch('/api/articles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(brief),
      })
      if (!response.ok || !response.body) {
        throw new Error(response.status === 422 ? 'Check the topic and the country and language codes.' : 'Could not start the article. Please retry.')
      }
      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
      let buffer = ''
      let terminal = false
      function handle(line: string) {
        if (!line.trim()) return
        const item = JSON.parse(line) as StreamEvent
        switch (item.type) {
          case 'stage': setStage(stages.findIndex(([key]) => key === item.stage)); break
          case 'sources': setSources(item.sources); break
          case 'result': setResult(item); terminal = true; break
          case 'error': setError(item.message); terminal = true; break
        }
      }
      while (true) {
        const chunk = await reader.read()
        if (chunk.done) break
        buffer += chunk.value
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        lines.forEach(handle)
      }
      handle(buffer)
      if (!terminal) throw new Error('The connection ended before the article finished. Please retry.')
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'The request failed. Please retry.')
    } finally {
      busy.current = false
      setRunning(false)
    }
  }

  const article = result?.article
  const markdown = article && [
    '# ' + article.title, article.body, '## Sources',
    ...sources.filter(source => source.status === 'Reviewed')
      .map(source => `- [${source.rank}] ${source.title} — ${source.url}`),
  ].join('\n\n')

  function download() {
    if (!markdown) return
    const url = URL.createObjectURL(new Blob([markdown], { type: 'text/markdown;charset=utf-8' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'article.md'
    anchor.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return <main>
    <header className="masthead"><div className="brand"><span aria-hidden="true">✦</span> Search to Article</div>
      {config && <span className="mode">{config.demo ? 'Demo mode' : 'Live mode'}</span>}
    </header>
    <section className="intro">
      <h1>Research and write an article</h1>
      <p>Review up to 10 organic Google results and turn the research into an article with citations.</p>
    </section>
    <section className="workspace">
      <form ref={form} className="card brief" onSubmit={submit}>
        <h2>Article brief</h2>
        {config?.demo && <p className="notice">Demo uses sample meal-prep results and a prepared article. Live mode accepts your own topic.</p>}
        <label>Topic or keyword<input name="topic" required maxLength={180} minLength={2}
          value={config?.demo ? config.demo_topic : topic} onChange={event => setTopic(event.target.value)}
          placeholder="e.g. How to plan a weekly meal prep routine" readOnly={config?.demo || running}/></label>
        {!config?.demo && <details><summary>Search and writing preferences</summary><fieldset disabled={running}>
          <label>Country code<input name="country" defaultValue="US" pattern="[A-Za-z]{2}" required /></label>
          <label>Language code<input name="language" defaultValue="en" pattern="[A-Za-z]{2}(-[A-Za-z]{2})?" required /></label>
          <label>Audience<input name="audience" maxLength={120} placeholder="e.g. First-time readers" /></label>
          <label>Tone<input name="tone" maxLength={80} defaultValue="Clear and conversational" required /></label>
        </fieldset></details>}
        <button className="primary" disabled={running || !config}>{running ? 'Working…' : config?.demo ? 'Run demo' : 'Generate article'}</button>
        {configError && <p role="alert">{configError} <button type="button" onClick={loadConfig}>Reconnect</button></p>}
      </form>
      <section className="card progress" aria-label="Research progress">
        <h2>Progress</h2>
        <ol aria-live="polite">{stages.map(([key, label], index) => {
          const status = result || index < stage ? 'Complete' : index === stage ? error ? 'Stopped' : 'In progress' : 'Pending'
          return <li key={key} data-status={status}><span>{label}</span><small>{status}</small></li>
        })}</ol>
      </section>
    </section>
    {error && <div className="notice error" role="alert">{error} <button type="button" onClick={() => form.current?.requestSubmit()}>Retry</button></div>}
    {(sources.length > 0 || result) && <section className="output">
      <div>
        {article && result && <article className="card article">
          <div className="actions">
            <span className="mode">{result.count} words</span>
            <button onClick={async () => {
              try { await navigator.clipboard.writeText(markdown ?? ''); setCopyStatus('Copied') }
              catch { setCopyStatus('Copy failed. Use Download Markdown.') }
            }}>Copy</button>
            <button onClick={download}>Download Markdown</button>
            <small role="status">{copyStatus}</small>
          </div>
          {!result.within_target && <p className="notice">The revised draft falls outside the 760–840 word target.</p>}
          <h2>{article.title}</h2>
          <Markdown skipHtml remarkPlugins={[remarkGfm]} disallowedElements={['img']} components={{
            a: ({children}) => <span>{children}</span>,
          }}>{article.body}</Markdown>
          <dl className="metadata"><dt>SEO title</dt><dd>{article.seo_title}</dd><dt>Meta description</dt><dd>{article.meta_description}</dd></dl>
        </article>}
      </div>
      <aside className="card sources">
        <h2>Search results</h2>
        <ol>{sources.map(source => {
          const url = webUrl(source.url)
          return <li key={source.rank} value={source.rank}>
            <strong>{source.title}</strong><span className="status" data-status={source.status}>{source.status}</span>
            {url ? <a href={url} target="_blank" rel="noreferrer">{source.url}</a> : <small>{source.url || 'URL unavailable'}</small>}
          </li>
        })}</ol>
      </aside>
    </section>}
  </main>
}

createRoot(document.getElementById('root')!).render(<App />)
