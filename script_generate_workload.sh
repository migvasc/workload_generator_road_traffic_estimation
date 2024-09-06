
rm -rf output
mkdir output
python3 generate_workload.py 'Toulouse, France' 0 2 3 'toulouse-computing-nodes.csv' 'output' &
python3 generate_workload.py 'Toulouse, France' 2 2 3 'toulouse-computing-nodes.csv' 'output' &
python3 generate_workload.py 'Toulouse, France' 4 2 3 'toulouse-computing-nodes.csv' 'output' &
python3 generate_workload.py 'Toulouse, France' 6 2 3 'toulouse-computing-nodes.csv' 'output' &
python3 generate_workload.py 'Toulouse, France' 8 2 3 'toulouse-computing-nodes.csv' 'output' &
wait
echo "Finished!"