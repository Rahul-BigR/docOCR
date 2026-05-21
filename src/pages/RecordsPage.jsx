import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import {
  LayoutGrid, Search, RefreshCw, Trash2, Download,
  FileJson, Hash, CreditCard, Landmark, IndianRupee,
  Calendar, User, ChevronDown, ChevronUp, AlertCircle
} from 'lucide-react';
import styles from './RecordsPage.module.css';

function getField(record, ...keys) {
  for (const k of keys) {
    if (record[k]) return record[k];
  }
  return '';
}

export default function RecordsPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [exporting, setExporting] = useState(false);

  const fetchRecords = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/records');
      setRecords(res.data.records || []);
    } catch (err) {
      setError('Failed to load records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRecords(); }, []);

  const handleDelete = async (name) => {
    if (!window.confirm(`Delete record "${name}"?`)) return;
    setDeleting(name);
    try {
      await api.delete(`/records/${name}`);
      setRecords(r => r.filter(rec => rec.file !== name));
    } catch {
      alert('Delete failed.');
    } finally {
      setDeleting(null);
    }
  };

  const handleDownload = (record) => {
    const blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${record.file}_ocr.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportAll = async () => {
    setExporting(true);
    try {
      const res = await api.get('/records/export/excel', { responseType: 'blob' });
      const type = res.headers['content-type'] || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      const isCsv = type.includes('csv');
      const blob = new Blob([res.data], { type });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = isCsv ? 'DocOCR_Records.csv' : 'DocOCR_Records.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Excel export failed.');
    } finally {
      setExporting(false);
    }
  };

  const filtered = records.filter(r => {
    const q = search.toLowerCase();
    return [r.file, getField(r,'cheque_number','Cheque_Number'), getField(r,'payee_name','Payee_Name'),
            getField(r,'ifsc_code','IFSC_Code'), getField(r,'account_number','Account_Number')]
      .some(v => (v||'').toLowerCase().includes(q));
  });

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>All Records</h1>
          <p className={styles.subtitle}>{records.length} document{records.length !== 1 ? 's' : ''} processed</p>
        </div>
        <div className={styles.controls}>
          <button className={styles.exportBtn} onClick={handleExportAll} disabled={exporting || records.length === 0}>
            <Download size={15} /> {exporting ? 'Exporting...' : 'Excel'}
          </button>
          <div className={styles.searchWrap}>
            <Search size={15} className={styles.searchIcon} />
            <input
              className={styles.searchInput}
              placeholder="Search records..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button className={styles.refreshBtn} onClick={fetchRecords} disabled={loading}>
            <RefreshCw size={15} className={loading ? styles.spin : ''} />
          </button>
        </div>
      </div>

      {error && (
        <div className={styles.errorBox}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {loading && records.length === 0 && (
        <div className={styles.loadingGrid}>
          {[1,2,3].map(i => <div key={i} className={styles.skeleton} />)}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className={styles.empty}>
          <FileJson size={48} strokeWidth={1} style={{ color: 'var(--border-light)' }} />
          <p>{search ? 'No records match your search' : 'No records yet — analyze a document first'}</p>
        </div>
      )}

      <div className={styles.tableWrap}>
        {filtered.length > 0 && (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Document</th>
                <th><Hash size={13} /> Cheque No.</th>
                <th><CreditCard size={13} /> Account</th>
                <th><Landmark size={13} /> IFSC</th>
                <th><IndianRupee size={13} /> Amount</th>
                <th><Calendar size={13} /> Date</th>
                <th><User size={13} /> Payee</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((record) => {
                const isOpen = expanded === record.file;
                return (
                  <React.Fragment key={record.file}>
                    <tr className={isOpen ? styles.rowActive : ''}>
                      <td>
                        <div className={styles.docCell}>
                          <div className={styles.docIcon}><FileJson size={14} /></div>
                          <span className={styles.docName}>{record.file}</span>
                          <button
                            className={styles.expandBtn}
                            onClick={() => setExpanded(isOpen ? null : record.file)}
                          >
                            {isOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          </button>
                        </div>
                      </td>
                      <td><span className={`${styles.mono} ${styles.chip}`}>{getField(record,'cheque_number','Cheque_Number') || '—'}</span></td>
                      <td><span className={`${styles.mono} ${styles.chip}`}>{getField(record,'account_number','Account_Number') || '—'}</span></td>
                      <td><span className={`${styles.mono} ${styles.chipBlue}`}>{getField(record,'ifsc_code','IFSC_Code') || '—'}</span></td>
                      <td><span className={styles.amountCell}>{getField(record,'amount','Amount') || '—'}</span></td>
                      <td><span className={styles.dateCell}>{getField(record,'date','Date') || '—'}</span></td>
                      <td><span className={styles.payeeCell}>{getField(record,'payee_name','Payee_Name') || '—'}</span></td>
                      <td>
                        <div className={styles.actionRow}>
                          <button className={styles.actionBtn} onClick={() => handleDownload(record)} title="Download JSON">
                            <Download size={14} />
                          </button>
                          <button
                            className={`${styles.actionBtn} ${styles.actionDelete}`}
                            onClick={() => handleDelete(record.file)}
                            disabled={deleting === record.file}
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                    {isOpen && (
                      <tr className={styles.expandedRow}>
                        <td colSpan={8}>
                          <div className={styles.expandedContent}>
                            <pre className={styles.json}>{JSON.stringify(record, null, 2)}</pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
