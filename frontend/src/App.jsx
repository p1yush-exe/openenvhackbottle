import { useRef, useState } from "react";

const starterCode = `print("hello clinical bench")`;

function getWebSocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

function formatPayload(payload) {
  return JSON.stringify(payload, null, 2);
}

export default function App() {
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [busy, setBusy] = useState(false);
  const [code, setCode] = useState(starterCode);
  const [events, setEvents] = useState([]);

  function addEvent(label, payload) {
    setEvents((current) => [
      {
        id: crypto.randomUUID(),
        label,
        payload,
        time: new Date().toLocaleTimeString()
      },
      ...current
    ]);
  }

  function sendMessage(message) {
    const socket = socketRef.current;

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      addEvent("error", { message: "Not connected" });
      return;
    }

    setBusy(true);
    socket.send(JSON.stringify(message));
  }

  function connect() {
    if (socketRef.current) {
      return;
    }

    const socket = new WebSocket(getWebSocketUrl());
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      addEvent("connected", { endpoint: "/ws" });
      socket.send(JSON.stringify({ type: "reset", data: {} }));
    };

    socket.onmessage = (event) => {
      setBusy(false);
      addEvent("response", JSON.parse(event.data));
    };

    socket.onerror = () => {
      setBusy(false);
      addEvent("error", { message: "WebSocket error" });
    };

    socket.onclose = () => {
      setBusy(false);
      setConnected(false);
      socketRef.current = null;
      addEvent("closed", { endpoint: "/ws" });
    };
  }

  function disconnect() {
    socketRef.current?.send(JSON.stringify({ type: "close", data: {} }));
    socketRef.current?.close();
  }

  function resetEnvironment() {
    sendMessage({ type: "reset", data: {} });
  }

  function submitStep() {
    sendMessage({
      type: "step",
      data: { code }
    });
  }

  return (
    <main className="shell">
      <section className="workspace">
        <div className="intro">
          <p className="eyebrow">ClinicalBench</p>
          <h1>Submit Python code to the environment.</h1>
        </div>

        <div className="toolbar">
          <button onClick={connect} disabled={connected}>
            Connect
          </button>
          <button onClick={resetEnvironment} disabled={!connected || busy}>
            Reset
          </button>
          <button onClick={disconnect} disabled={!connected}>
            Disconnect
          </button>
        </div>

        <label className="editor">
          <span>Code</span>
          <textarea
            value={code}
            onChange={(event) => setCode(event.target.value)}
            spellCheck="false"
          />
        </label>

        <button className="submit" onClick={submitStep} disabled={!connected || busy}>
          {busy ? "Waiting" : "Submit step"}
        </button>
      </section>

      <section className="events" aria-label="Environment responses">
        <div className="eventsHeader">
          <h2>Responses</h2>
          <button onClick={() => setEvents([])} disabled={events.length === 0}>
            Clear
          </button>
        </div>

        {events.length === 0 ? (
          <p className="empty">Connect to start a session.</p>
        ) : (
          events.map((event) => (
            <article className="event" key={event.id}>
              <div>
                <strong>{event.label}</strong>
                <span>{event.time}</span>
              </div>
              <pre>{formatPayload(event.payload)}</pre>
            </article>
          ))
        )}
      </section>
    </main>
  );
}
