.PHONY: install run test clean

install:
	python -m pip install -r requirements.txt

run:
	python -m uvicorn api.main:app --reload

test:
	python -m pytest

clean:
	python -c "from pathlib import Path; import shutil; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('__pycache__')]; [p.unlink() for p in Path('.').rglob('*.pyc')]"
