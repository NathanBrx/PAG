all: facteur/build/facteur chinese-postman-problem/chinese
	python3 cpp.py && ./facteur/build/facteur

facteur/build/facteur: facteur/*.cpp facteur/*.h
	/usr/bin/cmake --build "facteur/build" --config Debug --target all -j 6 --

chinese-postman-problem/chinese:
	cd chinese-postman-problem && make chinese

cleanchinese:
	cd chinese-postman-problem && make clean

cleanfacteur:
	cd facteur && rm -rf build/facteur

clean: cleanchinese cleanfacteur

fresh: clean all