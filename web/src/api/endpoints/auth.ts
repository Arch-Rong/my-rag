import { apiClient } from '../client';

export type AuthResponse = {
	access_token: string;
	token_type: string;
	id: string;
	email: string;
	display_name: string | null;
};

export type UserResponse = {
	id: string;
	email: string | null;
	display_name: string | null;
	created_at: string;
};

export type LoginRequest = {
	email: string;
	password: string;
};

export function login(body: LoginRequest) {
	return apiClient.post<AuthResponse>('/api/v1/auth/login', body);
}

export function register(body: LoginRequest & { display_name?: string }) {
	return apiClient.post<AuthResponse>('/api/v1/auth/register', body);
}

export function fetchMe() {
	return apiClient.get<UserResponse>('/api/v1/auth/me');
}
