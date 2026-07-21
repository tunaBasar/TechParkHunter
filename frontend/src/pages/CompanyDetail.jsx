import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { api } from '../services/api';

const STATUS_OPTIONS = [
  { value: 'not_applied', label: 'Başvurulmadı' },
  { value: 'applied', label: 'Başvuruldu' },
  { value: 'interview', label: 'Mülakat' },
  { value: 'rejected', label: 'Reddedildi' },
  { value: 'accepted', label: 'Kabul Edildi' },
];

function CompanyDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [status, setStatus] = useState('not_applied');
  const [notes, setNotes] = useState('');
  const [savingStatus, setSavingStatus] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const [statusSaved, setStatusSaved] = useState(false);
  const [notesSaved, setNotesSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setNotFound(false);
      try {
        const data = await api.getCompany(id);
        if (cancelled) return;
        setCompany(data);
        setStatus(data.application_status ?? 'not_applied');
        setNotes(data.notes ?? '');
      } catch {
        if (!cancelled) setNotFound(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleSaveStatus = async () => {
    setSavingStatus(true);
    setStatusSaved(false);
    try {
      await api.updateCompany(id, { application_status: status });
      setStatusSaved(true);
      setTimeout(() => setStatusSaved(false), 2000);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
    } finally {
      setSavingStatus(false);
    }
  };

  const handleSaveNotes = async () => {
    setSavingNotes(true);
    setNotesSaved(false);
    try {
      await api.updateCompany(id, { notes });
      setNotesSaved(true);
      setTimeout(() => setNotesSaved(false), 2000);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
    } finally {
      setSavingNotes(false);
    }
  };

  if (loading) {
    return (
      <div className="page fade-in">
        <div className="loading-state pulse">Yükleniyor...</div>
      </div>
    );
  }

  if (notFound || !company) {
    return (
      <div className="page fade-in">
        <button type="button" className="detail-back-btn" onClick={() => navigate('/companies')}>
          <ArrowLeft size={16} /> Geri
        </button>
        <div className="empty-state">Şirket bulunamadı</div>
      </div>
    );
  }

  return (
    <div className="page fade-in">
      <div className="detail-header">
        <button type="button" className="detail-back-btn" onClick={() => navigate('/companies')}>
          <ArrowLeft size={16} /> Geri
        </button>

        <div className="detail-title-row">
          <h1>{company.name}</h1>
          {company.sector && <span className="badge badge-info">{company.sector}</span>}
          {(company.sector_tags ?? []).map((tag) => (
            <span key={tag} className="badge badge-muted">
              {tag}
            </span>
          ))}
        </div>

        <span className="detail-source">Kaynak: {company.source}</span>
      </div>

      <div className="detail-layout">
        <div className="detail-column">
          <div className="card detail-card">
            <h4>Açıklama</h4>
            <p>{company.description || 'Açıklama bulunmuyor.'}</p>
            {company.full_description && <p>{company.full_description}</p>}
          </div>

          <div className="card detail-card">
            <h4>İletişim</h4>
            {company.website && (
              <div className="detail-contact-row">
                🌐{' '}
                <a href={company.website} target="_blank" rel="noreferrer">
                  {company.website}
                </a>
              </div>
            )}
            {company.contact_email && (
              <div className="detail-contact-row">
                ✉️ <a href={`mailto:${company.contact_email}`}>{company.contact_email}</a>
              </div>
            )}
            {!company.website && !company.contact_email && (
              <p style={{ color: 'var(--text-muted)' }}>İletişim bilgisi bulunmuyor.</p>
            )}
          </div>
        </div>

        <div className="detail-column">
          <div className="card detail-card">
            <h4>Başvuru Durumu</h4>
            <select
              className="input detail-status-select"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <div className="detail-save-row">
              {statusSaved && <span className="detail-save-hint">✓ Kaydedildi</span>}
              <button
                type="button"
                className="btn btn-primary"
                disabled={savingStatus}
                onClick={handleSaveStatus}
              >
                {savingStatus ? 'Kaydediliyor...' : 'Kaydet'}
              </button>
            </div>
          </div>

          <div className="card detail-card">
            <h4>Notlar</h4>
            <textarea
              className="input detail-textarea"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Bu şirket hakkında notlarınız..."
            />
            <div className="detail-save-row">
              {notesSaved && <span className="detail-save-hint">✓ Kaydedildi</span>}
              <button
                type="button"
                className="btn btn-primary"
                disabled={savingNotes}
                onClick={handleSaveNotes}
              >
                {savingNotes ? 'Kaydediliyor...' : 'Kaydet'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="card ai-panel">
        <div>
          <h4 style={{ marginBottom: '0.25rem' }}>🤖 AI ile Başvuru Oluştur</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Faz 4'te aktif olacak
          </p>
        </div>
        <button type="button" className="btn btn-primary" disabled title="Faz 4'te aktif olacak">
          🤖 AI ile Başvuru Oluştur
        </button>
      </div>
    </div>
  );
}

export default CompanyDetail;
