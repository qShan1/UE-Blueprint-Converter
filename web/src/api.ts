const API_BASE = 'http://localhost:8000';

async function handleError(res: Response): Promise<never> {
  let detail = res.statusText;
  try {
    const body = await res.json();
    if (body.detail) detail = body.detail;
  } catch {
  }
  throw new Error(detail);
}

export async function parseBlueprint(text: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) await handleError(res);
  return res.json();
}

export async function formatBlueprint(text: string, format: string, stats: boolean): Promise<string> {
  const res = await fetch(`${API_BASE}/api/format`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, format, stats }),
  });
  if (!res.ok) await handleError(res);
  const data = await res.json();
  return data.result;
}

export async function getExamples(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/examples`);
  if (!res.ok) await handleError(res);
  const data = await res.json();
  return data.examples;
}

export async function getExample(name: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/examples/${name}`);
  if (!res.ok) await handleError(res);
  const data = await res.json();
  return data.content;
}