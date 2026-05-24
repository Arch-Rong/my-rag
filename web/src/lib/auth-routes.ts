/** 无顶栏的认证页路径 */
export const AUTH_PATHS = ['/login', '/register'] as const;

export function isAuthPath(pathname: string): boolean {
	return AUTH_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

/** 登录后安全跳转，避免开放重定向 */
export function getSafeRedirect(from: string | null | undefined): string {
	if (!from || !from.startsWith('/') || from.startsWith('//')) {
		return '/library';
	}
	if (isAuthPath(from)) return '/library';
	return from;
}
