import type { RequestInterceptor } from '../types';

/** 有 body 时自动加 Content-Type: application/json */
export const jsonContentTypeInterceptor: RequestInterceptor = ({
	url,
	init,
}) => {
	const headers = new Headers(init.headers);
	if (
		init.body != null &&
		typeof init.body === 'string' &&
		!headers.has('Content-Type')
	) {
		headers.set('Content-Type', 'application/json');
	}
	return { url, init: { ...init, headers } };
};

/** 开发环境打印请求（可选） */
export const devLogRequestInterceptor: RequestInterceptor = ({ url, init }) => {
	if (process.env.NODE_ENV === 'development') {
		console.debug('[api] →', init.method ?? 'GET', url, init.body ?? '');
	}
	return { url, init };
};
