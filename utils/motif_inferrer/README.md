####
# This file contain the instructions to build the JASPAR domains database.
# Note that "curl" is only valid in Mac OS X environments. For UNIX use "wget".
####

###
# CIS-BP: check for the latest release!!!
###
#curl http://cisbp.ccbr.utoronto.ca/data/1.02/DataFiles/SQLDumps/SQLArchive_cisbp_1.02.zip -o files/cisbp_1.02.zip
#curl http://cisbp.ccbr.utoronto.ca/data/1.02/DataFiles/Bulk_downloads/EntireDataset/TF_Information_all_motifs.txt.zip -o files/TF_Information_all_motifs.txt.zip
wget http://cisbp.ccbr.utoronto.ca/data/1.02/DataFiles/SQLDumps/SQLArchive_cisbp_1.02.zip -o files/cisbp_1.02.zip
unzip files/cisbp_1.02.zip -d files/
unzip files/cisbp_1.02.prot_features.zip -d files/
gzip files/cisbp_1.02.prot_features.sql
unzip files/cisbp_1.02.proteins.zip -d files/
gzip files/cisbp_1.02.proteins.sql
unzip files/cisbp_1.02.tfs.zip -d files/
gzip files/cisbp_1.02.tfs.sql
unzip files/TF_Information_all_motifs.txt.zip -d files/
gzip files/TF_Information_all_motifs.txt
rm files/*.zip

###
# UniProt
###
#curl ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_sprot.fasta.gz -o files/uniprot_sprot.fasta.gz
wget ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_sprot.fasta.gz -o files/uniprot_sprot.fasta.gz
gunzip files/uniprot_sprot.fasta.gz
#curl ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_trembl.fasta.gz -o files/uniprot_trembl.fasta.gz
wget ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_trembl.fasta.gz -o files/uniprot_trembl.fasta.gz
gunzip files/uniprot_trembl.fasta.gz
cat files/uniprot_sprot.fasta files/uniprot_trembl.fasta > files/uniprot_sprot+trembl.fasta
gzip files/uniprot_sprot+trembl.fasta
rm files/uniprot_sprot.fasta files/uniprot_trembl.fasta

###
# BLAST
###
#curl ftp://ftp.ncbi.nlm.nih.gov/blast/executables/release/LATEST/blast-2.2.26-universal-macosx.tar.gz -o blast-2.2.26.tar.gz
wget -O blast-2.2.26.tar.gz ftp://ftp.ncbi.nlm.nih.gov/blast/executables/release/LATEST/blast-2.2.26-x64-linux.tar.gz
mkdir ./src/
tar xfz blast-2.2.26.tar.gz -C ./src/
cp ./src/blast-2.2.26/bin/blastpgp ./src/blast-2.2.26/bin/formatdb ./src/blast-2.2.26/data/BLOSUM62 ./src/
rm -rf ./src/blast-2.2.26/
rm blast-2.2.26.tar.gz

###
# Domains
###
python scripts/domains.py -b src/ -d files/cisbp_1.02.prot_features.sql.gz -i files/TF_Information_all_motifs.txt.gz -j files/JASPAR_2016_beta_CORE_matrix_proteins.txt -p files/cisbp_1.02.proteins.sql.gz -t files/cisbp_1.02.tfs.sql.gz -u files/uniprot_sprot+trembl.fasta.gz -v

###
# Motif Inference
###
python motif_inferrer.py -i examples/MAX.fa
# If we don't want to infer JASPAR profiles involving multiple TFs:
python motif_inferrer.py -i examples/MAX.fa -s
