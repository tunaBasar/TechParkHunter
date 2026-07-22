const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export const api = {
  getCompanies: (params) => request(`/companies/?${new URLSearchParams(params)}`),
  getCompany: (id) => request(`/companies/${id}`),
  getStats: () => request('/companies/stats'),
  updateCompany: (id, data) =>
    request(`/companies/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteCompany: (id) => request(`/companies/${id}`, { method: 'DELETE' }),
  findContactEmail: (id) =>
    request(`/companies/${id}/find-contact-email`, { method: 'POST' }),
  getSites: () => request('/scrape/sites'),
  startScraping: (slug) => request(`/scrape/${slug}`, { method: 'POST' }),
  getScrapingStatus: (jobId) => request(`/scrape/status/${jobId}`),
  generateBrief: (companyId) =>
    request('/ai/generate-brief', {
      method: 'POST',
      body: JSON.stringify({ company_id: companyId }),
    }),
  sendEmail: (companyId) =>
    request('/ai/send-email', {
      method: 'POST',
      body: JSON.stringify({ company_id: companyId }),
    }),
};
