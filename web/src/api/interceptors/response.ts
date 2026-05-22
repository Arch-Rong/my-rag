import { ApiError, type ResponseInterceptor } from '../types';

/** 解析 FastAPI 错误体 */
export async function parseErrorMessage(res: Response): Promise<string> {
	try {
		const data = await res.json();
		if (typeof data.detail === 'string') return data.detail;
		if (Array.isArray(data.detail)) {
			return data.detail
				.map((d: { msg?: string }) => d.msg)
				.filter(Boolean)
				.join('；');
		}
	} catch {
		// ignore
	}
	return res.statusText || `HTTP ${res.status}`;
}

/** 非 2xx 时抛 ApiError */
export const httpErrorInterceptor: ResponseInterceptor = async (ctx) => {
	if (!ctx.response.ok) {
		throw new ApiError(
			await parseErrorMessage(ctx.response),
			ctx.response.status,
			ctx.url,
		);
	}
	return ctx;
};

/** 开发环境打印响应状态 */
export const devLogResponseInterceptor: ResponseInterceptor = (ctx) => {
	if (process.env.NODE_ENV === 'development') {
		console.debug('[api] ←', ctx.response.status, ctx.url);
	}
	return ctx;
};
