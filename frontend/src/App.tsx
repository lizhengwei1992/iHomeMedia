import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import MediaViewPage from './pages/MediaViewPage'
import SearchResultsPage from './pages/SearchResultsPage'
import { AuthProvider, useAuth } from './hooks/useAuth'

// Protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/search/results" 
            element={
              <ProtectedRoute>
                <SearchResultsPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/media/view/:mediaId" 
            element={
              <ProtectedRoute>
                <MediaViewPage />
              </ProtectedRoute>
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App 