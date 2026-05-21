AI Knowledge Studio
。技术栈 Electron + React+TypeScript + Zustand+Dexie + Node,jis + LangChain.js + Vector Search + SQLite + Worker
Threads
一款基于Electron的本地优先AI知识工作台,支持本地文件实l时索引、离线RAG检索、AI辅助编辑与多窗口协
作。通过深度整合系统能力与大模型,实现"无需上传数据"的高隐私知识管理体验。

。技术栈:Electron+React+TypeScript+Zustand+Dexie+SQLite+LangChain.js + Vector Search
。项目简介:一款本地优先的AI知识工作台,基于Electron深度整合操作系统能力,实现本地文件实时索引、离
线RAG检索与AI辅助编辑,支持多窗口协作与高隐私数据气管理。
本地文件智能索引与增量更新:基于chokidar监听文件系统列变化,支持PDF/Word/Markdown自动解析与语义
切片;通过文件hash+chunk级dif实现向量库增量更新,避免全量重建带来的性能开销
离线优先RAG引擎:构建基于SQLite的本地向量检索系统,支持无网络环境下的语义搜索;设计在线/离线双
通道embedding fallback机制,提升系统稳定性与可用性
AI+编辑器深度融合:在富文本编辑器中实现选区级AI改写、跨文档引用与溯源高亮能力,增强知识消费与生
产效率多窗口协同与状态同步:基于ElectronIPC构建跨窗|口通信机制,结合Zustand实现多窗口状态共享与实
时同步,提升复杂工作流下的交互效率
。多线程性能优化:利用Worker Threads处理文档解析-与向量化任务,将高耗时计算从主线程剥离,保障界面子交
互流畅性 Local-First数据架构:构建IndexedDB+SQLite+FileSystem三层数据存储体系,实现UI状态、结构化
数据与原始文件的分层管理
