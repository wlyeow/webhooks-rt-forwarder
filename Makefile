SITE=$(shell python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')
CWD=$(shell pwd)

upload.zip: $(SITE) lambda_function.py
	-@rm $@
	(cd $<; zip -r9 $(CWD)/$@ -x@$(CWD)/upload-exclude.lst .)
	zip -u $@ $(filter-out $<,$^)

