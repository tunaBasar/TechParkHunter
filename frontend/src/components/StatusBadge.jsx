const STATUS_CONFIG = {
  not_applied: { label: 'Başvurulmadı', className: 'badge-muted' },
  applied: { label: 'Başvuruldu', className: 'badge-info' },
  interview: { label: 'Mülakat', className: 'badge-warning' },
  rejected: { label: 'Reddedildi', className: 'badge-error' },
  accepted: { label: 'Kabul Edildi', className: 'badge-success' },
};

function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.not_applied;

  return (
    <span className={`badge ${config.className}`}>
      <span className="badge-dot" />
      {config.label}
    </span>
  );
}

export default StatusBadge;
