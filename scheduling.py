import sys
import fileinput
import os.path
import matplotlib.pyplot as plt 
#import prettytable

import collections
import subprocess
import numpy as np


schedule_type=["DYNAMIC","GUIDED","STATIC"]
#schedule_type=["DYNAMIC"]
schedule_chunk=["default","1","4","8","64","128","256","1024"]
#schedule_chunk=["24","48"]
waitclause=["wait", "nowait"]
file_tuning=''


prevline_restore= ''
prevline_number = 0
file_len = 0
number_regions=0
nowaitline= 0

maximum=0.0


def parsefile(argv):


	if not os.path.isfile(argv):
		print "File provided is not a file or not exists."
		sys.exit(2)
	global file_len
	global prevline_restore
	global prevline_number
	global nowaitline
	pragma_found = False
	pragma_first_time = False
	linenumber = prevline_number
	lines = []
	counter = 0
	filein = open(argv,"r")
	for line in filein:

		#starting pomp region
		if "!$OMP" in line and  "DO" in line and not "END" in line and pragma_found:
			lines.append("       !$POMP INST INIT\n")
			lines.append("       !$POMP INST BEGIN(schedule_region)\n")
			lines.append(line)
		#ending pomp region

		elif "!$OMP" in line and  "END" in line and  "DO" in line and "nowait" in line:
                        if "PARALLEL" in line:
				lines.append("       !$OMP END PARALLEL DO\n")
			else:
				lines.append("       !$OMP END DO\n")
                        pragma_found= False

		elif "!$OMP" in line and  "END" in line and "DO" in line and pragma_found:
			nowaitline= counter
			lines.append(line)
			lines.append("       !$POMP INST END(schedule_region)\n")
			pragma_found= False
		elif "!$POMP INST INIT" in line:
			#ignore line and not append
                        line = ''
		elif "!$POMP" in line and "(schedule_region)" in line:
			#ignore line and not append
			line = ''
		#next pragma will be scheduled in runtime
		elif "!$pragma try_schedule" in line and counter > prevline_number and not pragma_first_time:
			pragma_found = True
			pragma_first_time = True
			lines.append(line)
		#change the scheduling 
		elif pragma_found and "SCHEDULE(" in line:
			prevline_restore = line
			line= "    !$OMP SCHEDULE(RUNTIME)\n"
			lines.append(line)
			linenumber = counter
		elif "SCHEDULE(RUNTIME)" in line:
			line = prevline_restore
			lines.append(line)
		else:
			lines.append(line)

		counter+=1
	fileout = open(argv, 'w')
	for line in lines:
		fileout.write(line)
	
	if file_len== 0:
		file_len=counter


	filein.close()
	fileout.close()
	return linenumber
	


def include_nowait(argv,linenum):

	global nowaitline
	filein = open(argv,"r")
	counter= 0 
	lines = []
        for line in filein:

		if counter >= nowaitline  and "!$OMP" in line and "END" in line:
			if "PARALLEL" in line and "DO" in line:
				line = "        !$OMP END PARALLEL DO nowait\n"
			elif "DO" in line:
				line = "        !$OMP END DO nowait\n"
			nowaitline= file_len
		lines.append(line)
		counter += 1

	fileout = open(argv, 'w')
        for line in lines:
                fileout.write(line)

	filein.close()
        fileout.close()


def process_results(dictionnary, lines, nowait):

	dictionnarymax = []
	dictionnarymin = []
	width = 20
	for types in schedule_type:
		if types != "STATIC":
			maxvalue = max(dictionnary[types])
			minvalue = min(dictionnary[types])
		else:
			maxvalue = dictionnary[types][0]
			minvalue = dictionnary[types][0]
		dictionnarymax.append(maxvalue)
		dictionnarymin.append(minvalue)	
	global maximum 
	maximum = max(dictionnarymax)
	if nowait:
		res_file = open("tuning_results.txt", "a+")
	else:
		res_file = open("tuning_results_nowait.txt","a+")
	#Writing header to file
	if prevline_number == 0:
		res_file.write("Results for the tuning of file: "+ file_tuning+"\n")

	res_file.write("*********** Global results: line ="+str(lines)+" **********\n")
	line= "|{0}|".format("Type Scheduling".ljust(width))
	for name_chunk in schedule_chunk:
		line += "|{0}|".format(name_chunk.ljust(width))
	line += "\n"
	res_file.write(line)
	for types in schedule_type:
		line = "|{0}|".format(types.ljust(width))
		for chunk in dictionnary[types]:
			line += "|{0}|".format(str(chunk).ljust(width))
		line += "\n"
        	res_file.write(line)
	res_file.write("*********** Max and Min: line ="+str(lines)+" ***********\n")
	
	line = "|{0}|".format(" ".ljust(width))
        for types in schedule_type:
                line += "|{0}|".format(types.ljust(width))
	line += "\n"
	res_file.write(line)
	line = "|{0}|".format("Maximum".ljust(width))
	counter = 0
        for types in schedule_type:
 		 line += "|{0}|".format(str(dictionnarymax[counter]).ljust(width))
		 counter += 1
	line += "\n"
        res_file.write(line)

	line = "|{0}|".format("Minimum".ljust(width))
	counter = 0 
	for types in schedule_type:
                 line += "|{0}|".format(str(dictionnarymin[counter]).ljust(width))
		 counter += 1
	line += "\n"
        res_file.write(line)


	res_file.close()


def plot_results(dictionnary, line, nowait):

	n_groups = len(schedule_type)

	i=1
	
	for item in dictionnary:
		x_pos=np.arange(len(schedule_chunk))
		plt.subplot(1,n_groups,i)
		plt.bar(x_pos,dictionnary[item])
		plt.xticks(x_pos,schedule_chunk)
		plt.xlabel('Chunk size')
		plt.ylabel('Execution time (s)')
		plt.title('Results for '+item+' in line: '+str(line))
		plt.ylim((0,maximum))

		i+=1

#	plt.show()

	if nowait:
		plt.savefig('tuningres_line_nowait_'+str(line)+'.png')
	else:
		plt.savefig('tuningres_line_'+str(line)+'.png')

def iterate_over(line, executable, nowait):
 	dictionnary_res = collections.defaultdict(list)
	dictionnary_res_nowait = collections.defaultdict(list)
	execution_logs = open("log_tuning_output.txt","a+")
	for types in schedule_type:
		if types != "STATIC":
			for ichunk in schedule_chunk:
				print "Working on schedule: "+ types+" with size of chunk: "+ ichunk
				
				if(ichunk=='default'):
					os.environ["OMP_SCHEDULE"] = types
				else:
					os.environ["OMP_SCHEDULE"] = types+","+ichunk
				if nowait:
					os.environ["OMPP_APPNAME"] = types+"_"+ichunk+"_nowait_"+str(line) 
				else:
					os.environ["OMPP_APPNAME"] = types+"_"+ichunk+"_"+str(line)
#				parsefile(argv, "24", "DYNAMIC")
				bashCommand = "pede pedeSteerMaster.txt"
				print "Execution... "+str(executable)
				subprocess.call(executable,stdout=execution_logs)
				if nowait:
					dictionnary_res_nowait[types].append(float(parse_ompp(types, ichunk,line,nowait)))
				else:
					dictionnary_res[types].append(float(parse_ompp(types, ichunk,line,nowait)))
		else:
			print "Working on schedule: "+ types+" with size of chunk: default"
			os.environ["OMP_SCHEDULE"] = types
			if nowait:
                        	os.environ["OMPP_APPNAME"] = types+"_0_nowait_"+str(line)
			else:
				os.environ["OMPP_APPNAME"] = types+"_0_"+str(line)
#                       parsefile(argv, "24", "DYNAMIC")
                        bashCommand = "pede pedeSteerMaster.txt"
			print "Execution... " + str(executable)
                        subprocess.call(executable,stdout=execution_logs)
			if nowait:
				dictionnary_res_nowait[types].append(float(parse_ompp(types, "0",line,nowait)))
			else:
				dictionnary_res[types].append(float(parse_ompp(types, "0",line,nowait)))
			for counter in range(0, len(schedule_chunk)-1): 
				 dictionnary_res[types].append(0.0)
	execution_logs.close()

	if nowait:
		print "Processing results..."
		process_results(dictionnary_res_nowait,line,nowait)
		print "Plotting results..."
#		plot_results(dictionnary_res_nowait,line,nowait)

	else:
		print "Processing results..."
        	process_results(dictionnary_res,line,nowait)
       		print "Plotting results..."
#        	plot_results(dictionnary_res,line,nowait)


def parse_ompp(types,ichunk, line, nowait):
	if nowait:
		file_name = types+"_"+ichunk+"_nowait_"+str(line)+".56-0.ompp.txt"
	else:
		file_name = types+"_"+ichunk+"_"+str(line)+".56-0.ompp.txt"
	if not os.path.isfile(file_name):
                print "Can not find OMPP file: "+file_name
                sys.exit(2)

        pragma_found = False
        lines = []
        filein = open(file_name,"r")
        for line in filein:
		if "ompP Callgraph" in line:
			pragma_found = True
		if "schedule_region" in line and pragma_found:
			result = line.split('(')
			return result[0]
			
	return "0.0"
def main(argv):

	if len(argv) <= 2:
                print "Error: usage: scheduling.py <analyzed_file> <executable> [<argument> ]"
                sys.exit(2)

	global file_tuning
	global number_regions
	global prevline_number
	file_tuning = argv[1]
	finished = False
	execution_logs = open("log_tuning_output.txt","a+")
	print "Starting tuning of the application: ".join(argv[2:])
	while not finished:
		print "Parsing and preparing file: "+argv[1]
		line_nums= parsefile(argv[1])
		if line_nums > prevline_number:
			print "Compiling sourcecode: calling make <executable>"
			make_result = subprocess.call("make clean", shell=True,stdout=execution_logs,stderr=execution_logs)
			make_result = subprocess.call("make "+argv[2],shell=True,stdout=execution_logs,stderr=execution_logs)
			if make_result != 0:
				execution_logs.close()
				print "Compilation error. Finishing tests"
				sys.exit(2)
			print "Launching executions"
			iterate_over(line_nums,argv[2:],False)
			number_regions+=1
			prevline_number= line_nums
			include_nowait(argv[1],line_nums)
			print "Compiling sourcecode for nowait: calling make <executable>"
                        make_result = subprocess.call("make clean", shell=True,stdout=execution_logs,stderr=execution_logs)
                        make_result = subprocess.call("make "+argv[2],shell=True,stdout=execution_logs,stderr=execution_logs)
                        if make_result != 0:
                                execution_logs.close()
                                print "Compilation error. Finishing tests"
                                sys.exit(2)
                        print "Launching executions with no wait"
                        iterate_over(line_nums,argv[2:],True)
	
		else:
			print "Finishing tuning process"
			finished = True
	execution_logs.close()
if __name__ == "__main__": main(sys.argv)
