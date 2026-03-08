import apiClient from "../api/apiClients";

export type User = { id: number; name: string; email: string };
export type UserCreate = { name: string; email: string };
export type UserUpdate = Partial<UserCreate>;

export const getUsers = () => apiClient.get("/users");
export const getUser = (id: number) => apiClient.get(`/users/${id}`);
export const createUser = (data: UserCreate) => apiClient.post("/users", data);
export const updateUser = (id: number, data: UserUpdate) => apiClient.put(`/users/${id}`, data);
export const deleteUser = (id: number) => apiClient.delete(`/users/${id}`);