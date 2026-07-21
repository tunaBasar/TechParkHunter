import { useState } from 'react';
import { api } from '../services/api';

function simpleMarkdownToHtml(markdown) {
  const escaped = markdown
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  const lines = escaped.split('\n');
  const html = [];
  let inList = false;

  for (const line of lines) {
    const listMatch = line.match(/^-\s+(.*)$/);
    if (listMatch) {
      if (!inList) {
        html.push('<ul>');
        inList = true;
      }
      html.push(`<li>${listMatch[1]}</li>`);
      continue;
    }
    if (inList) {
      html.push('</ul>');
      inList = false;
    }

    let formatted = line
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>');

    if (/^###\s+/.test(formatted)) {
      html.push(`<h5>${formatted.replace(/^###\s+/, '')}</h5>`);
    } else if (/^##\s+/.test(formatted)) {
      html.push(`<h4>${formatted.replace(/^##\s+/, '')}</h4>`);
    } else if (/^#\s+/.test(formatted)) {
      html.push(`<h3>${formatted.replace(/^#\s+/, '')}</h3>`);
    } else if (formatted.trim() === '') {
      html.push('<br/>');
    } else {
      html.push(`<p>${formatted}</p>`);
    }
  }
  if (inList) html.push('</ul>');

  return html.join('\n');
}

function AIGeneratorPanel({ companyId, companyName }) {
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.generateBrief(companyId);
      setBrief(result.brief_markdown);
    } catch (err) {
      setError(err.message || 'Brief oluşturulamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!brief) return;
    navigator.clipboard.writeText(brief);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card ai-generator-panel">
      <div className="ai-generator-header">
        <div>
          <h4 style={{ marginBottom: '0.25rem' }}>📋 Başvuru Brief'i Oluştur</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {companyName} için şirket ve profil bilgisini birleştiren bir brief hazırlanır.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          disabled={loading}
          onClick={handleGenerate}
        >
          {loading ? 'Oluşturuluyor...' : '📋 Brief Oluştur'}
        </button>
      </div>

      {error && (
        <div className="card ai-error-card">
          <p>{error}</p>
          <button type="button" className="btn btn-secondary" onClick={handleGenerate}>
            Tekrar Dene
          </button>
        </div>
      )}

      {brief && !error && (
        <div className="ai-result-block">
          <div className="ai-result-actions">
            <button type="button" className="btn btn-ghost" onClick={handleCopy}>
              {copied ? 'Kopyalandı! ✅' : '📋 Kopyala'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={handleGenerate} disabled={loading}>
              🔄 Yeniden Oluştur
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setShowHelp((v) => !v)}
            >
              💡 Cowork'te nasıl kullanılır?
            </button>
          </div>

          {showHelp && (
            <div className="ai-help-hint">
              Bu metni kopyalayıp Claude Cowork'e yapıştırın, e-posta ve CV önerilerini orada
              oluşturun.
            </div>
          )}

          <div
            className="ai-markdown-output"
            dangerouslySetInnerHTML={{ __html: simpleMarkdownToHtml(brief) }}
          />
        </div>
      )}
    </div>
  );
}

export default AIGeneratorPanel;
