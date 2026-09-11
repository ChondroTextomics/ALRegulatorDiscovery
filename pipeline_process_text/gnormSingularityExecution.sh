#!/bin/bash

# Information about the foldes and the setup files of the singularity
# setup.txt: this is the default setup file that is used when one is not given for the java scripts
# setup.SR.txt: setup file that is used when the Java script GNormPlus is doing species recognition (we are not going to give this one either because we want to use the one in the singularity)
# setup.GN.txt: setup file that is used when the Java script GNormPlus is doing gene normalization
# tmp_SR: directory where the input files with the species recognised in the file
# tmp_GNR: directory where teh input files with the genes recognised in the texts
# tmp_SA: directory where the input files with the species assigned to the genes recognised
# tmp: directory where all the temporary files neccessary to run the python script are stored
# input: directory where the pubtator or bioxml files that are going to go through GNorm2
# output: directory where the results of the software is going to be stored

## Files and directories to change
results_directory="<path_to_results>"
input_pubtator_file="<path_to_input_pubtator_file>"
setup_path="<path_folder_to_setup_files>"
setup_file="<setup_file_name>.txt" # It doesnt matter the name, it will be changed to the final one in the final directory
gnorm_singularity_path="<path_to_gnorm_singularity_file>" # to the specific gnorm2-ncbi_latest.sif file
gnorm_script_path="<path_to_gnorm_execution_script>" # to the file gnormAppExecution.sh

## Creating all directories
mkdir $results_directory
mkdir $results_directory/tmp_SR
mkdir $results_directory/tmp_GNR
mkdir $results_directory/tmp_SA
mkdir $results_directory/tmp
mkdir $results_directory/input
mkdir $results_directory/output

## Move neccessary files to the results folder
cp $setup_path$setup_file $results_directory
mv $results_directory/$setup_file $results_directory/setup.GN.txt

cp $input_pubtator_file $results_directory/input

## Run GNorm2
singularity exec --bind $results_directory/setup.GN.txt:/app/setup.GN.txt,$results_directory/tmp_SR:/app/tmp_SR,$results_directory/tmp_GNR:/app/tmp_GNR,$results_directory/tmp_SA:/app/tmp_SA,$results_directory/tmp:/app/tmp,$results_directory/input:/app/input,$results_directory/output:/app/output $gnorm_singularity_path /bin/bash < $gnorm_script_path
