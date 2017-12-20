
PREFIX=$(HOME)/.local


install:
	python setup.py install --prefix=$(PREFIX) 

pex:
	pip wheel -w . .	
	pex -f $PWD MySQL-python ./ -e ipq.ipq:main $(RB_SHEBANG) -o xa.pex --disable-cache


clean:
	python setup.py clean
	rm -rfv ./build
	rm *whl 
	rm *.pex

push:
	git status
	git add -A
	git commit -a
