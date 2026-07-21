import StatusBadge from './StatusBadge';

function CompanyCard({ company, onClick, onDelete, onMouseEnterNote, onMouseMoveNote, onMouseLeaveNote }) {
  const handleDeleteClick = (e) => {
    e.stopPropagation();
    onDelete?.(company);
  };

  return (
    <div
      className={`card company-card${company.notes ? ' has-note' : ''}`}
      onClick={onClick}
      onMouseEnter={company.notes ? onMouseEnterNote : undefined}
      onMouseMove={company.notes ? onMouseMoveNote : undefined}
      onMouseLeave={company.notes ? onMouseLeaveNote : undefined}
    >
      <div className="company-card-header">
        <h3>
          {company.name}
          {company.notes && <span className="note-indicator">📝</span>}
        </h3>
        {company.sector && <span className="badge badge-info">{company.sector}</span>}
      </div>

      {company.description && (
        <p className="company-card-description">{company.description}</p>
      )}

      <div className="company-card-footer">
        <span className="company-card-source">{company.source}</span>
        <div className="company-card-footer-actions">
          <StatusBadge status={company.application_status} />
          {onDelete && (
            <button
              type="button"
              className="company-card-delete-btn"
              title="Şirketi sil"
              aria-label="Şirketi sil"
              onClick={handleDeleteClick}
            >
              🗑️
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default CompanyCard;
