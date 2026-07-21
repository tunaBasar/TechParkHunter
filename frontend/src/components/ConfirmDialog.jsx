import { AlertTriangle } from 'lucide-react';

function ConfirmDialog({ open, title, message, confirmLabel = 'Sil', onConfirm, onCancel }) {
  if (!open) return null;

  return (
    <div className="confirm-dialog-overlay" onClick={onCancel}>
      <div className="confirm-dialog card" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-dialog-icon">
          <AlertTriangle size={28} />
        </div>
        <h4>{title}</h4>
        <p>{message}</p>
        <div className="confirm-dialog-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Vazgeç
          </button>
          <button type="button" className="btn btn-danger" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmDialog;
