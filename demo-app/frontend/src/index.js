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

  useEffect(() => {
    fetch('/api/data')
      .then(response => response.json())
      .then(data => {
        setMessage(data);
      })
      .catch(error => console.error('Error fetching data:', error));
  }, []);

  const displayText = message && message['example-feature'] && message['example-feature']['something']
    ? message['example-feature']['something']
    : 'Not Enrolled';

  return (
    <div className="App">
      <h1>{displayText}</h1>
    </div>
  );
}
