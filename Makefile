SITE=$(shell python3 -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')
CWD=$(shell pwd)
CERT_BUNDLE=certs/

RT_GIT_REPO?=https://raw.githubusercontent.com/CZ-NIC/python-rt
RT_GIT_BRANCH?=master

upload.zip: $(SITE) lambda_function.py rt.py
	-@rm $@
	(cd $<; zip -r9 $(CWD)/$@ -i@$(CWD)/upload-include.lst -x@$(CWD)/upload-exclude.lst .)
	-(cd $(CERT_BUNDLE); zip -u $(CWD)/$@ *.crt)
	zip -u $@ $(filter-out $<,$^)

rt.py:
	curl $(RT_GIT_REPO)/$(RT_GIT_BRANCH)/rt.py -o $@
