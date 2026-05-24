import type { UserResponse } from '@/api/endpoints/auth';

export function getUserInitials(user: UserResponse | null): string {
	if (!user) return '?';
	const name = user.display_name?.trim();
	if (name) {
		const parts = name.split(/\s+/).filter(Boolean);
		if (parts.length >= 2) {
			return (parts[0][0] + parts[1][0]).toUpperCase();
		}
		return name.slice(0, 2).toUpperCase();
	}
	const email = user.email?.trim();
	if (email) {
		const local = email.split('@')[0] ?? email;
		return local.slice(0, 2).toUpperCase();
	}
	return '?';
}

export function getUserDisplayName(user: UserResponse | null): string {
	if (!user) return '用户';
	if (user.display_name?.trim()) return user.display_name.trim();
	if (user.email) return user.email.split('@')[0] ?? user.email;
	return '用户';
}
