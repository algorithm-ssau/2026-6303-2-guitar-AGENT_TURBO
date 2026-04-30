/**
 * Изолированный компонент для просмотра demo-сценариев чата.
 * Не подключается к App.tsx и не меняет production flow.
 */
import React, { useState } from 'react';
import { MessageList } from '../components/MessageList';
import { ErrorMessage } from '../components/ErrorMessage';
import {
  emptyChatDemo,
  consultationDemo,
  searchResultsDemo,
  emptyResultsDemo,
  errorDemo,
  longTextDemo,
} from './demoMessages';

interface Scenario {
  key: string;
  label: string;
}

const scenarios: Scenario[] = [
  { key: 'emptyChat', label: 'Пустой чат' },
  { key: 'consultation', label: 'Консультация' },
  { key: 'searchResults', label: 'Результаты поиска' },
  { key: 'emptyResults', label: 'Нет результатов' },
  { key: 'error', label: 'Ошибка' },
  { key: 'longText', label: 'Длинный текст' },
];

const scenarioData: Record<string, { messages: React.ComponentProps<typeof MessageList>['messages']; error?: string | null }> = {
  emptyChat: { messages: emptyChatDemo.messages },
  consultation: { messages: consultationDemo.messages },
  searchResults: { messages: searchResultsDemo.messages },
  emptyResults: { messages: emptyResultsDemo.messages },
  error: { messages: errorDemo.messages, error: errorDemo.error },
  longText: { messages: longTextDemo.messages },
};

export const ChatDemoScenarios: React.FC = () => {
  const [activeScenario, setActiveScenario] = useState<string>('emptyChat');

  const data = scenarioData[activeScenario];

  return (
    <div className="chat-demo-scenarios" style={{
      display: 'flex',
      height: '100vh',
      fontFamily: 'system-ui, -apple-system, sans-serif',
    }}>
      {/* Панель сценариев */}
      <aside className="chat-demo-sidebar" style={{
        width: '220px',
        backgroundColor: 'var(--bg-card, #1a1a2e)',
        borderRight: '1px solid var(--border, #333)',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        overflowY: 'auto',
      }}>
        <h3 style={{
          margin: '0 0 12px',
          fontSize: '14px',
          fontWeight: 600,
          color: 'var(--text-main, #e0e0e0)',
        }}>
          Demo сценарии
        </h3>
        {scenarios.map((scenario) => (
          <button
            key={scenario.key}
            data-testid={`scenario-btn-${scenario.key}`}
            onClick={() => setActiveScenario(scenario.key)}
            style={{
              padding: '10px 14px',
              textAlign: 'left',
              border: '1px solid',
              borderColor: activeScenario === scenario.key
                ? 'var(--accent, #6366f1)'
                : 'var(--border, #333)',
              borderRadius: '8px',
              backgroundColor: activeScenario === scenario.key
                ? 'var(--accent, #6366f1)'
                : 'transparent',
              color: activeScenario === scenario.key
                ? '#fff'
                : 'var(--text-main, #e0e0e0)',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: activeScenario === scenario.key ? 600 : 400,
              transition: 'all 0.15s',
            }}
          >
            {scenario.label}
          </button>
        ))}
      </aside>

      {/* Область превью */}
      <main className="chat-demo-preview" style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--bg-main, #0f0f23)',
        overflow: 'hidden',
      }}>
        <div className="chat-demo-header" style={{
          padding: '12px 20px',
          borderBottom: '1px solid var(--border, #333)',
          fontSize: '13px',
          color: 'var(--text-dim, #888)',
        }}>
          Превью: <strong style={{ color: 'var(--text-main, #e0e0e0)' }}>
            {scenarios.find((s) => s.key === activeScenario)?.label}
          </strong>
        </div>

        <div className="chat-demo-content" style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
        }}>
          {data.messages.length === 0 && !data.error && (
            <MessageList messages={data.messages} />
          )}

          {data.messages.length > 0 && (
            <MessageList messages={data.messages} />
          )}

          {data.error && (
            <ErrorMessage message={data.error} />
          )}
        </div>
      </main>
    </div>
  );
};
