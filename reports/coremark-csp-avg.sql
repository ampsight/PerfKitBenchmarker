-- ALL CSP 1-thread prelim results

SELECT  'AWS_c5_xlarge', avg(value) FROM `perfkitbenchmark-test-project.coremark_prelim_results.AWS_c5_xlarge_us-east-1a` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=1%'
UNION ALL
SELECT  'Azure_Standard_F4', avg(value) FROM `perfkitbenchmark-test-project.coremark_prelim_results.Azure_Standard_F4_eastus` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=1%'
UNION ALL
SELECT  'GCP_c3-highcpu-4', avg(value) FROM `perfkitbenchmark-test-project.coremark_prelim_results.GCP_c3-highcpu-4_us-east4-b` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=1%'
UNION ALL
SELECT  'OCI_Vm_Standard_E3', avg(value) FROM `perfkitbenchmark-test-project.coremark_prelim_results.OCI_VM_Standard_E3_Flex_us-ashburn-1_VCPUs4_RAM8` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=1%'
