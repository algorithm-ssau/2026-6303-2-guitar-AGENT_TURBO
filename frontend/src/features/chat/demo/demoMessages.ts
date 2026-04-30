/**
 * Demo fixtures для тестирования состояний чата без backend
 */
import type { Message, GuitarResult, ChatState } from '../types';

/** Генератор уникальных ID для демо-сообщений */
let demoIdCounter = 0;
const demoId = (): string => `demo-${++demoIdCounter}`;

const now = new Date();

/**
 * Сценарий: пустой чат (welcome screen)
 */
export const emptyChatDemo: { messages: Message[] } = {
  messages: [],
};

/**
 * Сценарий: консультация — вопрос и ответ агента
 */
export const consultationDemo: { messages: Message[] } = {
  messages: [
    {
      id: demoId(),
      role: 'user',
      content: 'В чём разница между синглами и хамбакерами?',
      timestamp: new Date(now.getTime() - 60000),
    } as Message,
    {
      id: demoId(),
      role: 'agent',
      content: `**Синглы** (single-coil) и **хамбакеры** (humbucker) — два основных типа звукоснимателей:

### Синглы
- Яркий, чистый, «стеклянный» звук
- Характерны для Fender Stratocaster и Telecaster
- Идеальны для блюза, фанка, кантри, инди-рока
- Фонят (ловят электромагнитные помехи)

### Хамбакеры
- Два катушки, включённые в противофазе — шум подавляется
- Более тёплый, жирный, мощный звук
- Характерны для Gibson Les Paul, SG
- Отлично подходят для рока, металла, джаза

**Комбо-гитары** (HSS, HSH) позволяют переключаться между типами, давая максимальную универсальность.`,
      timestamp: now,
      mode: 'consultation',
    } as Message,
  ],
};

/**
 * Сценарий: поиск с результатами — минимум 3 гитары
 */
export const searchResultsDemo: { messages: Message[] } = {
  messages: [
    {
      id: demoId(),
      role: 'user',
      content: 'Хочу телекастер с ярким звуком, до $600',
      timestamp: new Date(now.getTime() - 120000),
    } as Message,
    {
      id: demoId(),
      role: 'agent',
      content: 'Нашёл несколько отличных вариантов на Reverb:',
      timestamp: new Date(now.getTime() - 60000),
      mode: 'search',
      parsedParams: {
        type: 'Telecaster',
        budget: '600',
        brand: undefined,
        tags: ['bright sound'],
      },
      results: [
        {
          id: 'guitar-1',
          title: 'Fender Player Telecaster — Polar White',
          price: 499,
          currency: 'USD',
          imageUrl: 'https://cdn.reverb.com/image/upload/fender-player-tele.jpg',
          listingUrl: 'https://reverb.com/item/fender-player-telecaster-polar-white',
        } as GuitarResult,
        {
          id: 'guitar-2',
          title: 'Squier Classic Vibe \u201850s Telecaster — Butterscotch Blonde',
          price: 399,
          currency: 'USD',
          imageUrl: 'https://cdn.reverb.com/image/upload/squier-classic-vibe-50s-tele.jpg',
          listingUrl: 'https://reverb.com/item/squier-classic-vibe-50s-telecaster',
        } as GuitarResult,
        {
          id: 'guitar-3',
          title: 'Fender Vintera II \u201860s Telecaster — Olympic White',
          price: 599,
          currency: 'USD',
          imageUrl: 'https://cdn.reverb.com/image/upload/fender-vintera-60s-tele.jpg',
          listingUrl: 'https://reverb.com/item/fender-vintera-ii-60s-telecaster',
        } as GuitarResult,
        {
          id: 'guitar-4',
          title: 'G&L ASAT Classic — Sunburst',
          price: 549,
          currency: 'USD',
          imageUrl: 'https://cdn.reverb.com/image/upload/gl-asat-classic.jpg',
          listingUrl: 'https://reverb.com/item/gl-asat-classic-sunburst',
        } as GuitarResult,
      ],
    } as Message,
  ],
};

/**
 * Сценарий: поиск без результатов
 */
export const emptyResultsDemo: { messages: Message[] } = {
  messages: [
    {
      id: demoId(),
      role: 'user',
      content: 'Ищу Gibson Les Paul Custom 1959 года, до $500',
      timestamp: new Date(now.getTime() - 120000),
    } as Message,
    {
      id: demoId(),
      role: 'agent',
      content: 'По вашему запросу ничего не найдено на Reverb.',
      timestamp: new Date(now.getTime() - 60000),
      mode: 'search',
      parsedParams: {
        type: 'Les Paul Custom',
        budget: '500',
        brand: 'Gibson',
        tags: ['1959'],
      },
      results: [],
    } as Message,
  ],
};

/**
 * Сценарий: ошибка подключения
 */
export const errorDemo: ChatState = {
  messages: [
    {
      id: demoId(),
      role: 'user',
      content: 'Покажи стратокастеры до $800',
      timestamp: new Date(now.getTime() - 60000),
    } as Message,
  ],
  isLoading: false,
  error: 'Ошибка подключения к серверу. Проверьте соединение и попробуйте снова.',
};

/**
 * Сценарий: очень длинный текст ответа
 */
export const longTextDemo: { messages: Message[] } = {
  messages: [
    {
      id: demoId(),
      role: 'user',
      content: 'Расскажи полную историю электрогитары',
      timestamp: new Date(now.getTime() - 300000),
    } as Message,
    {
      id: demoId(),
      role: 'agent',
      content: `История электрогитары — это захватывающее путешествие через почти столетие музыкальной эволюции. Всё началось в 1930-х годах, когда музыканты джазовых оркестров столкнулись с проблемой: акустические гитары просто не могли конкурировать по громкости с духовыми инструментами и ударными в больших залах.

**Первые эксперименты (1931–1935)**

В 1931 году Джордж Бошамп и Адольф Рикенбакер создали первую коммерчески успешную электрогитару — «Frying Pan» (Сковородка), названную так за характерную форму. Это была гавайская гитара с электромагнитным звукоснимателем, которая звучала громче и могла конкурировать с другими инструментами в ансамбле.

Параллельно с этим компания Gibson начала собственные эксперименты. В 1936 году они представили Gibson ES-150 — полуакустическую электрогитару, которая стала хитом благодаря джазовому гитаристу Чарли Кристиану. Именно его игра на ES-150 продемонстрировала потенциал электрогитары как сольного инструмента.

**Революция Лео Фендера (1948–1954)**

Настоящая революция произошла в конце 1940-х, когда Лео Фендер — радиоинженер по образованию — решил создать электрогитару с нуля, не опираясь на акустические традиции. В 1948 году появилась Fender Broadcaster (позже переименованная в Telecaster) — первая массовая цельнокорпусная (solid body) электрогитара.

Telecaster имела ряд революционных особенностей: цельнокорпусная конструкция из ясеня, болчёный гриф из клёна, два звукоснимателя — бриджевый (яркий, острый) и нековый (тёплый, мягкий). Простота конструкции делала её надёжной и доступной.

В 1954 году Фендер выпустил Stratocaster — гитару, которая стала иконой. Три сингла, тремоло-система, эргономичный контурный корпус — Stratocaster стал выбором Джими Хендрикса, Дэвида Гилмора, Эрика Клэптона и сотен других легендарных музыкантов.

**Ответ Gibson — Лес Пол (1952)**

Gibson не остался в стороне. В 1952 году, при участии гитариста Леса Пола, компания выпустила Gibson Les Paul — цельнокорпусную гитару с хамбакерами, тёплым жирным звуком и невероятной сустейностью. Les Paul стал символом рок-музыки: на ней играли Джимми Пейдж, Джо Перри, Слэш, Билли Гиббонс.

**Золотая эра (1955–1970)**

В этот период появились многие модели, ставшие классикой:
- Fender Jazzmaster (1958) — с уникальной электроникой и широким грифом
- Gibson SG (1961) — более лёгкая и острая альтернатива Les Paul
- Fender Jaguar (1962) — любимая гитара сёрф- и альтернативных музыкантов
- Gibson Flying V и Explorer (1958) — радикальные дизайны, опередившие время
- Rickenbacker 325 — гитара The Beatles раннего периода

**Появление хамбакера**

В 1955 году инженер Seth Lover из Gibson изобрёл хамбакер — звукосниматель с двумя катушками, включёнными в противофазе. Это решило главную проблему синглов — фоновый шум. Звук стал толще, теплее, с большим сустейном. Хамбакер определил звучание рока и металла.

**Современная эпоха (1980-е — настоящее время)**

С 1980-х годов электрогитара продолжает эволюционировать:
- Активная электроника (EMG) — ещё больше мощности и чистоты
- Цифровые моделирующие процессоры — тысячи звуков в одном устройстве
- Многоладовые гитары (7-, 8-струнные) — расширенный диапазон для метал-музыки
- ИИ и машинное обучение в обработке звука
- 3D-печать корпусов и экспериментальные материалы

Сегодня электрогитара остаётся одним из самых выразительных и универсальных инструментов. От джаза до металла, от блюза до электроники — она адаптируется к любому жанру и продолжает вдохновлять новые поколения музыкантов.`,
      timestamp: now,
      mode: 'consultation',
    } as Message,
  ],
};
