/**
 * API 统一入口
 *
 * 目录说明：
 * - client.ts       请求客户端 + 拦截器链
 * - types.ts        类型与 ApiError
 * - interceptors/   请求 / 响应 / 错误拦截器
 * - endpoints/      按业务拆分的接口方法
 *
 * 扩展方式：
 *   import { apiClient } from '@/lib/api';
 *   apiClient.useRequest(yourInterceptor);
 */

export { apiClient, ApiClient } from './client';
export { ApiError } from './types';
export type {
	RequestInterceptor,
	ResponseInterceptor,
	ErrorInterceptor,
	ApiRequestOptions,
} from './types';

export { agentChat } from './endpoints/agent';
export type { AgentChatResponse, AgentChatRequest } from './endpoints/agent';

export { healthCheck } from './endpoints/health';
export type { HealthResponse } from './endpoints/health';
