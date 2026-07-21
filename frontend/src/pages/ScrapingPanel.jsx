import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderSearch } from 'lucide-react';
import { api } from '../services/api';
import Skeleton from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import { useToast } from '../components/Toast';

function ScrapingPanel() {
  const { showToast } = useToast();
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [jobs, setJobs] = useState({}); // slug -> { jobId, status, progress, total_found, error }
  const intervalsRef = useRef({}); // slug -> intervalId

  useEffect(() => {
    document.title = 'TechPark Hunter | Scraping';
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getSites();
        if (!cancelled) setSites(data ?? []);
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          showToast('Site listesi yüklenemedi', 'error');
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

  useEffect(() => {
    const intervals = intervalsRef.current;
    return () => {
      Object.values(intervals).forEach((intervalId) => clearInterval(intervalId));
    };
  }, []);

  const pollStatus = (slug, jobId) => {
    const intervalId = setInterval(async () => {
      try {
        const statusData = await api.getScrapingStatus(jobId);
        setJobs((prev) => ({
          ...prev,
          [slug]: { ...prev[slug], ...statusData },
        }));

        if (statusData.status === 'completed' || statusData.status === 'failed') {
          clearInterval(intervalId);
          delete intervalsRef.current[slug];
          if (statusData.status === 'completed') {
            showToast(
              `${slug}: ${statusData.total_found ?? 0} şirket bulundu`,
              'success'
            );
          } else {
            showToast(`${slug} scraping başarısız oldu`, 'error');
          }
        }
      } catch (err) {
        setJobs((prev) => ({
          ...prev,
          [slug]: { ...prev[slug], status: 'failed', error: err.message },
        }));
        clearInterval(intervalId);
        delete intervalsRef.current[slug];
        showToast(`${slug} scraping başarısız oldu`, 'error');
      }
    }, 2000);

    intervalsRef.current[slug] = intervalId;
  };

  const handleStartScraping = async (slug) => {
    setJobs((prev) => ({
      ...prev,
      [slug]: { status: 'starting', progress: 0, total_found: 0, error: null },
    }));

    try {
      const { job_id: jobId } = await api.startScraping(slug);
      setJobs((prev) => ({
        ...prev,
        [slug]: { ...prev[slug], jobId, status: 'running' },
      }));
      pollStatus(slug, jobId);
    } catch (err) {
      setJobs((prev) => ({
        ...prev,
        [slug]: { ...prev[slug], status: 'failed', error: err.message },
      }));
    }
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>🕷️ Scraping Yönetimi</h1>
        <p>Bir kaynak seçip veri toplama işlemini başlatın</p>
      </div>

      {error && <div className="empty-state">❌ Hata: {error}</div>}

      {loading ? (
        <div className="sites-grid">
          {Array.from({ length: 3 }).map((_, i) => (
            // eslint-disable-next-line react/no-array-index-key
            <Skeleton key={i} className="skeleton-card" />
          ))}
        </div>
      ) : sites.length === 0 ? (
        <EmptyState
          icon={FolderSearch}
          title="Hiç site config'i bulunamadı"
          message="backend/app/scraping/sites/ dizinine YAML config ekleyerek yeni siteler tanımlayabilirsiniz."
        />
      ) : (
        <div className="sites-grid">
          {sites.map((site) => {
            const job = jobs[site.slug];
            const isRunning = job?.status === 'starting' || job?.status === 'running';

            return (
              <div key={site.slug} className="card site-card">
                <h3>{site.name}</h3>
                <span className="site-card-url">{site.base_url}</span>

                {job && job.status !== 'idle' && (
                  <div
                    className={`site-card-status${
                      job.status === 'failed' ? ' status-error' : ''
                    }${job.status === 'completed' ? ' status-success' : ''}`}
                  >
                    {isRunning && (
                      <>
                        <span className="spinner" />
                        ⏳ {job.status === 'starting' ? 'Scraping başlatılıyor...' : `Çalışıyor... ${job.progress ?? 0} şirket bulundu`}
                      </>
                    )}
                    {job.status === 'completed' && (
                      <>✅ Tamamlandı! {job.total_found ?? job.progress ?? 0} şirket kaydedildi</>
                    )}
                    {job.status === 'failed' && <>❌ Hata: {job.error ?? 'Bilinmeyen hata'}</>}
                  </div>
                )}

                {job?.status === 'completed' ? (
                  <Link to="/companies" className="btn btn-secondary">
                    Şirketleri Görüntüle
                  </Link>
                ) : (
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={isRunning}
                    onClick={() => handleStartScraping(site.slug)}
                  >
                    {isRunning ? 'Çalışıyor...' : '🚀 Scrape Başlat'}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ScrapingPanel;
