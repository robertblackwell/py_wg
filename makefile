NOC_SHEBANG="--python-shebang='/usr/bin/env python'"

PREFIX=$(HOME)/.local


install:
	python setup.py install --prefix=$(PREFIX) 

clean:
	python setup.py clean
	rm -rfv ./build
	rm *whl 
	rm *.pex

push:
	git status
	git add -A
	git commit -a
