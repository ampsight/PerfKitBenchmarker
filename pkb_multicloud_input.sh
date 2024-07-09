#!/bin/bash
# Short Script that will run selected test on static VMs based on an input file

# Requirements:
# Must have PerfkitBenchmarker Reposition on your Machine
# Must have authenticated with cloud providers and have appropriate permission  
# Must have virtual environment with python and other requirements

# delimiter for spliting arrays
IFS=' '
# datetime
DT=`date +"%Y-%m-%d-%H:%M:%S"`
# pwd
PWD=`pwd`
# Array of Log file Names
logArr=()
# Array of Table Names
bqtArr=()

# Default Values can be overwritten on the CLI
BENCHMARK="iperf"

# Default Google Project ID 
PROJECT=$(gcloud info --format='value(config.project)')

# Default automated perfkit values
CLOUD="AWS Azure GCP OCI"
ZONE="us-east-1a eastus us-east4-a us-ashburn-1"
MACHINETYPE="m6i.xlarge Standard_D4s_v5 n2-standard-4 VM.Standard3.Flex"
DISKTYPE=""
COMPUTE_UNITS=4
MEMORY_UNITS=16

# Default static VM file
STATIC_VM_FILE=/home/jetryan4/GitRepos/PerfKitBenchmarker/config_files/block_storage_workload_static.yaml
# Refers to the YAML object list that contains all the test in the config file
TEST_GROUP_PARENT="storage_tests"
SSH_KEY="ssh_private_key"
IP_KEY="ip_address"
USER_KEY="user_name"
DISK_KEY="name"
MOUNT_KEY="mount_point"
VM_YQ_PATH="vm_groups.default.static_vms"
STATIC_TEST_BATCH_SIZE=30
NUMBER_OF_STATIC_MACHINES=4
USE_STATIC_VMS=true

# SUPPORT FUNCTIONS

# Create files based on static config file passed
create_file(){
    echo "Reading the config file"
    echo "Creating File Number: $1"
    yq -r ".${TEST_GROUP_PARENT} | explode(.)" "${STATIC_VM_FILE}" | yq -r ".[${1}]" > "temp_config_file${1}.yaml"
    echo "Created File: temp_config_file${1}.yaml"
}

# Cleans Static VM file before it is passed to perfkit 
config_clean_and_format(){
    echo "going to run: sed ' $ d' ${PWD}/temp_config_file${1}.yaml"
    # sed " $ d" "${PWD}/temp_config_file${1}.yaml" > "${PWD}/temp_config_file${1}.yaml"
    head -n -1 "${PWD}/temp_config_file${1}.yaml" > temp.txt ; mv temp.txt "${PWD}/temp_config_file${1}.yaml"
    echo "Removed name from the disk because it is an invalid item only used for simplifying code"
    # adding yq anchor and repeating the benchmark the number of batch size plus 1
    anc="tempAnchor"
    sed -i "s/${BENCHMARK}:/& \&${anc}/" "${PWD}/temp_config_file${1}.yaml" # > temp.txt ; mv temp.txt "${PWD}/temp_config_file${1}.yaml"
    echo "benchmarks:" >> "${PWD}/temp_config_file${1}.yaml"
    for ((i=0;i<=STATIC_TEST_BATCH_SIZE;i++)); do echo "  - ${BENCHMARK}: *${anc}" >> "${PWD}/temp_config_file${1}.yaml"; done
}

# Remove Temporary config files after the completion of the tests
remove_file(){
    rm "temp_config_file${1}.yaml"
    echo "Removed File: temp_config_file${1}.yaml"
}

# Function for Assembling Log File
setup_logs(){
    templog="${2}/${BENCHMARK}_output_logs_machine_number${1}_${DT}.log"
    touch "${templog}"
}

# Capture IP and Key path for VM
get_machine_details(){
    # echo  "Captured this path: .${BENCHMARK}.${VM_YQ_PATH}[0].${SSH_KEY}"
    sshkey_name=`yq -r ".${BENCHMARK}.${VM_YQ_PATH}[0].${SSH_KEY}" "${PWD}/${1}"`
    ip_name=`yq -r ".${BENCHMARK}.${VM_YQ_PATH}[0].${IP_KEY}" "${PWD}/${1}"`
    user_name=`yq -r ".${BENCHMARK}.${VM_YQ_PATH}[0].${USER_KEY}" "${PWD}/${1}"`
    disk_name=`yq -r ".${BENCHMARK}.${VM_YQ_PATH}[0].disk_specs[1].${DISK_KEY}" "${PWD}/${1}"`
    mount_point=`yq -r ".${BENCHMARK}.${VM_YQ_PATH}[0].disk_specs[0].${MOUNT_KEY}" "${PWD}/${1}"`
    echo "SSH Key: ${sshkey_name}"
    echo "IP: ${ip_name}"
    echo "USERNAME: ${user_name}"
    echo "DISK NAME: ${disk_name}"
    echo ".${BENCHMARK}.${VM_YQ_PATH}[0].disk_specs[1].${MOUNT_KEY}"
    echo "Mount Point: ${mount_point}"
    # sleep 5
}
# Drive Mount and 
# TODO: automount script
mount_drive(){
    # unmount
    ssh -i "${1}" "${2}@${3}" sudo umount "${5}"
    # make file system 
    ssh -i "${1}" "${2}@${3}" sudo mkfs -t ext4 /dev/"${4}"
    # if directory doesnt exist
    ssh -i "${1}" "${2}@${3}" "[ ! -d ${5} ]" && ssh -i "${1}" "${2}@${3}" mkdir "${5}" && echo "Directory ${5} DOES NOT exists, so we created it."
    # echo "sudo mount /dev/${4} ${5}"
    ssh -i "${1}" "${2}@${3}" sudo mount /dev/"${4}" "${5}"
    # sleep 5change ownership of create dir
    ssh -i "${1}" "${2}@${3}" sudo chown -R "${2}:${2}" "${5}" 
    echo "Completed mounting process and ready to run"
}

# removes a directory on the remote machine
remove_dir(){
    ssh -i "${1}" "${2}@${3}" "[ -d ${4} ]" && ssh -i "${1}" "${2}@${3}" sudo rm -rf "${4}" && echo "Directory ${4} DOES exists, so we deleted it."
}

# Create BQ table
bqt(){
    table_name="${1}_${2//./_}_${3}"
}

# Function for uploading result of a query to Google Big Query
bqup(){
    bq mk "${BENCHMARK}"_test
    bq load --project_id="${PROJECT}" \
        --autodetect \
        --source_format=NEWLINE_DELIMITED_JSON \
        "${BENCHMARK}"_test."$2" \
        "$1"
}

# Result location capture 
rlc(){
    # Capture location of results file and moving to the documents
    file_val=`cat $1 | tail -n 1 | sed 's:.*/\([[:alnum:]]\{8\}\)/.*:\1:'`
    echo "File Name is ${file_val}"
    cp -r /tmp/perfkitbenchmarker/runs/${file_val}/ /mnt/c/Users/jetry/OneDrive/Desktop/StorageTests/General_Purpose
    # Capture output location from logs to capture path of results
    # bqup "/tmp/perfkitbenchmarker/runs/${file_val}/perfkitbenchmarker_results.json" "$2"
}

#/mnt/c/Users/jetry/OneDrive/Desktop/StorageTests/General_Purpose/${file_val}


# Function for running benchmark
# If Static configuration
# $1 is the config file
#
# If automated configuration 
# $1 is the cloud
# $2 is the machine type
# $3 is the az
task(){
    if $USE_STATIC_VMS 
    then
        echo "Running Static Tests"
        echo "/home/jetryan4/GitRepos/PerfKitBenchmarker/pkb.py --benchmark_config_file=${PWD}/${1}" --install_packages=false
        /home/jetryan4/GitRepos/PerfKitBenchmarker/pkb.py --benchmark_config_file="${PWD}/${1}" --install_packages=false
    else
        echo "Running task with $1, $2, $3"
        # echo "/home/jetryan4/PerfKit/PerfKitBenchmarker/pkb.py --cloud=$1 --benchmarks=${BENCHMARK} --machine_type=$2 --zone=$3"
        # /home/jetryan4/PerfKit/PerfKitBenchmarker/pkb.py --cloud="$1" --benchmarks=${BENCHMARK} --machine_type="$2" --zone="$3"
    fi
    # ./pkb.py --cloud=OCI --benchmarks=block_storage_workload --machine_type=VM.Optimized3.Flex --zone=us-ashburn-1 --oci_compute_units=4 --oci_compute_memory=16
    # sleep 5
}

# Run Function
funct(){
    # Create file if neccessary
    # Run benchmark in correct configuration
    # Remove unnecessary files
    sleep 5
}

# MAIN FUNCTION

# Currently only accepts one benchmark at a time
# accepts space delimited list for all other field types
# only currently operates for same size lists for all field types


# Capture CMDLine Args
while getopts b:m:c:z:p:u:r:s: flag
do
    case "${flag}" in
        b) BENCHMARK=${OPTARG};;
        m) MACHINETYPE=${OPTARG};;
        c) CLOUD=${OPTARG};;
        z) ZONE=${OPTARG};;
        p) PROJECT=${OPTARG};;
        u) COMPUTE_UNITS=${OPTARG};;
        r) MEMORY_UNITS=${OPTARG};;
        s) STATIC_VM_FILE=${OPTARG};;
    esac
done

# echo "$BENCHMARK"
# echo "$MACHINETYPE"
# echo "$CLOUD"
# echo "$ZONE"
# echo "$COMPUTE_UNITS"
# echo "$MEMORY_UNITS"
# echo "$PROJECT"
# echo "$STATIC_VM_FILE"


# Make Log dir
echo "Making this dir: logs/${BENCHMARK}_logs_${DT}"
dirname="${PWD}/bash_scripts/logs/${BENCHMARK}_logs_${DT}"
mkdir -p "$dirname"

# TODO: Combine run style of automated and static machine testing
# Run amount 
# run_iterations=$(( USE_STATIC_VMS ? NUMBER_OF_STATIC_MACHINES :  ))
for (( mn=0 ; mn<$NUMBER_OF_STATIC_MACHINES ; mn++ ));
do
    # Setup logs
    setup_logs "${mn}" "${dirname}" # Creates directory and files for log

    create_file "${mn}" # Create a file to be passed into the task
    get_machine_details "temp_config_file${mn}.yaml" # captures the details of a specific machine
    config_clean_and_format "${mn}" # Removed unneeded information from the config that would cause errors
    
    # remove_dir "${sshkey_name}" "${user_name}" "${ip_name}" "/opt/pkb/fio"
    mount_drive "${sshkey_name}" "${user_name}" "${ip_name}" "${disk_name}" "${mount_point}"
    task "temp_config_file${mn}.yaml" >> $templog 2>&1 &
    
    process_id=$!
    echo "The Process ID is: ${process_id}"

    # remove_file "${mn}"
done


wait


# once all test are complete

for (( mn=0 ; mn<$NUMBER_OF_STATIC_MACHINES ; mn++ ));
do
    # bqt "${cloud[$mn]}" "${cloud_machines[$mn]}" "${cloud_azs[$mn]}" # Need to define list of machines
    rlc "${PWD}/bash_scripts/logs/${BENCHMARK}_logs_${DT}/${BENCHMARK}_output_logs_machine_number${mn}_${DT}.log"
    # bqup "/tmp/perfkitbenchmarker/runs/${file_val}/perfkitbenchmarker_results.json"
done

#/mnt/c/Users/jetry/OneDrive/Desktop/StorageTests/General_Purpose
#cd /mnt/c/Users/jetry/OneDrive/Desktop/StorageTests

python /mnt/c/Users/jetry/OneDrive/Desktop/StorageTests/pkb_script_final.py
#HAVE pkb_script_final.py DOWNLOADED IN StorageTests

# Process for Running Static Benchmarks
# Read in all static vms into a list: capture IP and key_path catch error when no machines left
# Prompt or read in user input for number of iterations per machine
# 
# Create config file using yq to read the yaml from the main config file
#  - Read static_vm section and test section into new file
# yq -r '.storage_tests | explode(.)' config_files/block_storage_workload_static.yaml | yq -r '.[0]'
