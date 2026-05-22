import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

app = FastAPI(title='MedRAG API', version='0.1.0')

_cors_origins = os.getenv(
	'CORS_ORIGINS',
	'http://localhost:3000,http://127.0.0.1:3000',
).split(',')

app.add_middleware(
	CORSMiddleware,
	allow_origins=[o.strip() for o in _cors_origins if o.strip()],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

app.include_router(api_router)


@app.get('/')
def read_root():
	return {'Hello': 'World'}


@app.get('/health')
def health():
	return {'status': 'ok', 'service': 'medrag-server'}


@app.get('/items/{item_id}')
def read_item(item_id: int, q: str | None = None):
	return {'item_id': item_id, 'q': q}
