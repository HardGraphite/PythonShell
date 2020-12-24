module_name=hg_pyshell
python_interpreter=python3

cur_dir=$(pwd)
file_dir=$(dirname $(readlink $0))

cd "${file_dir}" && \
$python_interpreter -m $module_name --working-directory "${cur_dir}" $*
