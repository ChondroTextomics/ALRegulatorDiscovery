#!/bin/bash

# Move to the app directory

cd /app

# Set the input and output directories
# These directories will be linked to some other directory that we have set with the -B in singualrity
INPUT="input"
OUTPUT="output"

# Species recognition (SR) with Java and the setup.SR.tct file
java -Xmx60G -Xms30G -jar GNormPlus.jar ${INPUT} tmp_SR setup.SR.txt

# Gene recognition and species attachment for normalization with python script
# This python can be with our without species assignment by giving more or less arguments
python GeneNER_SpeAss_run.py -i tmp_SR -r tmp_GNR -a tmp_SA -n gnorm_trained_models/geneNER/GeneNER-Bioformer.h5 -s gnorm_trained_models/SpeAss/SpeAss-Bioformer.h5

# Gene normalization
java -Xmx60G -Xms30G -jar GNormPlus.jar tmp_SA ${OUTPUT} setup.GN.txt

# Remove the temporal files
#rm -rf tmp_SR/* tmp_GNR/* tmp_SA/*
