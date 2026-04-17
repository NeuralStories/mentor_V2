.PHONY: install run test test-unit test-e2e test-fast clean

install:
	python -m pip install -r requirements.txt

run:
	python -m uvicorn api.main:app --host 127.0.0.1 --port 8765 --reload

test:
	pytest -v

test-unit:
	pytest tests/test_parser_unit.py tests/test_store_unit.py -v

test-e2e:
	pytest tests/test_ingestion_e2e.py -v

test-fast:
	pytest -v -m "not requires_tesseract"

clean:
	python -c "from pathlib import Path; import shutil; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('__pycache__')]; [p.unlink() for p in Path('.').rglob('*.pyc')]"
