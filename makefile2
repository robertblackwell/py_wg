NOC_SHEBANG="--python-shebang='/usr/bin/env python'"
MYNAME="Robert Blackwell"
MYEMAIL="rob@whiteacorn.com"
PROJECT_NAME=xa
LICENSE=gpl-3.0
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

_license:
	licenser -n $(MYNAME) -e $(MYEMAIL) -l "MIT" -p "workgroup"

bumppatch:
	bumpversion --current-version `python setup.py --version` patch

bumpminor:
	bumpversion --current-version `python setup.py --version` minor

bumpmajor:
	bumpversion --current-version `python setup.py --version` major


git_push: git_commit
	git push origin master

git_commit:
	git add -A
	git commit -a

git_list_tags:
	git show-ref --tags -d