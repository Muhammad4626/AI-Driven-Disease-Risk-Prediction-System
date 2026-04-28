import apiClient from '../api/apiClients';
import { User } from './userServices';

const ACCESS_TOKEN_KEY = 'access_token';

export type AuthResponse = {
  access_token: string;
  token_type: 'bearer';
  user: User;
};

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await apiClient.post('/api/auth/login', { email, password });
  localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
  return response;
};

export const register = async (name: string, email: string, password: string): Promise<AuthResponse> => {
  const response = await apiClient.post('/api/auth/register', { name, email, password });
  localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
  return response;
};

export const logout = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
};

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);

export const isAuthenticated = () => !!getAccessToken();

export const getCurrentUser = async () => apiClient.get('/api/auth/me');
