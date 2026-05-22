import { apiClient } from '../client';

export type HealthResponse = {
	status: string;
	service: string;
};

export function healthCheck() {
	return apiClient.get<HealthResponse>('/health', { cache: 'no-store' });
}
