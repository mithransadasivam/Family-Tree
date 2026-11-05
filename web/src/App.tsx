import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ApiError } from './api'
import Backdrop from './Backdrop'
import CommunitiesPage from './CommunitiesPage'
import ApprovePage from './ApprovePage'
import CommunityPage from './CommunityPage'
import LoginPage from './LoginPage'
import ManagePage from './ManagePage'
import ProfilePage from './ProfilePage'
import Protected from './Protected'
import RequireSuperuser from './RequireSuperuser'
import StaffTreePage from './StaffTreePage'
import StaffTreesPage from './StaffTreesPage'
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

/** The website's pages. (Staff pages live under /staff/ because Django's own admin site owns the other address.) */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Protected />}>
        <Route path="/" element={<TreesPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/approve/:kind/:requestId" element={<ApprovePage />} />
        <Route path="/communities" element={<CommunitiesPage />} />
        <Route path="/communities/:communityId" element={<CommunityPage />} />
        <Route path="/trees/:treeId" element={<TreePage />} />
        <Route path="/trees/:treeId/manage" element={<ManagePage />} />
        {/* Superusers only: read-only look at every family (the server enforces it too). */}
        <Route element={<RequireSuperuser />}>
          <Route path="/staff/trees" element={<StaffTreesPage />} />
          <Route path="/staff/trees/:treeId" element={<StaffTreePage />} />
        </Route>
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Backdrop />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
