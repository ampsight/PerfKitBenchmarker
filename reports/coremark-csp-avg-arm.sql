--sql code for arm processor 1-thread:
SELECT  'AWS_m6g_xlarge', avg(value) FROM `perfkitbenchmark-test-project.coremark_prelim_results.AWS_m6g_xlarge_us-east-1a` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=1%'
UNION ALL
SELECT  'Azure_Standard_D4ps', avg(value) FROM `perfkitbenchmark-test-project.coremark_prelim_results.Azure_Standard_D4ps_v5_eastus` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=1%'
UNION ALL
SELECT  'GCP_n2d-highcpu-4', avg(value) FROM `perfkitbenchmark-test-project.coremark_prelim_results.GCP_n2d-standard-4_us-east4-b` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=1%'
UNION ALL
SELECT  'OCI_Vm_Standard_A1', avg(value) FROM `perfkitbenchmark-test-project.coremark_prelim_results.OCI_VM_Standard_A1_Flex_us-ashburn-1_VCPUs4_RAM16` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=1%'

--sql code code for arm processor 4-thread:
SELECT  'AWS_m6g_xlarge', avg(value) FROM `perfkitbenchmark-test-project.coremark_4thread_prelim_results.AWS_m6g_xlarge_us-east-1a` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=4%'
UNION ALL
SELECT  'Azure_Standard_D4ps', avg(value) FROM `perfkitbenchmark-test-project.coremark_4thread_prelim_results.Azure_Standard_D4ps_v5_eastus` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=4%'
UNION ALL
SELECT  'GCP_n2d-highcpu-4', avg(value) FROM `perfkitbenchmark-test-project.coremark_4thread_prelim_results.GCP_n2d-standard-4_us-east4-b` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=4%'
UNION ALL
SELECT  'OCI_Vm_Standard_A1', avg(value) FROM `perfkitbenchmark-test-project.coremark_4thread_prelim_results.OCI_VM_Standard_A1_Flex_us-ashburn-1_VCPUs4_RAM16` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=4%'

--sql code for arm processor 8
SELECT  'AWS_m6g_xlarge', avg(value) FROM `perfkitbenchmark-test-project.coremark_8thread_prelim_results.AWS_m6g_xlarge_us-east-1a` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=8%'
UNION ALL
SELECT  'Azure_Standard_D4ps', avg(value) FROM `perfkitbenchmark-test-project.coremark_8thread_prelim_results.Azure_Standard_D4ps_v5_eastus` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=8%'
UNION ALL
SELECT  'GCP_n2d-highcpu-4', avg(value) FROM `perfkitbenchmark-test-project.coremark_8thread_prelim_results.GCP_n2d-standard-4_us-east4-b` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=8%'
UNION ALL
SELECT  'OCI_Vm_Standard_A1', avg(value) FROM `perfkitbenchmark-test-project.coremark_8thread_prelim_results.OCI_VM_Standard_A1_Flex_us-ashburn-1_VCPUs4_RAM16` WHERE metric = 'Coremark Score' AND labels LIKE '%DMULTITHREAD=8%'
