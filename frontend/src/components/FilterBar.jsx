import { useEffect, useRef, useState } from 'react';
import { Search } from 'lucide-react';

const STATUS_OPTIONS = [
  { value: '', label: 'Tüm Durumlar' },
  { value: 'not_applied', label: 'Başvurulmadı' },
  { value: 'applied', label: 'Başvuruldu' },
  { value: 'interview', label: 'Mülakat' },
  { value: 'rejected', label: 'Reddedildi' },
  { value: 'accepted', label: 'Kabul Edildi' },
];

function FilterBar({ filters, onFilterChange, sources = [] }) {
  const [searchValue, setSearchValue] = useState(filters.search ?? '');
  const debounceRef = useRef(null);

  useEffect(() => {
    setSearchValue(filters.search ?? '');
  }, [filters.search]);

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchValue(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onFilterChange({ ...filters, search: value });
    }, 300);
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const handleSourceChange = (e) => {
    onFilterChange({ ...filters, source: e.target.value });
  };

  const handleStatusChange = (e) => {
    onFilterChange({ ...filters, status: e.target.value });
  };

  const handleClear = () => {
    setSearchValue('');
    onFilterChange({ search: '', source: '', status: '' });
  };

  return (
    <div className="filter-bar">
      <div className="filter-search">
        <Search size={16} className="filter-search-icon" />
        <input
          type="text"
          className="input"
          placeholder="Şirket ara..."
          value={searchValue}
          onChange={handleSearchChange}
        />
      </div>

      <select
        className="input filter-select"
        value={filters.source ?? ''}
        onChange={handleSourceChange}
      >
        <option value="">Tüm Kaynaklar</option>
        {sources.map((source) => (
          <option key={source} value={source}>
            {source}
          </option>
        ))}
      </select>

      <select
        className="input filter-select"
        value={filters.status ?? ''}
        onChange={handleStatusChange}
      >
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <button type="button" className="btn btn-ghost" onClick={handleClear}>
        Temizle
      </button>
    </div>
  );
}

export default FilterBar;
