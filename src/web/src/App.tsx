import { useCallback, useState } from "react";

import { clearApiKey, getStoredApiKey, storeApiKey } from "./api";
import { applyTheme, getInitialTheme, storeTheme, type Theme } from "./theme";
import { ApiKeyGate } from "./components/ApiKeyGate";
import { MonthTab } from "./components/MonthTab";
import { RecordForm } from "./components/RecordForm";
import { TodayTab } from "./components/TodayTab";
import type { TimeRecord } from "./types";

type View =
  | { kind: "tabs"; tab: "today" | "month" }
  | { kind: "form"; date: string; record: TimeRecord | null; backTab: "today" | "month" };

export function App() {
  const [hasKey, setHasKey] = useState(() => getStoredApiKey() !== "");
  const [view, setView] = useState<View>({ kind: "tabs", tab: "today" });
  const [reloadToken, setReloadToken] = useState(0);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    storeTheme(next);
  };

  const handleUnauthorized = useCallback(() => {
    clearApiKey();
    setHasKey(false);
  }, []);

  if (!hasKey) {
    return (
      <ApiKeyGate
        onSubmit={(key) => {
          storeApiKey(key);
          setHasKey(true);
          setReloadToken((token) => token + 1);
        }}
      />
    );
  }

  if (view.kind === "form") {
    return (
      <RecordForm
        date={view.date}
        record={view.record}
        onUnauthorized={handleUnauthorized}
        onDone={(changed) => {
          if (changed) {
            setReloadToken((token) => token + 1);
          }
          setView({ kind: "tabs", tab: view.backTab });
        }}
      />
    );
  }

  const openForm = (tab: "today" | "month") => (date: string, record: TimeRecord | null) =>
    setView({ kind: "form", date, record, backTab: tab });

  return (
    <div className="app">
      <header className="app-header">
        <h1>Folha de Ponto</h1>
        <div className="header-actions">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title={theme === "dark" ? "Mudar para tema claro" : "Mudar para tema escuro"}
            aria-label="Alternar tema"
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
          <button className="link-button" onClick={handleUnauthorized} title="Trocar chave de API">
            Sair
          </button>
        </div>
      </header>

      <nav className="tabs">
        <button
          className={view.tab === "today" ? "tab active" : "tab"}
          onClick={() => setView({ kind: "tabs", tab: "today" })}
        >
          Hoje
        </button>
        <button
          className={view.tab === "month" ? "tab active" : "tab"}
          onClick={() => setView({ kind: "tabs", tab: "month" })}
        >
          Mês
        </button>
      </nav>

      <main className="content">
        {view.tab === "today" ? (
          <TodayTab
            reloadToken={reloadToken}
            onEdit={openForm("today")}
            onUnauthorized={handleUnauthorized}
          />
        ) : (
          <MonthTab
            reloadToken={reloadToken}
            onEdit={openForm("month")}
            onUnauthorized={handleUnauthorized}
          />
        )}
      </main>
    </div>
  );
}
