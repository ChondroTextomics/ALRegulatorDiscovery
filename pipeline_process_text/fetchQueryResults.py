# Python script that will retrieve from a query the PMIDs that match with the search in PubMed
# As well, this script will save the PMIDs in a txt format when each one is a line so we can
# generate a list with readlines() for future use

# Packages
from Bio import Entrez # Retrieve the PMIDs
import subprocess
import sys
import argparse
import regex as re
import os

# Most of the argumenst can be found in https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch
parser = argparse.ArgumentParser()
parser.add_argument("-out", help = "output file that will contain the pmids", required = True)
parser.add_argument("-mindate", help = "data (year/month/day) that will bethe min date when searching in the database with entrez")
parser.add_argument("-maxdate", help = "data (year/month/day) that will bethe max date when searching in the database with entrez")
parser.add_argument("-db", help = "database to search with entrez (Value must be a valid Entrez database name but it wont be checked)", default = "pubmed")
parser.add_argument("-email", help = "email for the search, it will be in the metadata", required = True)
parser.add_argument("-query", help = "query to search in the database with entrez")
parser.add_argument("-retrieve", help = "path to the file where the retrieved data will be stored")
parser.add_argument("-pmidfile", help = "path to an existing file with one PMID per line; if given, the search step is skipped and data is retrieved directly for these PMIDs (requires -retrieve)")
args = parser.parse_args()

# --------------------
# Check the parameters
# Check that the files out and retrieve (if given) dont exist and are not the same
if args.out == args.retrieve:
    sys.exit("ERROR: -out and -retrieve files cannot be the same.")
 
if args.pmidfile:
    # Skipping the search: we need a PMID file to read from and somewhere to put the retrieved data
    if not os.path.exists(args.pmidfile):
        sys.exit(f"ERROR: -pmidfile '{args.pmidfile}' does not exist.")
    if not args.retrieve:
        sys.exit("ERROR: -retrieve is required when using -pmidfile.")
else:
    # These are only needed when we actually perform a search
    if not args.query or not args.mindate or not args.maxdate:
        sys.exit("ERROR: -query, -mindate and -maxdate are required unless -pmidfile is given.")
 
if os.path.exists(args.out):
    answer = input(f"The file '{args.out}' given for -out already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -out file already exists and was not replaced.")
 
if args.retrieve and os.path.exists(args.retrieve):
    answer = input(f"The file '{args.retrieve}' given for -retrieve already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -retrieve file already exists and was not replaced.")
 
# Check the min and maxdate are in the correct format (only relevant when searching)
if not args.pmidfile:
    date_pattern = r"\d{4}\/\d{2}\/\d{2}|\d{4}\/\d{2}|\d{4}"
 
    if not re.fullmatch(date_pattern, args.mindate):
        sys.exit("ERROR: -mindate is not in the correct format (YYYY or YYYY/MM or YYYY/MM/DD).")
 
    if not re.fullmatch(date_pattern, args.maxdate):
        sys.exit("ERROR: -maxdate is not in the correct format (YYYY or YYYY/MM or YYYY/MM/DD).")
 
# make sure the database is pubmed or something else that is valid
Entrez.email = args.email
try:
    handle = Entrez.einfo()
    record = Entrez.read(handle)
    handle.close()
    valid_dbs = record["DbList"]
except Exception as e:
    sys.exit(f"Could not verify -db value against Entrez (network/API issue): {e}")
 
if args.db not in valid_dbs:
    sys.exit(f"ERROR: -db value '{args.db}' is not a valid Entrez database. Valid options are: {', '.join(valid_dbs)}")
 

# --------------------
# --------------------
if args.pmidfile:
    # Read the PMIDs straight from the given file instead of searching
    with open(args.pmidfile) as f:
        id_list = [line.strip() for line in f if line.strip()]
 
    if not id_list:
        sys.exit(f"ERROR: -pmidfile '{args.pmidfile}' contains no PMIDs.")
 
    print(f"{len(id_list)} PMIDs read from {args.pmidfile}")
 
    # Keep a copy in -out for consistency with the search workflow (and because the
    # EDirect branch below reads its input from -out)
    with open(args.out, "w") as output_file:
        output_file.writelines(id + "\n" for id in id_list)
 
    count = len(id_list)
else:
    # https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch
    # Get the number of papers that the query extracts
    search_entrez = Entrez.esearch(db = args.db,
                           term = args.query,
                           mindate = args.mindate,
                           maxdate = args.maxdate,
                           retmode = "xml", # the xlm format can be read with Entrez.read() but the json cant. They give very similar information
                           retmax = 9999 # This is the maximum
                        )
 
    initial_object = Entrez.read(search_entrez)
 
    print(f"{int(initial_object['Count'])} articles found")
 
    # there is nothing to retrieve so we abort the program
    if int(initial_object["Count"]) == 0:
        sys.exit(f"No articles found in {args.db}. Exiting.")
 
    count = int(initial_object["Count"])
    id_list = initial_object["IdList"]
 
    # Lets get the txt file with only the PMIDs
    with open(args.out, "w") as output_file:
        output_file.writelines(id + "\n" for id in id_list)

# Extracting the info of the articles (wheter from pmid file or the one created by the search)
# If we have 9999 or less we will use Entrez.efetch(), if it is more, we will use EDirect (command line)
if count <= 9999:
    # Retrieve if it is wanted
    # We are going to do it in a xml format so we can parse it
    # We are going to obtain the medline format because it holds the metadata of the articles
    # Depending on the number of elements in the list, this could take more or less time
    if args.retrieve:
        handle_articles = Entrez.efetch(db = args.db,
                        id = id_list,
                        retmode = "xml",
                        rettype = "medline" # In a MEDLINE format with slight metadata such as defining title, authors, etc
        )
        data_articles = handle_articles.read().decode("utf-8")
        handle_articles.close()
else:
    if not args.pmidfile:
        # Search with EDirect because the search_object_xml will not have all the info that we want
        # Needs to have the app edirect in the system
        fetch_pmids_command = f"esearch -db {args.db} -query '{args.query}' -maxdate {args.maxdate} -mindate {args.mindate} | efetch -format uid"
        result = subprocess.run(fetch_pmids_command, shell = True, capture_output = True, text = True)
 
        if result.stderr:
            print(f"ERROR During esearch:\n{result.stderr}")
            sys.exit(1)
 
        # Write the results
        with open(args.out, "w") as output_file:
            output_file.write(result.stdout)
 
    if args.retrieve:
        print(f"Extracting information for {count} articles with EDirect. It could take some minutes!")
 
        command_run = f"efetch -db {args.db} -format medline -mode xml -input '{args.out}'"
        initial_object_data = subprocess.run(command_run, shell = True, capture_output = True, text = True)
 
        if initial_object_data.stderr:
            print(f"ERROR During efetch:\n{initial_object_data.stderr}")
            sys.exit(1)
 
        # EDirect gives us chunks so we need to process it so it can turn into a one big xml search and treat it as an output of Entrez.efetch
        # pattern that needs to be taken out of the file. It will take things like
        # </PubmedArticleSet>
        # <?xml version="1.0" ?>
        # <!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2025//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_250101.dtd">
        # <PubmedArticleSet>
        pattern = r"</PubmedArticleSet>\n<\?xml version=.*?\?>\n<!DOCTYPE .*?>\n<PubmedArticleSet>"
 
        data_articles = re.sub(pattern, '', initial_object_data.stdout, flags = re.DOTALL)
 
if args.retrieve:
    # Save the xml data into a file
    # We are doing this so we can actually parse it in the future if neccessary without having to call entrez again with all those PMIDs
    with open(args.retrieve, 'w', encoding = "utf-8") as f:
        f.write(data_articles)