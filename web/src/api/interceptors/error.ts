import { ApiError, type ErrorInterceptor } from '../types';

/** 网络层失败（后端未启动、代理错误等） */
export const networkErrorInterceptor: ErrorInterceptor = ({ url, error }) => {
	if (error instanceof ApiError) throw error;

	const message =
		error instanceof TypeError
			? '无法连接后端，请确认 FastAPI 已启动且代理配置正确'
			: error instanceof Error
				? error.message
				: '未知网络错误';

	throw new ApiError(message, 0, url);
};
