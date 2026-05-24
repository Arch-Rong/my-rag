/**
 * MedRAG 学习主题说明
 *
 * 颜色在 `src/app/globals.css` 的 `:root` / `.dark` 中定义；
 * 页面请用 Tailwind 语义类：`bg-background`、`text-primary`、`bg-primary/10` 等。
 *
 * 浅色：纯白底 + 柔和青绿主色。
 * 暗黑：中性石板灰底（低饱和），青绿仅作点缀，减轻长时间学习的视觉疲劳。
 */
export const MED_RAG_THEME = {
	name: '自习室',
	cssPath: 'src/app/globals.css',
	/** 点缀色色相（按钮/链接），背景不跟此色相 */
	primaryHue: 172,
	/** 暗黑背景中性色相（石板灰） */
	darkNeutralHue: 265,
} as const;
