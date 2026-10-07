const form = document.querySelector('#run-form');
const badge = document.querySelector('#badge');
const button = document.querySelector('#run-button');
const errorBox = document.querySelector('#error');
const eventList = document.querySelector('#events');
let activeRun = null;

function setStatus(text, kind) { badge.textContent = text; badge.className = `badge ${kind}`; }
function showError(message) { errorBox.textContent = message; errorBox.hidden = false; button.disabled = false; setStatus('ERROR', 'error'); }
function addEvent(item) {
  const li = document.createElement('li');
  const index = document.createElement('div'); index.className = 'event-index'; index.textContent = String(eventList.children.length + 1).padStart(2, '0');
  const body = document.createElement('div');
  const agent = document.createElement('div'); agent.className = 'event-agent'; agent.textContent = item.agent || 'System';
  const message = document.createElement('div'); message.className = 'event-message'; message.textContent = item.message || '';
  const detail = document.createElement('div'); detail.className = 'event-detail'; detail.textContent = item.detail || '';
  body.append(agent, message, detail); li.append(index, body); eventList.append(li);
  eventList.scrollTop = eventList.scrollHeight;
}
function fillList(id, entries) {
  const list = document.querySelector(id); list.replaceChildren();
  for (const entry of entries || []) { const li = document.createElement('li'); li.textContent = entry; list.append(li); }
}
function showDelivery(result) {
  document.querySelector('#delivery').hidden = false;
  document.querySelector('#verdict').textContent = result.verdict === 'review_ready' ? 'REVIEW READY' : 'NEEDS REVISION';
  document.querySelector('#summary').textContent = result.summary;
  document.querySelector('#code').textContent = result.python_code;
  document.querySelector('#tests').textContent = result.test_code;
  fillList('#research-notes', result.research_notes);
  fillList('#review-notes', result.review_notes);
  const sources = document.querySelector('#sources'); sources.replaceChildren();
  for (const url of result.source_urls || []) {
    if (!url.startsWith('https://docs.python.org/3/library/')) continue;
    const link = document.createElement('a'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = url; sources.append(link);
  }
  document.querySelector('#checks').textContent = Object.entries(result.syntax_checks || {}).map(([name, check]) => `${name}: ${check.ok ? 'syntax OK' : check.detail}`).join(' · ');
  document.querySelector('#delivery').scrollIntoView({behavior: 'smooth', block: 'start'});
}
async function poll(runId) {
  let shown = 0;
  while (activeRun === runId) {
    try {
      const response = await fetch(`/api/runs/${runId}`, {cache: 'no-store'});
      const run = await response.json();
      if (!response.ok) throw new Error(run.error || 'Could not get run status');
      for (const item of run.events.slice(shown)) addEvent(item);
      shown = run.events.length;
      if (run.status === 'complete') { showDelivery(run.result); setStatus('COMPLETE', 'complete'); button.disabled = false; return; }
      if (run.status === 'error') { addEvent({agent: 'System', message: run.error}); showError(run.error); return; }
    } catch (exc) { showError(exc.message); return; }
    await new Promise(resolve => setTimeout(resolve, 1800));
  }
}
form.addEventListener('submit', async event => {
  event.preventDefault(); errorBox.hidden = true; button.disabled = true; setStatus('RUNNING', 'running');
  document.querySelector('#empty').hidden = true; document.querySelector('#live').hidden = false; document.querySelector('#delivery').hidden = true; eventList.replaceChildren();
  const data = new FormData(form);
  const body = {idea: data.get('idea').trim(), model: data.get('model'), api_key: data.get('api_key').trim() || null};
  try {
    const response = await fetch('/api/runs', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not start crew');
    activeRun = result.id;
    addEvent({agent: 'System', message: 'Request accepted', detail: 'Local server started a CrewAI job'});
    poll(result.id);
  } catch (exc) { showError(exc.message); }
});
document.querySelector('#sample').addEventListener('click', () => {
  document.querySelector('#idea').value = 'Create a Python function that turns a customer name into a URL-safe slug. Add unittest cases for accents, punctuation, repeated spaces, and empty input.';
});
document.querySelectorAll('[data-copy]').forEach(control => control.addEventListener('click', async () => {
  const target = control.dataset.copy === 'code' ? '#code' : '#tests';
  await navigator.clipboard.writeText(document.querySelector(target).textContent);
  const old = control.textContent; control.textContent = 'Copied ✓'; setTimeout(() => control.textContent = old, 1800);
}));
fetch('/api/config').then(response => response.json()).then(config => {
  document.querySelector('#model').value = config.model;
  if (config.key_configured) document.querySelector('#key-hint').textContent = 'A Gemini key is already set for the server. You can leave this field empty.';
});
