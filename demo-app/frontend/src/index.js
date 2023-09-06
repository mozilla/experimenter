import ReactDOM from 'react-dom';
import React, { useState, useEffect } from 'react';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

function App() {
  const [message, setMessage] = useState({});
  const [clientId, setClientId] = useState('');
  const [context, setContext] = useState('');
  const [apiCallTriggered, setApiCallTriggered] = useState(false);

  useEffect(() => {
    if (apiCallTriggered) {
      const apiUrl = '/api/data';

      fetch(apiUrl, {
        method: 'GET',
        headers: {
          'x-client-id': clientId,
          'x-context': context,
        },
      })
        .then((response) => response.json())
        .then((data) => {
          setMessage(data);
          setApiCallTriggered(false);
        })
        .catch((error) => {
          console.error('Error fetching data:', error);
          setApiCallTriggered(false);
        });
    }
  }, [apiCallTriggered, clientId, context]);

  const displayText = message && message['example-feature'] && message['example-feature']['something']
    ? message['example-feature']['something']
    : 'Not Enrolled';

  return (
    <div className="App">
      <h1>{displayText}</h1>
      <div>
        <input
          type="text"
          placeholder="Client ID"
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
        />
        <input
          type="text"
          placeholder="Context"
          value={context}
          onChange={(e) => setContext(e.target.value)}
        />
        <button onClick={() => setApiCallTriggered(true)}>Send My Details</button>
      </div>
    </div>
  );
}

