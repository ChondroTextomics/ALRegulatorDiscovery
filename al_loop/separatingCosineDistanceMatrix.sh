#!/bin/bash

# Read and store the first line of the file because it is column names
read -r first_line < "$1"
#echo $first_line

# counter
sample=0

mkdir -p "$2"

tail -n +2 "$1" | while IFS="," read -r distance; do
	echo "Working on sample $sample"

	output_file="$2/${sample}.csv"

	if [ -f "$output_file" ];then
		sample=$((sample+1))
		continue
	fi

	echo "$first_line" >> "$output_file"
	echo "$distance" >> "$output_file"
	sample=$((sample+1))
done
