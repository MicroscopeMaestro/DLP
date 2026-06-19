#!/usr/bin/env bash
# Get script directory.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $DIR

if type swig >/dev/null 2>&1; then
    echo "Running swig..."
    swig -c++ -python $DIR/../NIRScanner.i
else
    echo "Did not detect swig, using generated Python Interface."
fi

# Find Python version & set library path.
PYTHON3_VERSION=$(/usr/bin/python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

# Determine python library flag (m suffix removed in Python 3.8+)
PYTHON_LIB="python${PYTHON3_VERSION}"
if [ $(/usr/bin/python3 -c 'import sys; print(1 if sys.version_info < (3, 8) else 0)') -eq 1 ]; then
    PYTHON_LIB="python${PYTHON3_VERSION}m"
fi

# Compile.
gcc -fpic -c $DIR/../*.c
g++ -fpic -c $DIR/../*.cpp
g++ -fpic -c $DIR/../*.cxx -I/usr/include/python${PYTHON3_VERSION}
mkdir -p $DIR/../build
mv ./*.o $DIR/../build
g++ -shared $DIR/../build/*.o -ludev -l${PYTHON_LIB} -o $DIR/../build/_NIRScanner.so.3
cp $DIR/../build/_NIRScanner.so.3 $DIR/../../lib/
cp $DIR/../../lib/_NIRScanner.so.3 $DIR/../../_NIRScanner.so

# Clean .o files.
rm -f $DIR/../build/*.o
