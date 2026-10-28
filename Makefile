.PHONY: build test test-unit

build:
	python3 tools/build.py

test-unit:
	python3 -m unittest discover -s tests -v

test: test-unit
	test -f build/artifacts/manifest.json
	mkdir -p build/bin
	$(CC) -Wall -Wextra -Werror -o build/bin/probe tests/probe.c $$(pkg-config --cflags --libs gutenprint) -lm
	LC_ALL=C STP_DATA_PATH="$(CURDIR)/build/artifacts/xml" build/bin/probe
	LC_ALL=C cupstestppd build/artifacts/ppd/*.ppd > build/ppd-check.log
