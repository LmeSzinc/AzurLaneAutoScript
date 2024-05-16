.PHONY: clean pack

RM = -rmdir /S /Q
CMAKE = cmake

all: clean pack

pack:
	$(CMAKE) -B build
	$(CMAKE) --build build
	$(CMAKE) --install build
	$(CMAKE) --build build --target package

clean:
	$(RM) build
	$(RM) pack
	$(RM) install