CITY ?=
POSTMEN ?=

all: facteur chinese run

run :
	python3 cpp.py $(CITY) $(POSTMEN) && ./facteur/build/facteur

facteur: $(shell pwd)/facteur/build/facteur

$(shell pwd)/facteur/build/facteur:
	/usr/bin/cmake --build "$(shell pwd)/facteur/build" --config Debug --target all -j 6 --

chinese:
	cd chinese-postman-problem && make chinese

cleanchinese:
	cd chinese-postman-problem && make clean

cleanfacteur:
	cd facteur && rm -rf build/facteur

clean: cleanchinese cleanfacteur

fresh: clean all