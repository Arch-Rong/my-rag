export default function ChatLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return <div className='flex min-h-0 flex-1 flex-col'>{children}</div>;
}

// console.log('stack [1]');

// setTimeout(() => console.log('macro [2]'), 0);

// setTimeout(() => console.log('macro [3]'), 1);

// const p = Promise.resolve();

// for (let i = 0; i < 3; i++) {
// 	p.then(() => {
// 		setTimeout(() => {
// 			console.log('stack [4]');

// 			setTimeout(() => console.log('macro [5]'), 0);

// 			p.then(() => console.log('micro [6]'));
// 		}, 0);

// 		console.log('stack [7]');
// 	});
// }

// console.log('stack [8]');

// // 前端 大模型 思考过程 AI分析 过程 结构组件
// // 后端 大模型 思考过程 AI分析 过程 结构组件

// // // 前端 大模型 思考过程 AI分析 过程 结构组件
// // 后端 大模型 思考过程 AI分析 过程 结构组件
