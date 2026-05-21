import { GuitarResult, Message, ChatMode } from './types';

interface RawResult {
  id?: string;
  title: string;
  price?: number;
  currency?: string;
  imageUrl?: string;
  image_url?: string;
  listingUrl?: string;
  listing_url?: string;
}

interface RawHistoryItem {
  id: number;
  mode: string;
  results?: RawResult[] | null;
  userQuery: string;
  createdAt: string;
  answer?: string | null;
  searchParams?: Record<string, unknown> | null;
}

export function normalizeResult(item: RawResult): GuitarResult {
  return {
    id: item.id,
    title: item.title,
    price: item.price,
    currency: item.currency,
    imageUrl: item.imageUrl || item.image_url,
    listingUrl: item.listingUrl || item.listing_url,
  };
}

export function historyToMessages(items: RawHistoryItem[]): Message[] {
  const messages: Message[] = [];
  for (const item of items) {
    const normalizedResults = item.mode === 'search'
      ? (item.results || []).map((result) => normalizeResult(result))
      : undefined;

    messages.push({
      id: `hist-user-${item.id}`,
      role: 'user',
      content: item.userQuery,
      timestamp: new Date(item.createdAt),
    });
    messages.push({
      id: `hist-agent-${item.id}`,
      role: 'agent',
      content: item.mode !== 'search'
        ? (item.answer || '')
        : (item.answer || `Найдено гитар: ${(normalizedResults || []).length}`),
      timestamp: new Date(item.createdAt),
      mode: item.mode as ChatMode,
      results: normalizedResults,
      searchParams: item.searchParams || null,
    });
  }
  return messages;
}
