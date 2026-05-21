export const SESSION_QUERY_PARAM = 'session';

export function readSessionIdFromUrl(): { sessionId: number | null; error: string | null } {
  const rawSessionId = new URLSearchParams(window.location.search).get(SESSION_QUERY_PARAM);
  if (!rawSessionId) {
    return { sessionId: null, error: null };
  }

  if (!/^\d+$/.test(rawSessionId)) {
    return { sessionId: null, error: 'Некорректная ссылка на чат' };
  }

  return { sessionId: Number(rawSessionId), error: null };
}

export function updateSessionUrl(sessionId: number | null, replace = false) {
  const url = new URL(window.location.href);

  if (sessionId === null) {
    url.searchParams.delete(SESSION_QUERY_PARAM);
  } else {
    url.searchParams.set(SESSION_QUERY_PARAM, String(sessionId));
  }

  const nextUrl = `${url.pathname}${url.search}${url.hash}`;
  const writeHistory = replace ? window.history.replaceState : window.history.pushState;
  writeHistory.call(window.history, {}, '', nextUrl);
}
