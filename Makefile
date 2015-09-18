.PHONY: all cacti cython clean

all: cacti cython

cacti:
	$(MAKE) -C cacti-p
cython:
	python setup.py build_ext --inplace
clean:
	$(MAKE) -C cacti-p clean
	find lumos -name "*.so" -delete
