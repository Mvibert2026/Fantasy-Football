import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { StandaloneApp } from './StandaloneApp';
import './styles/base.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <StandaloneApp />
  </StrictMode>,
);
