import { useState } from "react";

export function ApiKeyGate({ onSubmit }: { onSubmit: (key: string) => void }) {
  const [key, setKey] = useState("");

  return (
    <div className="app gate">
      <h1>Folha de Ponto</h1>
      <p>Informe a chave de API configurada no servidor (variável API_KEY do .env).</p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (key.trim()) {
            onSubmit(key.trim());
          }
        }}
      >
        <input
          type="password"
          value={key}
          onChange={(event) => setKey(event.target.value)}
          placeholder="Chave de API"
          autoFocus
        />
        <button type="submit" className="primary" disabled={!key.trim()}>
          Entrar
        </button>
      </form>
    </div>
  );
}
