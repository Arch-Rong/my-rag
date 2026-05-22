import { apiClient } from '../client';

export type AgentChatRequest = {
	message: string;
	thread_id?: string | null;
};

export type AgentChatResponse = {
	reply: string;
	raw_message_count: number;
};

/** 智能问答 */
export function agentChat(message: string, options?: { threadId?: string }) {
	return apiClient.post<AgentChatResponse>('/api/v1/agent/chat', {
		message,
		thread_id: options?.threadId ?? null,
	});
}
