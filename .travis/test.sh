set -vxe # enable output and stop on errors
conda install -y numpy quantities pytest -c chemreac
conda develop .
py.test -s
