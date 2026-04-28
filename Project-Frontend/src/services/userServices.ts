import apiClient from "../api/apiClients";

export type User = { user_id: number; user_name: string; user_email: string };
export type UserCreate = { user_name: string; user_email: string };
export type UserUpdate = Partial<UserCreate>;

export const getUsers = () => apiClient.get("/api/users");
export const getUser = (id: number) => apiClient.get(`/api/users/${id}`);
export const createUser = (data: UserCreate) => apiClient.post("/api/users", data);
export const updateUser = (id: number, data: UserUpdate) => apiClient.put(`/api/users/${id}`, data);
export const deleteUser = (id: number) => apiClient.delete(`/api/users/${id}`);