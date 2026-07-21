import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, SearchX, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import AIGeneratorPanel from '../components/AIGeneratorPanel';
import Skeleton from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../components/Toast';

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
  const { showToast } = useToast();

  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [status, setStatus] = useState('not_applied');
  const [notes, setNotes] = useState('');
  const [savingStatus, setSavingStatus] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const [statusSaved, setStatusSaved] = useState(false);
  const [notesSaved, setNotesSaved] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

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
        document.title = `TechPark Hunter | ${data.name}`;
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
      showToast('Şirket durumu güncellendi', 'success');
      setTimeout(() => setStatusSaved(false), 2000);
    } catch (err) {
      showToast('Durum güncellenemedi', 'error');
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
      showToast('Notlar kaydedildi', 'success');
      setTimeout(() => setNotesSaved(false), 2000);
    } catch (err) {
      showToast('Notlar kaydedilemedi', 'error');
      // eslint-disable-next-line no-console
      console.error(err);
    } finally {
      setSavingNotes(false);
    }
  };

  const handleDeleteConfirm = async () => {
    setDeleting(true);
    try {
      await api.deleteCompany(id);
      showToast(`"${company.name}" silindi`, 'success');
      navigate('/companies');
    } catch (err) {
      showToast('Şirket silinemedi', 'error');
      // eslint-disable-next-line no-console
      console.error(err);
      setDeleting(false);
      setConfirmDeleteOpen(false);
    }
  };

  if (loading) {
    return (
      <div className="page fade-in">
        <Skeleton className="skeleton-title" />
        <div className="detail-layout">
          <div className="detail-column">
            <Skeleton className="skeleton-block" />
            <Skeleton className="skeleton-block" />
          </div>
          <div className="detail-column">
            <Skeleton className="skeleton-block" />
            <Skeleton className="skeleton-block" />
          </div>
        </div>
      </div>
    );
  }

  if (notFound || !company) {
    return (
      <div className="page fade-in">
        <button type="button" className="detail-back-btn" onClick={() => navigate('/companies')}>
          <ArrowLeft size={16} /> Geri
        </button>
        <EmptyState
          icon={SearchX}
          title="Şirket bulunamadı"
          message="Bu şirket kaydı mevcut değil veya silinmiş olabilir."
          actionLabel="Şirketlere Dön"
          onAction={() => navigate('/companies')}
        />
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
          <button
            type="button"
            className="btn btn-danger detail-delete-btn"
            onClick={() => setConfirmDeleteOpen(true)}
          >
            <Trash2 size={16} /> Sil
          </button>
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

      <AIGeneratorPanel companyId={id} companyName={company.name} />

      <ConfirmDialog
        open={confirmDeleteOpen}
        title="Şirketi Sil"
        message={`"${company.name}" kalıcı olarak silinecek. Bu işlem geri alınamaz.`}
        confirmLabel={deleting ? 'Siliniyor...' : 'Sil'}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setConfirmDeleteOpen(false)}
      />
    </div>
  );
}

export default CompanyDetail;
