import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Globe, Send, Clock } from 'lucide-react';
import { api } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const APPLIED_STATUSES = ['applied', 'interview', 'accepted'];

function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentCompanies, setRecentCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [statsData, companiesData] = await Promise.all([
          api.getStats(),
          api.getCompanies({ per_page: 10 }),
        ]);
        if (cancelled) return;
        setStats(statsData);
        setRecentCompanies(companiesData.companies ?? []);
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
  }, []);

  const totalApplied = stats
    ? Object.entries(stats.by_status ?? {})
        .filter(([status]) => APPLIED_STATUSES.includes(status))
        .reduce((sum, [, count]) => sum + count, 0)
    : 0;

  const totalPending = stats?.by_status?.not_applied ?? 0;
  const sourceCount = stats ? Object.keys(stats.by_source ?? {}).length : 0;

  const statCards = [
    { label: 'Toplam Şirket', value: stats?.total_companies ?? 0, icon: Building2 },
    { label: 'Kaynak Sayısı', value: sourceCount, icon: Globe },
    { label: 'Başvurulan', value: totalApplied, icon: Send },
    { label: 'Bekleyen', value: totalPending, icon: Clock },
  ];

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>📊 Dashboard</h1>
        <p>Genel istatistikler ve son eklenen şirketler</p>
      </div>

      {error && <div className="empty-state">❌ Hata: {error}</div>}

      <div className="stats-grid">
        {statCards.map(({ label, value, icon: Icon }) => (
          <div key={label} className="card stat-card">
            <div className="stat-card-icon">
              <Icon />
            </div>
            <div>
              <div className="stat-card-value">
                {loading ? <span className="pulse">–</span> : value}
              </div>
              <div className="stat-card-label">{label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h4 style={{ marginBottom: '1rem' }}>Son Eklenen Şirketler</h4>

        {loading ? (
          <div className="loading-state pulse">Yükleniyor...</div>
        ) : recentCompanies.length === 0 ? (
          <div className="empty-state">Henüz şirket verisi yok.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>İsim</th>
                  <th>Sektör</th>
                  <th>Kaynak</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody>
                {recentCompanies.map((company) => (
                  <tr
                    key={company.id}
                    onClick={() => navigate(`/companies/${company.id}`)}
                  >
                    <td>{company.name}</td>
                    <td>{company.sector || '—'}</td>
                    <td>{company.source}</td>
                    <td>
                      <StatusBadge status={company.application_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
