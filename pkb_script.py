import json
import pandas as pd
import math
import os
from pathlib import Path
import numpy as np

"""
    For pricing data, please edit the dictionary on line 22
    Edit the variable num_tests_needed on line 20 to minimum test amount

    We made changes to publisher.py when writing the jsons so that the format is correct, needs to be pushed
    
"""

TYPE_DICT = { #converts json name to name that we want
            "iperf": "Network",
            "fio": "Storage",
            "coremark": "Compute",
            "gpu_pcie_bandwidth": "GPU"
        }

class Base:
    def __init__(self: str, identifier: str, json_filename: str, csv_filename: str, test_type: str):
        self.identifier = identifier
        self.json_filename = json_filename
        self.csv_filename = csv_filename
        self.test_type = test_type
        self.num_test_needed = 30 #Change this for amount of test needed
        self.margin_of_error = 0.5 #change this accordingly
        self.provider = "AWS" #change this based on provider, same format as priceData

        #ALTER THIS WITH UPDATED HOURLY COST - let us know if calculated differently
        self.priceData = {
                'Type': ['Network', 'Storage', 'Compute', 'GPU'],
                'AWS': [0.03, 3, 4, 5],
                'IBM': [6, 8, 9, 10],
                'AZURE': [11, 13, 14, 15],
                'OCI': [16, 18, 19, 20],
                'GCP': [21, 23, 24, 25]
            }
        self.priceData = pd.DataFrame(self.priceData)

        self.testTypeDict = { #used when calculating cost
            "Network": 0,
            "Storage": 1,
            "Compute": 2,
            "GPU": 3
        }

        with open(json_filename, "r") as file:
            self.json_data = json.load(file)

        self.csv_data = pd.read_csv(csv_filename)
        unnamed_columns = [col for col in self.csv_data.columns if 'Unnamed' in col]
        self.csv_data.drop(columns=unnamed_columns, inplace=True)
        
        
    def convert(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    
    def calculate_cost(self) -> float: 
        """Calculates the cost of each test

        Returns:
            float: The cost to run one test of that type
        """        
        countDict = {} #This dictionary stores as tuple in (num of tests, end to end runtime) format
        
        #find the price for that test type and provider
        testType = self.testTypeDict[self.csv_data.at[0, "Type"]] 
        pricePerHour = self.priceData.at[testType, self.provider]

        for index, row in self.csv_data.iterrows():

        #use the dictionary to find amount of tests and runtime
            #Adds to the counter dictionary of identifiers
            ident = row["Identifier"] #remember, same ident means its coming from the same json
            runtime = row["Time"]
            if ident in countDict and runtime != -1: #if the ident is already seen and correct runtime, increase count keep runtime
                countDict[ident] = (countDict[ident][0] + 1, runtime)
            elif ident in countDict: #ident already seen, wrong runtime it increases count but keeps ident
                countDict[ident] = (countDict[ident][0] + 1, countDict[ident][1])
            else: #otherwise first time seeing that ID, set as new dictionary entry
                countDict[ident] = (1, runtime)

        times = [] #calculate time per test for each type of test
        for key in countDict:
            times.append(countDict[key][1]/countDict[key][0])
        
        avg_time = sum(times)/len(times) #average out all of the times per test to get just one time for that provider and test
        avg_time = avg_time/3600 #convert avg time (seconds) to hours

        costPerTest = round(pricePerHour *(avg_time), 5) #average cost per test per hour
        return costPerTest
    
    def num_of_tests_calc(self, percent_of_mean, mean, stdev) -> int:
        """Calculates the amount of tests necessary for a 95% confidence interval

        Args:
            percent_of_mean (any): The percentage of the mean to use as margin of error
            mean (any): The average for the data
            stdev (any): The standard deviation for the data

        Returns:
            int: the amount of tests needed for a 95% confidence interval
        """        
        percent_of_mean= percent_of_mean / 1000
        moe = percent_of_mean*mean
        num_tests = (1.96*stdev/moe)**2
        return math.ceil(num_tests)

    def calculate_confidence(self, file: str) -> None:
        """Writes to calculations.txt with confidence/cost calculations

        Returns:
            None
        """                
        num_tests_needed = 5 #change this number (30?)
        margin_of_error = 0.5 #assume MOE

        self.csv_data= pd.read_csv(self.csv_filename)
        testscores = self.csv_data["Value"].tolist() #retrieves column of values
        mean = np.mean(testscores, axis=0)
        stdev = np.std(testscores, axis=0)

        with open(file, "w") as file:
            i = margin_of_error*10
            num_t = self.num_of_tests_calc(i, mean, stdev) # of the mean margin of errors
            file.write("Number of tests for a 95% Confidence Interval at 0."+str(i)+"% margin of error: "+str(num_t)+"\n")
            if(num_t <= 5):
                file.write("The recommended number of tests has been met, no further testing is necessary.\n")
            else:
                extra_tests = math.ceil(num_t - 5)
                extra_tests_cost = round(extra_tests * self.calculate_cost(), 5)
                file.write(str(extra_tests)+" more tests are necessary, costing $"+str(self.calculate_cost())+" per test or $"+str(extra_tests_cost)+" total.\n")

    def output_conf(self, data, file):

        """
        Writes the confidence of the tests to the calculation file

        Args: 
            data : the values taken from the results json
            file : the file to output to

        Returns:
            none
        """        
        testscores = data["Value"].tolist() #retrieves column of values
        mean = np.mean(testscores, axis=0)
        stdev = np.std(testscores, axis=0)

        file.write("\nMean: " + str(mean))
        file.write("\nStandard Deviation: " + str(stdev))
        i = self.margin_of_error*10
        num_t = self.num_of_tests_calc(i, mean, stdev) # of the mean margin of errors
        file.write("\nNumber of tests for a 95% Confidence Interval at 0."+str(int(i))+"% margin of error: "+str(num_t))
        if(num_t <= self.num_test_needed):
            file.write("\nThe recommended number of tests has been met, no further testing is necessary.\n")
        else:
            extra_tests = math.ceil(num_t - self.num_test_needed)
            extra_tests_cost = round(extra_tests * self.calculate_cost(), 5)
            file.write(f"\n{extra_tests} more tests are necessary, costing ${self.calculate_cost()} per test or ${extra_tests_cost} total.\n")

    
class Network(Base):

    def convert(self):
        adding_df = pd.DataFrame(
            columns=[ #columns that every benchmark csv will have
                'Identifier', 
                'Machine', 
                'Value', 
                'Provider',
                'Type', 
                'Time'
            ])
        
        for json_obj in self.json_data: #default set all the values (except identifier)
            machine = ''
            value = ''
            time = ''

            if json_obj["metric"] == 'Throughput': #splitting up labels for searching
                labels_str = json_obj.get('labels') #the long string of all of the labels
                labels_list = labels_str.split('|,|') #list of individual labels
                
                #find machine type
                for str in labels_list: #loops through each label in the long string
                    if "machine_type" in str: #str = "receiving_machine_type:m5.large"
                        self.machine = str.split(":")[1] #splits label and takes the machine type
                
                value = json_obj.get('value') #find value     
                
                row = {
                       'Identifier': self.identifier, 
                       'Machine': machine, 
                       'Value': value, 
                       'Provider': self.provider, 
                       'Type': self.test_type,
                       'Time': -1.0
                      }

                adding_df.loc[len(adding_df)] = row
                
            if json_obj["metric"] == "End to End Runtime": #find time, type
                time = json_obj.get("value")
                
                adding_df.at[0, 'Time'] = time #add the time for the first row in each test
                adding_df["Type"] = self.test_type
                
        if self.csv_data.empty:
            adding_df.to_csv(self.csv_filename)
        else:
            combined_df = pd.concat([self.csv_data, adding_df], ignore_index=True)
            combined_df.to_csv(self.csv_filename)

    def calculate_cost(self):
        return super().calculate_cost()
    
    def calculate_confidence(self):
        return super().calculate_confidence("output/calculations_network.txt")
    
class Storage(Base):
    
    def convert(self) -> None:
        """Converts the JSON results file into a CSV of results
        """                
        adding_df = pd.DataFrame(
            columns=[
                     'Identifier', 
                     'Machine', 
                     'Value', 
                     'Provider', 
                     'Sequential/Random', 
                     'Read/Write', 
                     'Parallel T/F', 
                     'BLI', #bandwidth, latency, iops
                     'Type', 
                     'Time'
                     ])
        
        for json_obj in self.json_data:
            str = json_obj.get("metric") #gives you: "sequential_write:write:bandwidth"
            metric_list = str.split(':')

            labels_str = json_obj.get('labels') #the long string of all of the labels
            labels_list = labels_str.split('|,|') #list of individual labels

            #default set all the values (except identifier)
            machine = ''
            value = ''
            seq_ran = ''
            read_write = ''
            parallel = False
            bli = ''
            time = ''

            if(len(metric_list) == 3):
                #now go in and set all the columns

                #seq_ran
                if (metric_list[0].__contains__("sequential")): #sequential
                    seq_ran = 'sequential'
                else:  #random
                    seq_ran = 'random'

                #read_write
                if (metric_list[1].__contains__('write')):
                    read_write = 'write'
                else: #read
                    read_write = 'read'

                #check if parallel
                if(seq_ran == 'random' and read_write == 'read' and metric_list[0].__contains__('parallel')):
                    parallel = True
                else:
                    parallel = False

                #check if bandwidth, latency, or iops
                if (metric_list[2].__contains__('bandwidth')):
                    bli = 'bandwidth'
                elif (metric_list[2].__contains__('latency')):
                    bli = 'latency'
                else: 
                    bli = 'iops'

                #find machine
                for str in labels_list: #loops through each label in the long string
                    if "machine_type" in str: #str = "receiving_machine_type:m5.large"
                        machine = str.split(":")[1] #splits label and takes the machine type
                        
                value = json_obj.get("value") #get value

                row = {
                       'Identifier': self.identifier, 
                       'Machine': machine, 
                       'Value': value, 
                       'Provider': self.provider, 
                       'Sequential/Random': seq_ran,
                       'Read/Write': read_write,
                       'Parallel T/F': parallel,
                       'BLI': bli, #bandwidth, latency, iops
                       'Type': self.test_type,
                       'Time': -1.0
                      }

                adding_df.loc[len(adding_df)] = row

            if json_obj["metric"] == "End to End Runtime":
                time = json_obj.get("value")
                adding_df.at[0, 'Time'] = time
    
        if self.csv_data.empty:
            adding_df.to_csv(self.csv_filename)
        else:
            combined_df = pd.concat([self.csv_data, adding_df], ignore_index=True)
            combined_df.to_csv(self.csv_filename)

        self.csv_data = pd.read_csv(self.csv_filename)
    
    def calculate_confidence(self) -> None:
        #Sequential Write
        s_w_b = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        s_w_l =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        s_w_i =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        
        #Sequential Read
        s_r_b = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        s_r_l =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        s_r_i =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        
        #Random Write
        r_w_b = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        r_w_l =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        r_w_i =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        
        #Random Read
        r_r_b = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        r_r_l =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        r_r_i =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        
        #Random Read Parallel
        r_r_p_b = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        r_r_p_l =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])
        r_r_p_i =  pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Sequential/Random', 'Read/Write', 'Parallel T/F', 'BLI', 'Type', 'Time'])

        for index, row in self.csv_data.iterrows(): #split up the storage data into pieces we want
            if(row['Sequential/Random'] == 'sequential'):
                if(row['Read/Write'] == 'write'):
                    if(row['BLI'] == 'bandwidth'):
                        s_w_b.loc[len(s_w_b)] = row
                    elif(row['BLI'] == 'latency'):
                        s_w_l.loc[len(s_w_l)] = row
                    elif(row['BLI'] == 'iops'):
                        s_w_i.loc[len(s_w_i)] = row
                elif(row['Read/Write'] == 'read'):
                    if(row['BLI'] == 'bandwidth'):
                        s_r_b.loc[len(s_r_b)] = row
                    elif(row['BLI'] == 'latency'):
                        s_r_l.loc[len(s_r_l)] = row
                    elif(row['BLI'] == 'iops'):
                        s_r_i.loc[len(s_r_i)] = row

            elif(row['Sequential/Random'] == 'random'):
                if(row['Read/Write'] == 'write'):
                    if(row['BLI'] == 'bandwidth'):
                        r_w_b.loc[len(r_w_b)] = row
                    elif(row['BLI'] == 'latency'):
                        r_w_l.loc[len(r_w_l)] = row
                    elif(row['BLI'] == 'iops'):
                        r_w_i.loc[len(r_w_i)] = row
                
                elif(row['Read/Write'] == 'read' and row['Parallel T/F'] == False):
                    if(row['BLI'] == 'bandwidth'):
                        r_r_b.loc[len(r_r_b)] = row
                    elif(row['BLI'] == 'latency'):
                        r_r_l.loc[len(r_r_l)] = row
                    elif(row['BLI'] == 'iops'):
                        r_r_i.loc[len(r_r_i)] = row
                elif(row['Read/Write'] == 'read' and row['Parallel T/F'] == True):
                    if(row['BLI'] == 'bandwidth'):
                        r_r_p_b.loc[len(r_r_p_b)] = row
                    elif(row['BLI'] == 'latency'):
                        r_r_p_l.loc[len(r_r_p_l)] = row
                    elif(row['BLI'] == 'iops'):
                        r_r_p_i.loc[len(r_r_p_i)] = row

        with open("output/calculations_storage.txt", "w") as file: #call the confidence math for each type
            #Sequential Write
            file.write("Calculating stats for Sequential Write Bandwidth:\n")
            super().output_conf(s_w_b, file)
            file.write("\nCalculating stats for Sequential Write Latency:\n")
            super().output_conf(s_w_b, file)
            file.write("\nCalculating stats for Sequential Write Iops:\n")
            super().output_conf(s_w_b, file)
            #Sequential Read
            file.write("\nCalculating stats for Sequential Read Bandwidth:\n")
            super().output_conf(s_r_b, file)
            file.write("\nCalculating stats for Sequential Read Latency:\n")
            super().output_conf(s_r_l, file)
            file.write("\nCalculating stats for Sequential Read Iops:\n")
            super().output_conf(s_r_i, file)
            #Random Write
            file.write("\nCalculating stats for Random Write Bandwidth:\n")
            super().output_conf(r_w_b, file)
            file.write("\nCalculating stats for Random Write Latency:\n")
            super().output_conf(r_w_l, file)
            file.write("\nCalculating stats for Random Write Iops:\n")
            super().output_conf(r_w_i, file)
            #Random Read
            file.write("\nCalculating stats for Random Read Bandwidth:\n")
            super().output_conf(r_r_b, file)
            file.write("\nCalculating stats for Random Read Latency:\n")
            super().output_conf(r_r_l, file)
            file.write("\nCalculating stats for Random Read Iops:\n")
            super().output_conf(r_r_i, file)
            #Random Read Parallel
            file.write("\nCalculating stats for Random Read Parallel Bandwidth:\n")
            super().output_conf(r_r_p_b, file)
            file.write("\nCalculating stats for Random Read Parallel Latenct:\n")
            super().output_conf(r_r_p_l, file)
            file.write("\nCalculating stats for Random Read Parallel Iops:\n")
            super().output_conf(r_r_p_i, file)
            
            
class GPU(Base):

    def convert(self) -> None:
        """Converts the JSON results file into a CSV of results
        """   
        adding_df = pd.DataFrame(
            columns=[
                     'Identifier', 
                     'Machine', 
                     'Value', 
                     'Provider',
                     'Connection', #H2D, D2H, D2D
                     'Type', 
                     'Time'
                     ])
        
        for json_obj in self.json_data:
            str = json_obj.get("metric")
            #need to throw away if has a comma in it, not a value we want
            if(str.__contains__(',')):
                continue

            #default set all the values (except identifier)
            machine = ''
            value = ''
            connection = ''
            time = ''

            if(str.__contains__("Host to device")):
                connection = "H2D"
            elif(str.__contains__("Device to host")):
                connection = "D2H"
            elif(str.__contains__("Device to device")):
                connection = "D2D"
            else:
                continue

            labels_str = json_obj.get('labels') #the long string of all of the labels
            labels_list = labels_str.split('|,|') #list of individual labels

            #get machine
            for str in labels_list: #loops through each label in the long string
                if "machine_type" in str: #str = "receiving_machine_type:m5.large"
                    machine = str.split(":")[1] #splits label and takes the machine type

            value = json_obj.get("value") #get value

            row = {
                       'Identifier': self.identifier, 
                       'Machine': machine, 
                       'Value': value, 
                       'Provider': self.provider, 
                       'Connection': connection,
                       'Type': self.test_type,
                       'Time': -1.0
                      }
            
            adding_df.loc[len(adding_df)] = row
            
        if json_obj["metric"] == "End to End Runtime": #add the time to the csv
            time = json_obj.get("value")
            adding_df.at[0, 'Time'] = time

        if self.csv_data.empty:
            adding_df.to_csv(self.csv_filename)
        else:
            combined_df = pd.concat([self.csv_data, adding_df], ignore_index=True)
            combined_df.to_csv(self.csv_filename)

        self.csv_data = pd.read_csv(self.csv_filename)

    def calculate_confidence(self) -> None: #create 3 separate dataframes to pass in
        dh = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Connection', 'Type', 'Time'])  
        hd = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Connection', 'Type', 'Time'])  
        dd = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Connection', 'Type', 'Time'])  
        
        for index, row in self.csv_data.iterrows(): #separate the GPU data by test type
            if(row['Connection'] == 'D2H'):
                dh.loc[len(dh)] = row
            elif(row['Connection'] == 'H2D'):
                hd.loc[len(hd)] = row
            elif(row['Connection'] == 'D2D'):
                dd.loc[len(dd)] = row

        with open("output/calculations_gpu.txt", "w") as file: #write the calculations to the txt file
            file.write("Calculating stats for D2D:\n")
            super().output_conf(dd, file)
            file.write("\nCalculating stats for D2H:\n")
            super().output_conf(dh, file)
            file.write("\nCalculating stats for H2D:\n")
            super().output_conf(hd, file)
        
                
class Compute(Base):
    
    def convert(self) -> None:
        """Converts the JSON results file into a CSV of results
        """   
        adding_df = pd.DataFrame(
            columns=[ #columns that every benchmark csv will have
                     'Identifier', 
                     'Machine', 
                     'Value', 
                     'Provider',
                     'Thread Count',
                     'Type', 
                     'Time'
                     ])            

        for json_obj in self.json_data:

            machine = ''
            value = ''
            thread_count = ''
            time = ''

            if json_obj["metric"] == 'Coremark Score': #splitting up labels for searching
                labels_str = json_obj.get('labels') #the long string of all of the labels
                labels_list = labels_str.split('|,|') #list of individual labels
                
                #find machine type
                for str in labels_list: #loops through each label in the long string
                    if "machine_type" in str: #str = "receiving_machine_type:m5.large"
                        machine = str.split(":")[1] #splits label and takes the machine type
                
                value = json_obj.get('value') #find value     

                for str in labels_list:
                    if "thread_count:" in str:
                        thread_count = str.split(":")[1]
                
                row = {
                       'Identifier': self.identifier, 
                       'Machine': machine, 
                       'Value': value, 
                       'Provider': self.provider, 
                       'Thread Count': thread_count,
                       'Type': self.test_type,
                       'Time': -1.0
                      }

                adding_df.loc[len(adding_df)] = row
                
            if json_obj["metric"] == "End to End Runtime": #find time, type
                time = json_obj.get("value")
        
                adding_df.at[0, 'Time'] = time #add the time for the first row in each test
                if self.csv_data.empty:
                    adding_df.to_csv(self.csv_filename)
                else:
                    combined_df = pd.concat([self.csv_data, adding_df], ignore_index=True)
                    combined_df.to_csv(self.csv_filename)
            
            self.csv_data = pd.read_csv(self.csv_filename)
            unnamed_columns = [col for col in self.csv_data.columns if 'Unnamed' in col]
            self.csv_data.drop(columns=unnamed_columns, inplace=True)


    def calculate_confidence(self) -> None:
        #separate the data into two dataframes, one for each threadcount
        thread1 = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Threads', 'Type', 'Time'])
        thread2 = pd.DataFrame(columns=['Identifier', 'Machine', 'Value', 'Provider', 'Threads', 'Type', 'Time'])
        
        for index, row in self.csv_data.iterrows(): #move the raw data from the csv file to the two new dataframes for processing
            if(row['Thread Count'] == 1):
                thread1.loc[len(thread1)] = row
            elif(row['Thread Count'] == 2):
                thread2.loc[len(thread2)] = row
        
        with open("output/calculations_compute.txt", "w") as file: #write the calculations to the txt file
            file.write("Calculating stats for Thread One:\n")
            super().output_conf(thread1, file)
            file.write("\nCalculating stats for Thread2:\n")
            super().output_conf(thread2, file)
        
    
def find_files() -> None:
    """This finds all of the JSON results files in the file system and creates the appropriate results scanner object
    for each test type. Returns nothing. Can be called to initiate all of the other functions
    """    
    gpu_counter, compute_counter, storage_counter, network_counter = 1, 1, 1, 1
    path_to_runs = os.getcwd() + "/General Purpose" # --> defines the path to the runs folder. Should be in the same dir as runs folder
    runs = os.listdir(path_to_runs) #lists out random numbers of names
    for run in runs: #loops through each run in the folder of runs
        files = os.listdir(path_to_runs + f"/{run}")
        hasResults: bool = False
        test_type: str = None
        for file in files: # loops through each file in the run folder
            if (os.path.splitext(file)[1] == ".json" and "results" in os.path.splitext(file)[0]): #if the folder has a json and a result
                hasResults = True
            fullname = os.path.splitext(file)[0]
            if fullname[:-1] in TYPE_DICT.keys():
                test_type = TYPE_DICT[fullname[:-1]]
        if (test_type != None and hasResults == True): #if the test has a type and a results file
            if test_type == "Network": #create the individual interpreters for each test type and call the appropriate functions
                currScanner = Network(str(network_counter)+"-"+run, path_to_runs + f"/{run}/perfkitbenchmarker_results.json", "output/data_network.csv", test_type)
                network_counter += 1
            elif test_type == "Storage":
                currScanner = Storage(str(network_counter)+"-"+run, path_to_runs + f"/{run}/perfkitbenchmarker_results.json","output/data_storage.csv", test_type)
                storage_counter += 1
            elif test_type == "GPU":
                currScanner = GPU(str(network_counter)+"-"+run, path_to_runs + f"/{run}/perfkitbenchmarker_results.json", "output/data_gpu.csv", test_type)
                gpu_counter += 1
            elif test_type == "Compute":
                currScanner = Compute(str(network_counter)+"-"+run, path_to_runs + f"/{run}/perfkitbenchmarker_results.json", "output/data_compute.csv", test_type)
                compute_counter += 1
            currScanner.convert()
            currScanner.calculate_confidence()  
    

def make_files():
    """Creates the data.csv file for the current run
    """    
    tests = ["compute", "storage", "gpu", "network"]
    for test in tests:
        df = pd.DataFrame()
        df.to_csv(f"output/data_{test}.csv")
        file = open(f"output/calculations_{test}.txt", "w")
    
def reset_csv(filename: str) -> None: #don't need this for production
    """Takes in csv filename and resets it
    """
    if Path(filename).is_file(): 
        df = pd.DataFrame()
        df.to_csv(filename)

def main():
    """Should run the code to reset the data.csv, as well as the find_files() function
    """ 
    reset_csv("data_compute.csv") #remove these calls for production
    reset_csv("data_gpu.csv")
    reset_csv("data_storage.csv")
    reset_csv("data_network.csv")
    make_files() #create the data files
    find_files() #finds results, calls scanners
    

if __name__ == "__main__":
    main()
