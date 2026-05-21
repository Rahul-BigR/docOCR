import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, AreaChart, Area, CartesianGrid
} from 'recharts';
import {
  TrendingUp, FileStack, IndianRupee, CheckCircle2,
  BarChart3, PieChartIcon, RefreshCw, AlertCircle
} from 'lucide-react';
import styles from './AnalyticsPage.module.css';

const FIELD_COLORS = {
  cheque_number:  '#818cf8',
  account_number: '#34d399',
  ifsc_code:      '#60a5fa',
  amount:         '#f59e0b',
  date:           '#f472b6',
  payee_name:     '#a78bfa',
};

const FIELD_LABELS = {
  cheque_number:  'Cheque No.',
  account_number: 'Account No.',
  ifsc_code:      'IFSC Code',
  amount:         'Amount',
  date:           'Date',
  payee_name:     'Payee Name',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className={styles.tooltip}>
      <p className={styles.tooltipLabel}>{label || payload[0]?.name}</p>
      <p className={styles.tooltipVal}>{payload[0]?.value}</p>
    </div>
  );
};

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/analytics');
      setData(res.data);
    } catch {
      setError('Failed to load analytics data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>Analytics</h1>
        </div>
        <div className={styles.loadingGrid}>
          {[1,2,3,4].map(i => <div key={i} className={styles.skeleton} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.errorBox}>
          <AlertCircle size={16} /> {error}
        </div>
      </div>
    );
  }

  const {
    total_documents,
    total_amount,
    avg_amount,
    max_amount,
    fields_found,
    amount_distribution = [],
    trend = [],
    payee_breakdown = [],
  } = data || {};

  const barData = Object.entries(fields_found || {}).map(([key, val]) => ({
    name: FIELD_LABELS[key] || key,
    value: val,
    fill: FIELD_COLORS[key] || '#6366f1',
  }));

  const pieData = barData.filter(d => d.value > 0);

  const detectionRate = total_documents
    ? Math.round(
        Object.values(fields_found || {}).reduce((a, b) => a + b, 0) /
        (total_documents * 6) * 100
      )
    : 0;

  const metrics = [
    {
      label: 'Total Documents',
      value: total_documents || 0,
      icon: FileStack,
      color: 'indigo',
      sub: 'processed so far',
    },
    {
      label: 'Total Amount',
      value: total_amount ? `₹${Number(total_amount).toLocaleString()}` : '₹0',
      icon: IndianRupee,
      color: 'amber',
      sub: 'extracted from cheques',
    },
    {
      label: 'Avg. Amount',
      value: avg_amount ? `₹${Number(avg_amount).toLocaleString()}` : '₹0',
      icon: TrendingUp,
      color: 'green',
      sub: 'per cheque',
    },
    {
      label: 'Highest Amount',
      value: max_amount ? `₹${Number(max_amount).toLocaleString()}` : '₹0',
      icon: CheckCircle2,
      color: 'rose',
      sub: `${detectionRate}% field detection`,
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Analytics</h1>
          <p className={styles.subtitle}>Insights across all processed documents</p>
        </div>
        <button className={styles.refreshBtn} onClick={fetchData}>
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {/* Metric cards */}
      <div className={styles.metricGrid}>
        {metrics.map(({ label, value, icon: Icon, color, sub }) => (
          <div className={`${styles.metricCard} ${styles[color]}`} key={label}>
            <div className={styles.metricTop}>
              <span className={styles.metricLabel}>{label}</span>
              <div className={styles.metricIconWrap}>
                <Icon size={16} strokeWidth={2} />
              </div>
            </div>
            <div className={styles.metricValue}>{value}</div>
            <div className={styles.metricSub}>{sub}</div>
          </div>
        ))}
      </div>

      {total_documents === 0 ? (
        <div className={styles.empty}>
          <BarChart3 size={48} strokeWidth={1} style={{ color: 'var(--border-light)' }} />
          <p>No data yet — process some documents to see charts</p>
        </div>
      ) : (
        <div className={styles.chartsGrid}>
          {/* Bar chart */}
          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <BarChart3 size={16} style={{ color: 'var(--indigo)' }} />
              <span className={styles.chartTitle}>Field Detection Count</span>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#4b5563', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#4b5563', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.06)' }} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={48}>
                  {barData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Amount distribution */}
          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <BarChart3 size={16} style={{ color: 'var(--indigo)' }} />
              <span className={styles.chartTitle}>Amount Distribution</span>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={amount_distribution} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                <XAxis dataKey="range" tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.06)' }} />
                <Bar dataKey="count" fill="#34d399" radius={[6, 6, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Trend */}
          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <TrendingUp size={16} style={{ color: 'var(--green)' }} />
              <span className={styles.chartTitle}>Amount Over Time</span>
            </div>
            {trend.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={trend} margin={{ top: 8, right: 8, left: -6, bottom: 0 }}>
                  <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="amount" stroke="#818cf8" fill="rgba(129,140,248,0.18)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className={styles.noData}>No valid date data to display</div>
            )}
          </div>

          {/* Payees */}
          <div className={`${styles.chartCard} ${styles.chartWide}`}>
            <div className={styles.chartHeader}>
              <PieChartIcon size={16} style={{ color: '#f59e0b' }} />
              <span className={styles.chartTitle}>Top Payees by Amount</span>
            </div>
            {payee_breakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={payee_breakdown}
                  layout="vertical"
                  margin={{ top: 8, right: 22, left: 30, bottom: 0 }}
                >
                  <XAxis type="number" tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis dataKey="payee" type="category" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} width={120} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(245,158,11,0.06)' }} />
                  <Bar dataKey="amount" fill="#f59e0b" radius={[0, 6, 6, 0]} maxBarSize={26} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className={styles.noData}>No payee data to display</div>
            )}
          </div>

          {/* Pie chart */}
          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <PieChartIcon size={16} style={{ color: 'var(--indigo)' }} />
              <span className={styles.chartTitle}>Field Distribution</span>
            </div>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="45%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    formatter={(value) => (
                      <span style={{ color: '#64748b', fontSize: '0.78rem' }}>{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className={styles.noData}>No field data to display</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
