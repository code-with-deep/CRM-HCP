import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'

import App from '@/App'
import { ToastProvider } from '@/components/common/ToastProvider'
import { store } from '@/store'
import '@/styles/index.css'

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element not found.')
}

createRoot(rootElement).render(
  <StrictMode>
    <Provider store={store}>
      <ToastProvider />
      <App />
    </Provider>
  </StrictMode>,
)
