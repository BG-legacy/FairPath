import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import IntakePage from './pages/IntakePage';
import RecommendationsPage from './pages/RecommendationsPage';
import GuardedRecommendationsPage from './pages/GuardedRecommendationsPage';
import ResumePage from './pages/ResumePage';
import CareerSwitchPage from './pages/CareerSwitchPage';
import OutlookPage from './pages/OutlookPage';
import PathsPage from './pages/PathsPage';
import CertsPage from './pages/CertsPage';
import CoachPage from './pages/CoachPage';
import CatalogPage from './pages/CatalogPage';
import CatalogDetailPage from './pages/CatalogDetailPage';
import TrustPage from './pages/TrustPage';
import NotFoundPage from './pages/NotFoundPage';
import Navigation from './components/Navigation';
import ErrorBoundary from './components/ErrorBoundary';
import GlobalErrorHandler from './components/GlobalErrorHandler';
import { QueryProvider } from './providers/QueryProvider';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <GlobalErrorHandler />
      <QueryProvider>
        <Router>
          <div className="App">
            <Navigation />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/intake" element={<IntakePage />} />
                <Route path="/recommendations" element={<RecommendationsPage />} />
                <Route path="/recommendations-guarded" element={<GuardedRecommendationsPage />} />
                <Route path="/resume" element={<ResumePage />} />
                <Route path="/career-switch" element={<CareerSwitchPage />} />
                <Route path="/outlook/:careerId" element={<OutlookPage />} />
                <Route path="/paths/:careerId" element={<PathsPage />} />
                <Route path="/certs/:careerId" element={<CertsPage />} />
                <Route path="/coach" element={<CoachPage />} />
                <Route path="/catalog" element={<CatalogPage />} />
                <Route path="/catalog/:careerId" element={<CatalogDetailPage />} />
                <Route path="/trust" element={<TrustPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </main>
          </div>
        </Router>
      </QueryProvider>
    </ErrorBoundary>
  );
}

export default App;

