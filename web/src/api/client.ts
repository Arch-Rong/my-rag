import {
	devLogRequestInterceptor,
	jsonContentTypeInterceptor,
} from './interceptors/request';
import {
	devLogResponseInterceptor,
	httpErrorInterceptor,
} from './interceptors/response';
import { networkErrorInterceptor } from './interceptors/error';
import type {
	ApiRequestOptions,
	ErrorInterceptor,
	RequestInterceptor,
	ResponseInterceptor,
} from './types';

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? '/backend').replace(
	/\/$/,
	'',
);

function buildUrl(path: string, params?: ApiRequestOptions['params']): string {
	const normalized = path.startsWith('/') ? path : `/${path}`;
	const full = path.startsWith('http') ? path : `${API_BASE}${normalized}`;

	if (!params) return full;

	const search = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null) {
			search.set(key, String(value));
		}
	}
	const q = search.toString();
	return q ? `${full}?${q}` : full;
}

export class ApiClient {
	private requestInterceptors: RequestInterceptor[] = [];
	private responseInterceptors: ResponseInterceptor[] = [];
	private errorInterceptors: ErrorInterceptor[] = [];

	constructor() {
		this.useRequest(jsonContentTypeInterceptor);
		this.useRequest(devLogRequestInterceptor);
		this.useResponse(devLogResponseInterceptor);
		this.useResponse(httpErrorInterceptor);
		this.useError(networkErrorInterceptor);
	}

	useRequest(interceptor: RequestInterceptor) {
		this.requestInterceptors.push(interceptor);
		return this;
	}

	useResponse(interceptor: ResponseInterceptor) {
		this.responseInterceptors.push(interceptor);
		return this;
	}

	useError(interceptor: ErrorInterceptor) {
		this.errorInterceptors.push(interceptor);
		return this;
	}

	private async runRequestInterceptors(ctx: {
		url: string;
		init: RequestInit;
	}) {
		let current = ctx;
		for (const fn of this.requestInterceptors) {
			current = await fn(current);
		}
		return current;
	}

	private async runResponseInterceptors(ctx: {
		url: string;
		init: RequestInit;
		response: Response;
	}) {
		let current = ctx;
		for (const fn of this.responseInterceptors) {
			current = await fn(current);
		}
		return current;
	}

	private async runErrorInterceptors(ctx: {
		url: string;
		init: RequestInit;
		error: unknown;
	}): Promise<never> {
		let current = ctx;
		for (const fn of this.errorInterceptors) {
			await fn(current);
		}
		throw current.error;
	}

	async request<T>(options: ApiRequestOptions): Promise<T> {
		const { path, body, rawBody, params, ...init } = options;

		const initWithBody: RequestInit = {
			...init,
			body:
				rawBody !== undefined
					? rawBody
					: body !== undefined
						? JSON.stringify(body)
						: undefined,
		};

		let ctx = await this.runRequestInterceptors({
			url: buildUrl(path, params),
			init: initWithBody,
		});

		let response: Response;
		try {
			response = await fetch(ctx.url, ctx.init);
		} catch (error) {
			return this.runErrorInterceptors({ ...ctx, error });
		}

		try {
			const after = await this.runResponseInterceptors({
				...ctx,
				response,
			});
			if (after.response.status === 204) {
				return undefined as T;
			}
			return (await after.response.json()) as T;
		} catch (error) {
			return this.runErrorInterceptors({ ...ctx, error });
		}
	}

	get<T>(path: string, options?: Omit<ApiRequestOptions, 'path' | 'body'>) {
		return this.request<T>({ ...options, path, method: 'GET' });
	}

	post<T>(
		path: string,
		body?: unknown,
		options?: Omit<ApiRequestOptions, 'path' | 'body'>,
	) {
		return this.request<T>({ ...options, path, method: 'POST', body });
	}
}

/** 默认单例，业务模块通过它发请求 */
export const apiClient = new ApiClient();
