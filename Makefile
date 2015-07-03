
install:
	sudo python setup.py install

clean:
	 sudo rm -rf build dist softsynth.egg-info

register:
	python setup.py register 

tag:
	git tag $$(python setup.py --version)

upload: register
	python setup.py sdist bdist bdist_dumb upload

release: clean upload tag
