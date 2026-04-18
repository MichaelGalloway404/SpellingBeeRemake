import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import SpellingBee from './SpellingBee.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <SpellingBee />
  </StrictMode>,
)
