import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

async function parseBlueprint(text: string): Promise<any> {
  const API_BASE = 'http://localhost:8000';
  const res = await fetch(`${API_BASE}/api/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
    }
    throw new Error(detail);
  }
  return res.json();
}

async function formatBlueprint(text: string, format: string, stats: boolean): Promise<string> {
  const API_BASE = 'http://localhost:8000';
  const res = await fetch(`${API_BASE}/api/format`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, format, stats }),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
    }
    throw new Error(detail);
  }
  const data = await res.json();
  return data.result;
}

async function getExamples(): Promise<string[]> {
  const API_BASE = 'http://localhost:8000';
  const res = await fetch(`${API_BASE}/api/examples`);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
    }
    throw new Error(detail);
  }
  const data = await res.json();
  return data.examples;
}

async function getExample(name: string): Promise<string> {
  const API_BASE = 'http://localhost:8000';
  const res = await fetch(`${API_BASE}/api/examples/${name}`);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
    }
    throw new Error(detail);
  }
  const data = await res.json();
  return data.content;
}

function mockResponse(data: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    json: () => Promise.resolve(data),
  } as Response;
}

describe('parseBlueprint', () => {
  it('should successfully parse a blueprint text', async () => {
    const graphData = {
      entry_points: [{ id: 'node_0', label: 'On Begin Play', node_type: 'EventBeginPlay' }],
      all_nodes: {},
      data_flows: [],
      stats: { total_nodes: 1 },
    };
    mockFetch.mockResolvedValue(mockResponse(graphData));

    const result = await parseBlueprint('some text');
    expect(result).toEqual(graphData);
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/parse',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: 'some text' }),
      }),
    );
  });

  it('should throw on empty text error', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ detail: 'text must not be empty' }, 400),
    );

    await expect(parseBlueprint('')).rejects.toThrow('text must not be empty');
  });
});

describe('formatBlueprint', () => {
  it('should return formatted result', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ result: 'formatted output' }),
    );

    const result = await formatBlueprint('some text', 'plain', false);
    expect(result).toBe('formatted output');
  });

  it('should handle unknown format error', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ detail: 'Unknown format: invalid' }, 400),
    );

    await expect(formatBlueprint('text', 'invalid', false)).rejects.toThrow(
      'Unknown format: invalid',
    );
  });
});

describe('getExamples', () => {
  it('should return example names', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ examples: ['simple_event', 'branch_flow'] }),
    );

    const result = await getExamples();
    expect(result).toEqual(['simple_event', 'branch_flow']);
  });
});

describe('getExample', () => {
  it('should return example content', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ name: 'simple_event', content: 'Begin Object...' }),
    );

    const result = await getExample('simple_event');
    expect(result).toBe('Begin Object...');
  });

  it('should throw on not found', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ detail: "Example 'nonexistent' not found" }, 404),
    );

    await expect(getExample('nonexistent')).rejects.toThrow(
      "Example 'nonexistent' not found",
    );
  });
});