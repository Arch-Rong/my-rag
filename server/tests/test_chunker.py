"""LangChain 结构分片单元测试。"""

from app.ingest.pipeline import chunk_file_content
from app.ingest.splitters.langchain import chunk_markdown
from app.ingest.tokens import estimate_tokens

SAMPLE_MD = """# 内科学

## 高血压

高血压是以体循环动脉压升高为主要表现的临床综合征。

### 诊断标准

收缩压 ≥140mmHg 或舒张压 ≥90mmHg。

## 糖尿病

糖尿病是一组由多病因引起的代谢性疾病。
"""


def test_chunk_markdown_section_metadata() -> None:
	chunks = chunk_markdown(SAMPLE_MD)
	assert len(chunks) >= 2
	assert any(
		draft.metadata.get('section') == '高血压'
		or '高血压' in draft.content
		for draft in chunks
	)
	assert all(draft.metadata.get('source_format') == 'markdown' for draft in chunks)


def test_chunk_markdown_respects_structure() -> None:
	chunks = chunk_markdown(SAMPLE_MD, max_tokens=512, overlap_tokens=32)
	assert len(chunks) >= 2
	for draft in chunks:
		assert draft.content.strip()
		assert draft.token_count > 0
		assert 'chunk_index' in draft.metadata


def test_chunk_markdown_splits_long_section() -> None:
	long_body = '这是测试句。' * 400
	md = f'# 第一章\n\n## 超长节\n\n{long_body}'
	chunks = chunk_markdown(md, max_tokens=80, overlap_tokens=16)
	assert len(chunks) > 1
	for draft in chunks:
		assert estimate_tokens(draft.content) <= 120


def test_chunk_file_content_md_bytes() -> None:
	chunks = chunk_file_content(SAMPLE_MD.encode('utf-8'), 'notes.md')
	assert len(chunks) >= 2
