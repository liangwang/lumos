PYTHONLIB_TARGET = _cacti.so
TARGET = cacti
SHELL = /bin/sh
.PHONY: all depend clean
.SUFFIXES: .cc .o

NPROCS := 1
OS := $(shell uname)
export NPROCS

ifeq ($(OS),Linux)
  NPROCS := $(shell grep -c ^processor /proc/cpuinfo)
else ifeq ($(OS),Darwin)
  NPROCS := $(shell sysctl hw.ncpu | awk '{print $$2}')
endif # $(OS)

ifeq ($(NUMPROC),0)
  NUMPROC = 1
endif 

ifndef NTHREADS
  NTHREADS = $(NPROCS)
endif


LIBS = -lm $(shell pkg-config --libs python3)
INCS = $(shell pkg-config --cflags python3)

ifeq ($(TAG),dbg)
  DBG = -Wall 
  OPT = -ggdb -g -O0 -DNTHREADS=1  -gstabs+
else
  DBG = 
  # OPT = -O3 -msse2 -mfpmath=sse -DNTHREADS=$(NTHREADS)
  OPT = -O3 -mtune=native -march=native -DNTHREADS=$(NTHREADS)
endif

#CXXFLAGS = -Wall -Wno-unknown-pragmas -Winline $(DBG) $(OPT) 
CXXFLAGS = -Wno-unknown-pragmas -fPIC $(DBG) $(OPT) $(INCS)
# CXX = g++ -m32
# CC  = gcc -m32

SRCS  = area.cc bank.cc mat.cc main.cc Ucache.cc io.cc technology.cc basic_circuit.cc parameter.cc \
		decoder.cc component.cc uca.cc subarray.cc wire.cc htree2.cc \
		cacti_interface.cc router.cc nuca.cc crossbar.cc arbiter.cc powergating.cc
PYTHONLIB_SRCS = $(patsubst main.cc, ,$(SRCS)) cacti_wrap.cc

OBJS = $(patsubst %.cc,obj_$(TAG)/%.o,$(SRCS))
PYTHONLIB_OBJS = $(patsubst %.cc,obj_$(TAG)/%.o,$(PYTHONLIB_SRCS)) 

all: obj_$(TAG)/$(PYTHONLIB_TARGET)

obj_$(TAG)/$(PYTHONLIB_TARGET) : $(PYTHONLIB_OBJS)
	$(CXX) $(PYTHONLIB_OBJS) -shared -o $@ $(CXXFLAGS) $(LIBS) -pthread

obj_$(TAG)/%.o : %.cc
	$(CXX) $(CXXFLAGS) -c $< -o $@

cacti_wrap.cc : cacti.i cacti_interface.h
	swig -c++ -python -o $@ cacti.i

clean:
	-rm -f cacti_wrap.cc cacti.py
