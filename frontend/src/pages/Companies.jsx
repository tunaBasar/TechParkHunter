import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import FilterBar from '../components/FilterBar';
import CompanyCard from '../components/CompanyCard';

function Companies() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ search: '', source: '', status: '' });
  const [companies, setCompanies] = useState([]);
  const [sources, setSources] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const params = { page, per_page: 20 };
        if (filters.search) params.search = filters.search;
        if (filters.source) params.source = filters.source;
        if (filters.status) params.status = filters.status;

        const data = await api.getCompanies(params);
        if (cancelled) return;
        setCompanies(data.companies ?? []);
        setTotalPages(data.total_pages || 1);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [filters, page]);

  useEffect(() => {
    api
      .getStats()
      .then((stats) => setSources(Object.keys(stats.by_source ?? {})))
      .catch(() => {});
  }, []);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const pageNumbers = useMemo(() => {
    const pages = [];
    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, start + 4);
    for (let i = start; i <= end; i++) pages.push(i);
    return pages;
  }, [page, totalPages]);

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>🏢 Şirketler</h1>
        <p>Taranan tüm şirketleri görüntüle, filtrele ve incele</p>
      </div>

      <FilterBar filters={filters} onFilterChange={handleFilterChange} sources={sources} />

      {error && <div className="empty-state">❌ Hata: {error}</div>}

      {loading ? (
        <div className="loading-state pulse">Yükleniyor...</div>
      ) : companies.length === 0 ? (
        <div className="empty-state">
          <p>Henüz şirket verisi yok. Scraping panelinden başlayın!</p>
          <button type="button" className="btn btn-primary" onClick={() => navigate('/scraping')}>
            Scraping Paneline Git
          </button>
        </div>
      ) : (
        <>
          <div className="company-grid">
            {companies.map((company) => (
              <CompanyCard
                key={company.id}
                company={company}
                onClick={() => navigate(`/companies/${company.id}`)}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                type="button"
                className="pagination-btn"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Önceki
              </button>

              {pageNumbers.map((num) => (
                <button
                  key={num}
                  type="button"
                  className={`pagination-btn${num === page ? ' active' : ''}`}
                  onClick={() => setPage(num)}
                >
                  {num}
                </button>
              ))}

              <button
                type="button"
                className="pagination-btn"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Sonraki →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Companies;
