import os, sys, re
from Bio import pairwise2
from Bio.Blast import NCBIXML
from Bio.SubsMat.MatrixInfo import blosum62
import gzip
import optparse
import subprocess

#-------------#
# Options     #
#-------------#

def parse_options():
    """
    This function parses the command line arguments and returns an optparse
    object.

    """
    parser = optparse.OptionParser("python motif_inferrer.py -i input_file [-b blast_path -d domains_file --db=database_file --dummy=dummy_dir -j jaspar_file -o output_file -s]")

    parser.add_option("-b",  default="./src/", action="store",type="string", dest="blast_path", help="BLAST path (blastpgp dwelling directory; default = ./src/)", metavar="{directory}")
    parser.add_option("-d", default="./domains.txt", action="store", type="string", dest="domains_file", help="Domains file (i.e. domains.txt from domains.py; default = ./domains.txt)", metavar="{filename}")
    parser.add_option("--db", default="./sequences.fa", action="store", type="string", dest="database_file", help="Database file (i.e. sequence.fa from domains.py; default = ./sequences.fa)", metavar="{filename}")
    parser.add_option("--dummy", default="/tmp/", action="store", type="string", dest="dummy_dir", help="Dummy directory (default = /tmp/)", metavar="{directory}")
    parser.add_option("-i", action="store", type="string", dest="input_file", help="Input file (i.e. query sequence in FASTA format; multiple sequences can be provided)", metavar="{filename}")
    parser.add_option("-j", default="./jaspar.txt", action="store", type="string", dest="jaspar_file", help="JASPAR file (i.e. jaspar.txt from domains.py; default = ./jaspar.txt)", metavar="{filename}")
    parser.add_option("-n", default=0, action="store", type="int", dest="n_parameter", help="N parameter for the Rost's curve (e.g. n=5 ensures 99% of correctly assigned homologs; default = 0)", metavar="{filename}")
    parser.add_option("-o", action="store", type="string", dest="output_file", help="Output file (default = stdout)", metavar="{filename}")
    parser.add_option("-s", "--single", default=False, action="store_true", dest="single", help="Single mode (if True, returns profiles derived from a single TF; default = False)", metavar="{boolean}")

    (options, args) = parser.parse_args()

    if options.input_file is None:
        parser.error("missing arguments: type option \"-h\" for help")

    return options

def parse_file(file_name, gz=False):
    """
    This function parses any file and yields lines one by one.
    
    @input:
    file_name {string}
    @return:
    line {string}

    """
    if os.path.exists(file_name):
        # Initialize #
        f = None
        # Open file handle #
        if gz: f = gzip.open(file_name, "rt")
        else: f = open(file_name, "rt")
        # For each line... #
        for line in f:
            yield line.strip("\n")
        f.close()
    else:
        raise ValueError("Could not open file %s" % file_name)

def parse_fasta_file(file_name, gz=False, clean=True):
    """
    This function parses any FASTA file and yields sequences as a tuple
    of the form (identifier, sequence).

    @input:
    file_name {string}
    @return:
    line {tuple} header, sequence

    """
    # Initialize #
    identifier = ""
    sequence = ""
    # For each line... #
    for line in parse_file(file_name, gz):
        if line[0] == ">":
            if sequence != "":
                if clean:
                    sequence += re.sub("\W|\d", "X", line)
                yield (identifier, sequence)
            m = re.search("^>(.+)", line)
            identifier = m.group(1)
            sequence = ""
        else:
            sequence += line.upper()
    if clean:
        sequence += re.sub("\W|\d", "X", line)
    yield (identifier, sequence)

def write(file_name, content=None):
    """
    This function writes any {content} to a file. If the file already
    exists, it pushed the {content} at the bottom of the file.

    @input:
    file_name {string}
    content {string}

    """
    if file_name is not None:
        try:
            f = open(file_name, "a")
            f.write("%s\n" % content)
        except:
            raise ValueError("Could create file %s" % file_name)
    else:
        sys.stdout.write("%s\n" % content)

def is_alignment_over_Rost_sequence_identity_curve(identities, align_length, parameter=0):
    """
    This function evaluates whether an alignment is over {True} or 
    below {False} the Rost's sequence identity curve.
    
    @input:
    identities {int}
    align_length {int}
    parameter {int} N parameter in the curve (if > 0 more strict)
    @return: {boolean}
    
    """
    return identities >= get_Rost_ID_threshold(align_length, n=parameter)

def get_Rost_ID_threshold(L, n=0):
    """
    This function returns the Rost sequence identity threshold for a
    given alignment of length "L".

    @input:
    L {int} alignment length
    parameter {int} N parameter in the curve (if > 0 more strict)
    @return: {Decimal}
        
    """
    import math

    return n+ (480*pow(L,float('-0.32')*(1+pow(float(repr(math.e)),float(repr(float(-L)/1000))))))

def get_alignment_identities(A, B):
    """
    This function returns the number of identities between a pair
    of aligned sequences {A} and {B}. If {A} and {B} have different
    lengths, returns None.

    @input:
    A {string} aligned sequence A (with residues and gaps)
    B {string} aligned sequence B (with residues and gaps)
    @return: {int} or None

    """
    if len(A) == len(B):
        return len([i for i in range(len(A)) if A[i] == B[i]])

    return None

#-------------#
# Main        #
#-------------#

if __name__ == "__main__":

    # Arguments & Options #
    options = parse_options()

    # Get current working directory #
    cwd = os.path.abspath(os.getcwd())

    # Initialize #
    domains = {}
    # For each line... #
    for line in parse_file(options.domains_file):
        if line.startswith("#"): continue
        line = line.split(";")
        domains.setdefault(line[0], {'domains': line[1].split(","), 'threshold': float(line[2])})

    # Initialize #
    jaspar = {}
    # For each line... #
    for line in parse_file(options.jaspar_file):
        if line.startswith("#"): continue
        line = line.split(";")
        jaspar.setdefault(line[0], [])
        jaspar[line[0]].append([line[1], line[2]])

    # Initialize #
    inferences = {}
    database_file = os.path.abspath(options.database_file)
    # For each header, sequence... #
    for header, sequence in parse_fasta_file(options.input_file):
        # Initialize #
        fasta_file = os.path.join(options.dummy_dir, "query." + str(os.getpid()) + ".fa")
        blast_file = os.path.join(options.dummy_dir, "blast." + str(os.getpid()) + ".xml")
        inferences.setdefault(header, [])
        # Create FASTA file #
        if os.path.exists(fasta_file): os.remove(fasta_file)
        write(fasta_file, ">%s\n%s" % (header, sequence))
        # Exec BLAST #
        try:
            # Initialize #
            homologs = []
            # Exec process #
            os.system("blastall -p blastp -i %s -d %s -o %s -m 7" % (fasta_file, database_file, blast_file))
            #process = subprocess.check_output(["/usr/local/bin/blastall", "-p", "blastp", "-i", fasta_file, "-d", database_file, "-o", blast_file, "-m", "7"], stderr=subprocess.STDOUT)
            # Parse BLAST results #
            blast_records = NCBIXML.parse(open(blast_file))
            # For each blast record... #
            for blast_record in blast_records:
                for alignment in blast_record.alignments:
                    for hsp in alignment.hsps:
                        # If structural homologs... #
                        if is_alignment_over_Rost_sequence_identity_curve(hsp.identities, hsp.align_length, parameter=int(options.n_parameter)):
                            homologs.append((str(alignment.hit_def), float(hsp.expect), hsp.query, "%s-%s" % (hsp.query_start, hsp.query_end),  hsp.sbjct, "%s-%s" % (hsp.sbjct_start, hsp.sbjct_end)))
                            break
        except:
            raise ValueError("Could not exec blastpgp!!!")
        # Remove files #
        os.remove(blast_file)
        os.remove(fasta_file)
        # For each uniacc... #
        for uniacc, evalue, query_alignment, query_from_to, hit_alignment, hit_from_to in homologs:
            # Skip if uniacc does not have assigned domains... #
            if uniacc not in domains: continue
            # Initialize #
            identities = []
            # For each domain... #
            for domain in domains[uniacc]['domains']:
                for alignment in pairwise2.align.globalds(sequence, domain, blosum62, -11.0, -1):
                    identities.append(get_alignment_identities(alignment[0], alignment[1])/float(len(domain)))
            # If domain alignment passes threshold... #
            if max(identities) >= domains[uniacc]['threshold']:
                # For each uniacc JASPAR matrix... #
                for matrix, genename in jaspar[uniacc]:
                    # If single mode... #
                    if options.single:
                        if "::" in genename: continue
                    # Infer matrix #
                    inferences[header].append([genename, matrix, evalue, query_alignment, query_from_to, hit_alignment, hit_from_to, max(identities)])

        # Write output #
        write(options.output_file, "#Query,TF Name,TF Matrix,E-value,Query Alignment,Query Start-End,TF Alignment,TF Start-End,DBD %ID")
        for header in inferences:
            for inference in sorted(inferences[header], key=lambda x: x[-1], reverse=True):
                write(options.output_file, "%s,%s" % (header, ",".join(map(str, inference))))
