/**
 * MedRAG 学习主题说明
 *
 * 颜色在 `src/app/globals.css` 的 `:root` / `.dark` 中定义；
 * 页面请用 Tailwind 语义类：`bg-background`、`text-primary`、`bg-primary/10` 等。
 *
 * 浅色基调：纯白背景 + 柔和青绿主色（干净、对比清晰）
 */
export const MED_RAG_THEME = {
	name: '自习室',
	cssPath: 'src/app/globals.css',
	/** 主色色相 oklch 第三参数，与 globals 中 --primary 一致 */
	primaryHue: 172,
} as const;
