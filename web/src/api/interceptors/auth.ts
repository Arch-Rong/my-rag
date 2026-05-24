import { getAccessToken } from '@/lib/auth';

import type { RequestInterceptor } from '../types';

/** 已登录时在请求头附带 JWT */
export const authBearerInterceptor: RequestInterceptor = ({ url, init }) => {
	const token = getAccessToken();
	if (!token) return { url, init };

	const headers = new Headers(init.headers);
	if (!headers.has('Authorization')) {
		headers.set('Authorization', `Bearer ${token}`);
	}
	return { url, init: { ...init, headers } };
};
