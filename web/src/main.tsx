import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { createApi, ApiError } from './api';
import './styles.css';

const container = document.getElementById('root');
if (!container) throw new Error('Application root is unavailable.');
try {
  const api = createApi(window.location.origin);
  createRoot(container).render(<React.StrictMode><App api={api} /></React.StrictMode>);
} catch (error) {
  const message = document.createElement('p');
  message.setAttribute('role', 'alert');
  message.textContent = error instanceof ApiError ? error.message : 'The local interface could not start.';
  container.replaceChildren(message);
}
