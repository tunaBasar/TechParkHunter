/**
 * Mouse pozisyonunda kısa bir önizleme + varsa "not" gösteren tooltip.
 * Notlar aşırı uzun olabileceği için içerik max-height ile sınırlanır ve
 * gerektiğinde kendi içinde kaydırılabilir (overflow-y: auto).
 */
function NoteTooltip({ tooltip }) {
  if (!tooltip) return null;

  const { note, x, y } = tooltip;

  // Ekranın sağ/alt kenarına taşmayı önlemek için basit bir konum düzeltmesi.
  const style = {
    left: Math.min(x + 16, window.innerWidth - 340),
    top: Math.min(y + 16, window.innerHeight - 40),
  };

  return (
    <div className="note-tooltip" style={style}>
      <div className="note-tooltip-header">📝 Not</div>
      <div className="note-tooltip-body">{note}</div>
    </div>
  );
}

export default NoteTooltip;
