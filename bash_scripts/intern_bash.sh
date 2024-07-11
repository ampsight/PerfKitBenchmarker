#!/bin/bash
NUM_TESTS_TO_RUN=3
for ((i=0; i<NUM_TESTS_TO_RUN; i++));
do
    perfkitbenchmarker/pkb.py --benchmarks=coremark --cloud=AWS --benchmark_config_file=intern_testing_config.yaml --ip_addresses=EXTERNAL
done
mkdir /tmp/perkitbenchmarker/output
#Line below assumes that the python script must be in the correct directory
#tmp -> perfkitbenchmarker -> output & runs & pkb_script_final.py
#output folder contains the csv's of data and calculations results for each benchmark
#runs folder contains all the runs and results json's
python /tmp/perfkitbenchmarker/pkb_script_final.py