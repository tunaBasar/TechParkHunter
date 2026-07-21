import StatusBadge from './StatusBadge';

function CompanyCard({ company, onClick }) {
  return (
    <div className="card company-card" onClick={onClick}>
      <div className="company-card-header">
        <h3>{company.name}</h3>
        {company.sector && <span className="badge badge-info">{company.sector}</span>}
      </div>

      {company.description && (
        <p className="company-card-description">{company.description}</p>
      )}

      <div className="company-card-footer">
        <span className="company-card-source">{company.source}</span>
        <StatusBadge status={company.application_status} />
      </div>
    </div>
  );
}

export default CompanyCard;
