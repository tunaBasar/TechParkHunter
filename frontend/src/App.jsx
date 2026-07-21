import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';

// Placeholder sayfalar (Faz 3b'de gerçek içerikle değiştirilecek)
const Dashboard = () => (
  <div className="page fade-in">
    <div className="page-header">
      <h1>Dashboard</h1>
      <p>Faz 3b'de tamamlanacak</p>
    </div>
  </div>
);

const Companies = () => (
  <div className="page fade-in">
    <div className="page-header">
      <h1>Şirketler</h1>
      <p>Faz 3b'de tamamlanacak</p>
    </div>
  </div>
);

const CompanyDetail = () => (
  <div className="page fade-in">
    <div className="page-header">
      <h1>Şirket Detay</h1>
      <p>Faz 3b'de tamamlanacak</p>
    </div>
  </div>
);

const ScrapingPanel = () => (
  <div className="page fade-in">
    <div className="page-header">
      <h1>Scraping</h1>
      <p>Faz 3b'de tamamlanacak</p>
    </div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/companies/:id" element={<CompanyDetail />} />
            <Route path="/scraping" element={<ScrapingPanel />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
