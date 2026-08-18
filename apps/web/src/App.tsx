import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import "./App.css";

/** Response shape from POST /ask (matches ai-assistant API contract). */
interface AskResponse {
  answer: string;
  source: string;
  confidence: number;
  blocked: boolean;
}

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  source?: string;
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/** Quick-start prompts that match seeded cache questions (Dutch, like ziggo.nl). */
const SUGGESTIONS = [
  "Wat is Ziggo GO?",
  "Wat is Wifi Garantie?",
  "Hoeveel zenders heeft Ziggo TV?",
  "Kan ik Ziggo GO gebruiken in het buitenland?",
];

const ZIGGO_LOGO =
  "https://vodafoneziggo.scene7.com/is/content/vodafoneziggo/ziggo-logo-orange-v1?fmt=svg&wid=256&fit=constrain";

/**
 * Looks like a link (underline/hover styles) but never navigates.
 * Demo chrome only — real ziggo.nl URLs would leak people off this page.
 */
function InertLink({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <span className={`inert-link ${className}`.trim()}>{children}</span>;
}

function sourceLabel(source: string): string {
  switch (source) {
    case "cache":
      return "Direct antwoord";
    case "rag":
      return "Uit de kennisbank";
    case "blocked":
      return "Niet beantwoord";
    case "none":
      return "Geen bron";
    default:
      return source;
  }
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function askQuestion(question: string) {
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data: AskResponse = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          source: data.blocked ? "blocked" : data.source,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "De assistent is even niet bereikbaar. Draait docker compose?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    void askQuestion(input.trim());
  }

  return (
    <div className="page">
      <a href="#main-content" className="skip-link">
        Direct naar inhoud
      </a>

      {/* Top strip: Privé / Zakelijk — same pattern as ziggo.nl audience selector */}
      <div className="audience">
        <div className="container audience__inner">
          <InertLink className="audience__link audience__link--active">
            Privé
          </InertLink>
          <InertLink className="audience__link">Zakelijk</InertLink>
        </div>
      </div>

      <header className="navbar">
        <div className="container navbar__inner">
          <InertLink className="navbar__brand">
            <span className="sr-only">Ziggo</span>
            <img
              src={ZIGGO_LOGO}
              alt="Ziggo"
              className="navbar__logo"
              height={30}
            />
          </InertLink>

          <nav className="navbar__nav" aria-label="Hoofdnavigatie">
            <InertLink>Producten</InertLink>
            <InertLink className="navbar__nav-item navbar__nav-item--active">
              Klantenservice
            </InertLink>
            <InertLink>Entertainment</InertLink>
          </nav>

          <div className="navbar__apps">
            <InertLink>Ziggo GO</InertLink>
            <InertLink className="navbar__account">Mijn Ziggo</InertLink>
          </div>
        </div>
      </header>

      <main id="main-content">
        <section className="hero" aria-labelledby="hero-title">
          <div className="container hero__inner">
            <p className="hero__eyebrow">Klantenservice</p>
            <h1 id="hero-title">Hoe kan ik je helpen?</h1>
            <p className="hero__sub">
              Stel je vraag over internet, tv, bellen of Ziggo GO.
            </p>
          </div>
        </section>

        <div className="container">
          <section className="chat-panel" aria-label="Ziggo Assistent">
            <div className="chat-panel__head">
              <span className="chat-panel__dot" aria-hidden="true" />
              <div>
                <h2>Ziggo Assistent</h2>
                <p>Antwoorden uit de Ziggo kennisbank</p>
              </div>
            </div>

            <div className="chat">
              {messages.length === 0 && !loading && (
                <div className="empty">
                  <p className="empty__lead">
                    Waar wil je meer over weten? Kies een vraag of typ er zelf
                    een.
                  </p>
                  <ul className="suggestions">
                    {SUGGESTIONS.map((q) => (
                      <li key={q}>
                        <button
                          type="button"
                          className="chip"
                          onClick={() => void askQuestion(q)}
                        >
                          {q}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} className={`bubble bubble--${msg.role}`}>
                  <p>{msg.text}</p>
                  {msg.source && (
                    <span className={`badge badge--${msg.source}`}>
                      {sourceLabel(msg.source)}
                    </span>
                  )}
                </div>
              ))}

              {loading && (
                <div className="bubble bubble--assistant bubble--typing">
                  <span className="typing" aria-label="Bezig met nadenken">
                    <span />
                    <span />
                    <span />
                  </span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <form className="composer" onSubmit={handleSubmit}>
              <label htmlFor="question" className="sr-only">
                Typ je vraag
              </label>
              <input
                id="question"
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Typ je vraag…"
                disabled={loading}
                autoComplete="off"
              />
              <button type="submit" disabled={loading || !input.trim()}>
                <span>Verstuur</span>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M5 12h12M13 6l6 6-6 6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </form>
          </section>
        </div>
      </main>

      <footer className="footer">
        <div className="container">
          <nav className="footer__grid" aria-label="Footer navigatie">
            <div>
              <h2>Pakketten</h2>
              <ul>
                <li>
                  <InertLink>Alles-in-1</InertLink>
                </li>
                <li>
                  <InertLink>Internet &amp; TV</InertLink>
                </li>
                <li>
                  <InertLink>Internet Only</InertLink>
                </li>
              </ul>
            </div>
            <div>
              <h2>Internet</h2>
              <ul>
                <li>
                  <InertLink>Over internet</InertLink>
                </li>
                <li>
                  <InertLink>Wifi</InertLink>
                </li>
                <li>
                  <InertLink>Wifi Garantie</InertLink>
                </li>
              </ul>
            </div>
            <div>
              <h2>Televisie</h2>
              <ul>
                <li>
                  <InertLink>Televisie</InertLink>
                </li>
                <li>
                  <InertLink>Ziggo GO</InertLink>
                </li>
                <li>
                  <InertLink>Vast bellen</InertLink>
                </li>
              </ul>
            </div>
            <div>
              <h2>Klantenservice</h2>
              <ul>
                <li>
                  <InertLink>Hulp &amp; contact</InertLink>
                </li>
                <li>
                  <InertLink>Mijn Ziggo</InertLink>
                </li>
                <li>
                  <InertLink>Community</InertLink>
                </li>
              </ul>
            </div>
          </nav>

          <div className="footer__legal">
            <p>© Ziggo B.V. — demo assistent, geen officieel Ziggo-kanaal</p>
            <ul>
              <li>
                <InertLink>Privacy</InertLink>
              </li>
              <li>
                <InertLink>Cookies</InertLink>
              </li>
              <li>
                <InertLink>Voorwaarden</InertLink>
              </li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}
