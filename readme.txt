Script created by: Estefania Serrano


Usage:

./scheduling.py <fileto be parsed> <application name> <application parameters>

Requirements:
Fortran source code.
Makefile with target equal to the application name.
OMPP installed and compatible makefile.

To mark a section for analysis, use the following syntax:

!$pragma try_schedule

just before the parallel construction. 
Compatible with teh following constructions:
	!$OMP PARALLEL DO
	!$OMP DO

It tests the following possibilities:
	Guided, dynamic and static scheduling. 
	Sizes of chunk: default, 1, 2, 4, 8, 6, 128, 256 
	nowait addition to the end of the pragma

The results are output to:
	tuning_results.txt
	tuning_results_nowait.txt

Graphic results now removed (to be corrected in future versions).
