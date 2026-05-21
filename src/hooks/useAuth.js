import { useState, useEffect } from 'react';
import api from '../lib/api';

export function useAuth() {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('docr_user')); } catch { return null; }
  });
  const [loading, setLoading] = useState(false);

  const login = async (username, password) => {
    const res = await api.post('/auth/login', { username, password });
    localStorage.setItem('docr_token', res.data.token);
    localStorage.setItem('docr_user', JSON.stringify(res.data.user));
    setUser(res.data.user);
    return res.data;
  };

  const register = async (username, password) => {
    const res = await api.post('/auth/register', { username, password });
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('docr_token');
    localStorage.removeItem('docr_user');
    setUser(null);
  };

  return { user, login, register, logout, loading };
}
