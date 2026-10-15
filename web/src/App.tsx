import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ApiError } from './api'
import Backdrop from './Backdrop'
import LoginPage from './LoginPage'
import ManagePage from './ManagePage'
import Protected from './Protected'
import TreePage from './TreePage'
import TreesPage from './TreesPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Auth and validation errors will not fix themselves, so only retry 5xx / network failures.
      retry: (count, err) => !(err instanceof ApiError && err.status < 500) && count < 2,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Backdrop />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<Protected />}>
            <Route path="/" element={<TreesPage />} />
            <Route path="/trees/:treeId" element={<TreePage />} />
            <Route path="/trees/:treeId/manage" element={<ManagePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
