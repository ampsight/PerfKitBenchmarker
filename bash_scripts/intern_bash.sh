#!/bin/bash
NUM_TESTS_TO_RUN=3
for ((i=0; i<NUM_TESTS_TO_RUN; i++));
do
    perfkitbenchmarker/pkb.py --benchmarks=coremark --cloud=AWS --benchmark_config_file=intern_testing_config.yaml --ip_addresses=EXTERNAL
done
mkdir /tmp/perkitbenchmarker/output
python /tmp/perfkitbenchmarker/pkb_script_final.py