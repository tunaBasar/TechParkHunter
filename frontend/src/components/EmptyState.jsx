function EmptyState({ icon: Icon, title, message, actionLabel, onAction }) {
  return (
    <div className="empty-state-rich">
      {Icon && <Icon size={48} strokeWidth={1.5} />}
      {title && <h3>{title}</h3>}
      {message && <p>{message}</p>}
      {actionLabel && onAction && (
        <button type="button" className="btn btn-primary" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export default EmptyState;
