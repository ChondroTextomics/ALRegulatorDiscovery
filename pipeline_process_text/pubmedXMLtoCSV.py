# Python script that will:
# - read the xml file with the info of the articles
# - extract title, abstract and pmid for each article
# - save that table as a csv
# - takes file names as input of the script
# - makes sure that is only analyzing articles and not other objects such as books
# - it does not read all the IDs, when it reads the pubmed it does not read anymore

# Packages
import pandas as pd # create the table
import xml.etree.ElementTree as ET # extarct the info of the xml data
import sys
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-input", help = "input file that will have all the data in xml format of articles", required = True)
parser.add_argument("-out", help = "output file that will contain the data of the given pmid article dates", required = True)
args = parser.parse_args()

if os.path.exists(args.input):
    try:
    # Read the xml files with the paper info
        tree = ET.parse(args.input)
        root = tree.getroot()
        print(f"Number of articles found in {args.input}: {len(root.findall('PubmedArticle'))}\nNumber of other entities found in {args.input}: {len(root) - len(root.findall('PubmedArticle'))}")
    except ET.ParseError as e:
        print(f"ERROR: during reading xml format parsing error occurred at line {e.position[0]}, column {e.position[1]}")
        print(f"Message: {e}")
        sys.exit(1)
else:
    print(f"ERROR: file {args.input} cannotbe found")
    sys.exit(1)

if os.path.exists(args.out):
    answer = input(f"The file '{args.out}' given for -out already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -out file already exists and was not replaced.")

# Functions
def extract_text(element):
    """Recursively extracts all text from an XML element while preserving original spacing."""
    text_content = []

    # Capture element text (before any subelements)
    if element.text:
        text_content.append(element.text)

    # Process subelements recursively
    for subelement in element:
        text_content.append(extract_text(subelement))  # Recursively extract text
        if subelement.tail:  
            text_content.append(subelement.tail)  # Preserve original tail spacing

    return ''.join(text_content)  # Join exactly as in XML, no extra spaces

# Body of the script
# Create the table
dataParsed = pd.DataFrame(columns = ["pmid", "title", "abstract"])

print("Parsing articles....")
# Parse each article and add the info for each pmid
for article in root.findall("PubmedArticle"):
    retracted_publication = False

    # We are going to make sure that it is the PubMed ID the one we get
    for id in article.findall("./PubmedData/ArticleIdList/ArticleId"):
        if id.get("IdType") == "pubmed":
            pmid = id.text
            break

    title_element = article.find("./MedlineCitation/Article/ArticleTitle")
    title = extract_text(title_element)
    
    abstract_elements = article.findall("./MedlineCitation/Article/Abstract/AbstractText")
    abstract = "" # Initialize the abstract text
    # If the abstract is split in different sections such as results, methods, etc there will be different elements in the abstract itself
    for index, part_abstract in enumerate(abstract_elements):
        if part_abstract.get("Label") != None:
            if index != 0: # Meaning that this is not the first part of the paper so it needs spacing between the last and this part of the text
                abstract += " " # This is done for aesthetic and splitter reasoning
            abstract += part_abstract.get("Label")+": " # Add label if it has

        abstract += extract_text(part_abstract)
    
    retracted = article.findall(".MedlineCitation/Article/PublicationTypeList/PublicationType")
    for publication in retracted:
        if publication.text.lower() == "retracted publication":
            retracted_publication = True
    
    # We only are going to add the not retracted ones
    if retracted_publication == False:
        dataParsed.loc[len(dataParsed)] = [pmid, title, abstract]
    
print(f"Saving data in {args.out}")
dataParsed.to_csv(args.out, header = True, index = False)
print("Data parsed and saved!")