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
  getSites: () => request('/scrape/sites'),
  startScraping: (slug) => request(`/scrape/${slug}`, { method: 'POST' }),
  getScrapingStatus: (jobId) => request(`/scrape/status/${jobId}`),
  generateEmail: (companyId) =>
    request('/ai/generate-email', {
      method: 'POST',
      body: JSON.stringify({ company_id: companyId }),
    }),
  generateCV: (companyId) =>
    request('/ai/generate-cv', {
      method: 'POST',
      body: JSON.stringify({ company_id: companyId }),
    }),
};
