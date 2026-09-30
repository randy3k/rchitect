all:

clean:
	rm -rf build dist *.egg-info .pytest_cache rchitect/host.exe && \
	find . -name '*.so' -not -path './.venv/*' -exec rm -rf {} \; && \
	find . -name '*.pyd' -not -path './.venv/*' -exec rm -rf {} \; && \
	find . -name '*.o' -not -path './.venv/*' -exec rm -rf {} \; && \
	find . -name '*.pyc' -not -path './.venv/*' -exec rm -rf {} \;

