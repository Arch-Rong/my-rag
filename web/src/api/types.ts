/** 单次请求的上下文（给拦截器用） */
export type RequestContext = {
	url: string;
	init: RequestInit;
};

export type ResponseContext = RequestContext & {
	response: Response;
};

export type ErrorContext = RequestContext & {
	error: unknown;
};

/** 请求拦截：在 fetch 之前改 URL / headers / body */
export type RequestInterceptor = (
	ctx: RequestContext,
) => RequestContext | Promise<RequestContext>;

/** 响应拦截：在 fetch 之后、解析 JSON 之前处理 Response */
export type ResponseInterceptor = (
	ctx: ResponseContext,
) => ResponseContext | Promise<ResponseContext>;

/** 错误拦截：网络失败或业务抛错时统一处理 */
export type ErrorInterceptor = (
	ctx: ErrorContext,
) => never | Promise<never>;

export type ApiRequestOptions = Omit<RequestInit, 'body'> & {
	/** 相对路径，如 /api/v1/agent/chat */
	path: string;
	body?: unknown;
	/** 跳过 JSON 序列化，直接传 RequestInit.body */
	rawBody?: BodyInit | null;
	params?: Record<string, string | number | boolean | undefined | null>;
};

export class ApiError extends Error {
	status: number;
	url: string;

	constructor(message: string, status: number, url: string) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.url = url;
	}
}
