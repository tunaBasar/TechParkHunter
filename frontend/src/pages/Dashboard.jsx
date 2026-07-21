import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Globe, Send, Clock, FolderOpen } from 'lucide-react';
import { api } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import Skeleton from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import NoteTooltip from '../components/NoteTooltip';
import useNoteTooltip from '../hooks/useNoteTooltip';
import { useToast } from '../components/Toast';

const APPLIED_STATUSES = ['applied', 'interview', 'accepted'];

function Dashboard() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { tooltip, showTooltip, moveTooltip, hideTooltip } = useNoteTooltip();
  const [stats, setStats] = useState(null);
  const [recentCompanies, setRecentCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'TechPark Hunter | Dashboard';
  }, []);

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
        if (!cancelled) {
          setError(err.message);
          showToast('Dashboard verileri yüklenemedi', 'error');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <Skeleton key={i} className="skeleton-stat-card" />
            ))
          : statCards.map(({ label, value, icon: Icon }) => (
              <div key={label} className="card stat-card">
                <div className="stat-card-icon">
                  <Icon />
                </div>
                <div>
                  <div className="stat-card-value">{value}</div>
                  <div className="stat-card-label">{label}</div>
                </div>
              </div>
            ))}
      </div>

      <div className="card">
        <h4 style={{ marginBottom: '1rem' }}>Son Eklenen Şirketler</h4>

        {loading ? (
          <>
            <Skeleton className="skeleton-row" />
            <Skeleton className="skeleton-row" />
            <Skeleton className="skeleton-row" />
            <Skeleton className="skeleton-row" />
          </>
        ) : recentCompanies.length === 0 ? (
          <EmptyState
            icon={FolderOpen}
            title="Henüz veri yok"
            message="Scraping panelinden veri çekmeye başlayın"
            actionLabel="Scraping Paneline Git"
            onAction={() => navigate('/scraping')}
          />
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
                    onMouseEnter={company.notes ? showTooltip(company.notes) : undefined}
                    onMouseMove={company.notes ? moveTooltip : undefined}
                    onMouseLeave={company.notes ? hideTooltip : undefined}
                    className={company.notes ? 'has-note' : undefined}
                  >
                    <td>
                      {company.name}
                      {company.notes && <span className="note-indicator">📝</span>}
                    </td>
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

      <NoteTooltip tooltip={tooltip} />
    </div>
  );
}

export default Dashboard;
