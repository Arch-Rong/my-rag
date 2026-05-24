import { apiClient } from '../client';

export type AgentScope = 'all' | 'system_only' | 'user_only';

export type AgentChatRequest = {
	message: string;
	thread_id?: string | null;
	scope?: AgentScope;
};

export type CitationItem = {
	id: string;
	label: string;
	excerpt: string;
};

export type AgentChatResponse = {
	reply: string;
	raw_message_count: number;
	scope: AgentScope;
	citations: CitationItem[];
};

/** 智能问答（scope：全部 / 教材 / 我的） */
export function agentChat(
	message: string,
	options?: { threadId?: string; scope?: AgentScope },
) {
	return apiClient.post<AgentChatResponse>('/api/v1/agent/chat', {
		message,
		thread_id: options?.threadId ?? null,
		scope: options?.scope ?? 'all',
	});
}
