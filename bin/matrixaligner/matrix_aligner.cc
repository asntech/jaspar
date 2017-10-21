#include <iostream>
# include <stdlib.h>
# include <math.h>
# include <string.h>
#include <stdio.h>
//# include <mysql.h>

using namespace std;

#define def_host_name "forkhead.cgr.ki.se"

// final_scorer 1: takes args
// 1: filename (input profile) 2: profile id (database) 3 gap opening penalty(optional) 4 gap extension penalty(optional)

/*
SEMANTICS at compiling 
objects:

g++ -c -Wall -I/usr/include/mysql/ scorer1.2.cc

compilation using libraries
g++ -o scorer4 scorer1.4.o -L/usr/lib/mysql -lmysqlclient -lz

lz is for comparession library


for simulator:

g++ -

 */



//const float open_penalty= 3; // open gap penalty
//const float ext_penalty= 0.01; // extend gap penalty
//const int max=50; // is not used...
int pos1;  // position on first profile
int pos2; // position on second profile


int nucleotide;       // nucleotide, 0-3 =ACGT 

class entry{  // box in score-table
public:
  float score;    // the dynamically best-score-yet
  float cell_score; // real score in this position
  entry *father;   //  pointer to father box
  int insert;          // insertion, 1=yes, 0 =no
  int deletion;       // deletion,  1=yes, 0 =no
  int align[2];  // first is matrix_1 pos(i) ,second is second matrix (j)
  int aln_length; // dynamically extended length of alignment so far
  char kind;
};


class alignment{   // structure for alignment and score, one for each scoring
public:
  float best_score; // the final score
  int length;       // the alignment length
  int gaps;         // number of gaps
  int over_string[30];  // string matrix 1 in alignment (gap represented with -1)
  int under_string[30]; // string matrix2 in alignment
};




float model3[1000][4]; // declaration of reversed second profile 
// the "30" is only for memeory, might be changed for other applications


alignment *score(int width1, int width2, float matrix1[][4],float matrix2[][4], double open_penalty, double ext_penalty)   // scoring function
{
  
  entry *F[width1+1][width2+1];  // matrix for storing ungapped alignments
  entry *I[width1+1][width2+1];  // matrix for insertions

  entry *B[width1+1][width2+1];  // matrix for deletions
  entry *E[width1+1][width2+1]; // matrix for ending alignment after gap
  
  //cout <<"inside: "<< open_penalty <<" "<<ext_penalty<<"\n";
int i; // counter for first profile, and later some other stuff
  int j; // counter for second profile, 


 //   cout<<"inside scorer\n";
//  for (i=0; i <=3; i++){
//      for(j=1; j <= width1; j++){

//        cout << matrix1[j][i]<<"\t";

//  	}

//      cout<<"\n";
//    }
//  cout<<"\n";
//   for (i=0; i <=3; i++){
//      for(j=1; j <= width2; j++){

//        cout << matrix2[j][i]<<"\t";

//  	}

//      cout<<"\n";
//    }


  
//   cout<<"\n"; 

  float nogap_score;   // score in a position without gaps
 
 
  float start_insert; // variables for cmparing scores, basically
  float extend_insert;
  float start_deletion;
  float extend_deletion;
  float max_score=0;
  float end_insert;
  float end_deletion;
  float end_continue;
  
  float sum_i; // counter for sums in a position in profile1
  float sum_j; // counter for sums in a position in profile2
  //float IC1; // information content of position in profile 1
  //float IC2; // information content of position in profile 2
  int align_i[40]; // keeping alignment for printing
  int align_j[40]; 
  int align_length; // length of alignment
  int counter =0;   // another counter variable
  int number_of_gaps=0; // number of gaps
  // define and zero out the score tableS
 
  // test













 
  for (i=0; i<=width1; ++i){
    for (j=0; j<=width2; ++j){
      
      F[i][j] = new entry;
      F[i][j]->score=0;
      F[i][j]->cell_score=0;
      F[i][j]->insert=0;
      F[i][j]->deletion=0;
      F[i][j]->father=NULL;
      F[i][j]->align[0] = 0;
      F[i][j]->align[1] = 0;
      F[i][j]->aln_length = 0;
      F[i][j]->kind ='F';
      
      I[i][j] = new entry;
      I[i][j]->score=0;
      I[i][j]->cell_score=0;
      I[i][j]->insert=0;
      I[i][j]->deletion=0;
      I[i][j]->father=NULL;
      I[i][j]->align[0] = 0;
      I[i][j]->align[1] = 0;
      I[i][j]->aln_length = 0;
      I[i][j]->kind ='I';
     
      
      B[i][j] = new entry;
      B[i][j]->score=0;
      B[i][j]->cell_score=0;
      B[i][j]->insert=0;
      B[i][j]->deletion=0;
      B[i][j]->father=NULL;
      B[i][j]->align[0] = 0;
      B[i][j]->align[1] = 0;
      B[i][j]->aln_length = 0;
      B[i][j]->kind ='B';
      
      E[i][j] = new entry;
      E[i][j]->score=0;
      E[i][j]->cell_score=0;
      E[i][j]->insert=0;
      E[i][j]->deletion=0;
      E[i][j]->father=NULL;
      E[i][j]->align[0] = 0;
      E[i][j]->align[1] = 0;
      E[i][j]->aln_length = 0;
      E[i][j]->kind ='E';

    }
  }
  
  entry *best_pntr; // pointer to the best entry so far
  

  // cout << "vidd1,2:"<<width1<<" "<<width2<<"\n";
  /*----------------------------------------
    Scoring engine
    --------------------------------------*/
  for (i=1; i<=width1; ++i){ // go over all pos vs all pos
    for (j=1; j<=width2; ++j){
      nogap_score=0; // initialized
      sum_i = 0; // calculate the sum of the position
      sum_j = 0;
     
      for (nucleotide=0; nucleotide<=3; ++nucleotide){   // go through nuclootides in position
	
	// the actual score model score
	// INFO -model, based on sums of squared diffs. Max diff is 8.
	// score = max diff (= sum1**2 + sum2**2) -actual diff
	// the max diff is usually slighty higher thna itcan be, due to info content constraints
	// gives a score between 8 (identical, max info content) and 0 (no identity)

	nogap_score += powf((matrix1[i][nucleotide]- matrix2[j][nucleotide]), 2);
	sum_i += matrix1[i][nucleotide];
	sum_j += matrix2[j][nucleotide];

	
	//cout <<sum_i<<"\n";
      }
      //  nogap_score = 1 / (nogap_score +1);
      //  cout<<"IC1 "<< IC1 << " IC2: "<< IC2 <<" "<< nogap_score <<"\n";

      // nogap_score = pow(sum_i, 2)+ pow(sum_j, 2) - nogap_score;

     

      nogap_score = 2 - nogap_score;
     
      

      // define the three different scores  


      F[i][j]->score= (nogap_score + F[i-1][j-1]->score); // define non-gapped alignment score
      F[i][j]->father= F[i-1][j-1];
      F[i][j]->cell_score = nogap_score;
      F[i][j]->align[0] =i;
      F[i][j]->align[1] =j;
     

      if (F[i][j]->score >= max_score){ // check if best score yet
	max_score = F[i][j]->score;
	best_pntr = F[i][j];  // point to this entry
	//cout <<"internal score: "<< nogap_score <<"\n";
	//cout <<"F"<< i<<" "<<j<< " "<<max_score<<"\n";
      }

      // inserts in  profile1 (i) profile
      start_insert  = F[i-1][j]->score - open_penalty; // define cost to open gap-insertion from here
      extend_insert = I[i-1][j]->score - ext_penalty;  // cost of extending gap-insertion from here
      
     

      if (start_insert >= extend_insert){        // take the best one
	I[i][j]->score = start_insert;
	I[i][j]->father= F[i-1][j];
	I[i][j]->cell_score = - open_penalty;
	I[i][j]->insert=1;
	I[i][j]->align[0] =i;
	I[i][j]->align[1] =0;
      }
      else{
	I[i][j]->score= extend_insert;
	I[i][j]->father= I[i-1][j];
	I[i][j]->cell_score = - ext_penalty;
	I[i][j]->insert=1;
	I[i][j]->align[0] =i;
	I[i][j]->align[1] =0;
      }
      if (I[i][j]->score >= max_score){  // update if best score yet
	max_score = I[i][j]->score;
	best_pntr=I[i][j];
      }


      // deletions in profile1 (i) profile
      start_deletion  = F[i][j-1]->score - open_penalty; // open deletion gap
      extend_deletion = B[i][j-1]->score - ext_penalty;  // extend deletion gap
      
      if (start_deletion >= extend_deletion){    // check which one is highest    
	B[i][j]->score= start_deletion;
	B[i][j]->father= F[i][j-1];
	B[i][j]->cell_score = - open_penalty;
	B[i][j]->deletion=1;
	B[i][j]->align[0] =0;
	B[i][j]->align[1] =j;

      }
      else{
	B[i][j]->score= extend_deletion;
	B[i][j]->father= B[i][j-1];
	B[i][j]->cell_score = - ext_penalty;
	B[i][j]->deletion=1;
	B[i][j]->align[0] =0;
	B[i][j]->align[1] =j;

      }
      if (B[i][j]->score >= max_score){ // update if best sofar
	max_score = B[i][j]->score;
	best_pntr=B[i][j];
      }
      // end alignment after gap

      end_insert   = I[i-1][j-1]->score + nogap_score;  // start real alignment after insertion-gap 
      end_deletion = B[i-1][j-1]->score + nogap_score;  // start real alignent after deletion-gap
      end_continue = E[i-1][j-1]->score + nogap_score;  // continue real alignment 
      
      if (end_insert>=end_deletion && end_insert>=end_continue ){ // check which score is highest
	E[i][j]->score= end_insert;
	E[i][j]->father= I[i-1][j-1];
	E[i][j]->cell_score = nogap_score;
	E[i][j]->align[0] =i;
	E[i][j]->align[1] =j;


      }
      else if(end_deletion >= end_insert && end_deletion >=end_continue)
	{
	E[i][j]->score= end_deletion;
	E[i][j]->father= B[i-1][j-1];
	E[i][j]->cell_score = nogap_score;
	E[i][j]->align[0] =i;
	E[i][j]->align[1] =j;

      }

      else{
	E[i][j]->score= end_continue;
	E[i][j]->father= E[i-1][j-1];
	E[i][j]->cell_score = nogap_score;
	E[i][j]->align[0] =i;
	E[i][j]->align[1] =j;
      }
      if (E[i][j]->score > max_score){ // update if highest yet
	max_score = E[i][j]->score;
	best_pntr =  E[i][j];
      }
     
      
 

    }
  }

 //   // print out score_table, only for diagnostics

 //   cout<< "\n\n score table\n";
//    for (pos1=0; pos1<=width1; ++pos1){
//      for (pos2=0; pos2<=width2; ++pos2){
      
//        // cout <<score_table[pos1][pos2]->score<<"\t";
//        printf("%5.5f\t", score_table[pos1][pos2]->score);   
//  }
    
//      cout <<"\n";
//    } 


  /*---------------------------------------
    function for walking through the alignment,
    starting with the best scoring cell, 
    going back throgh the father-pointers


    -----------------------------------------  */
  // cout<<"max score: " << max_score<<"\n"; 
  
  alignment *align = new alignment;
  align->best_score= max_score ;


  counter=0;
  align_length=0;
  entry *current_pntr=best_pntr; // for walking, start with the best score
  while (current_pntr->father != NULL){ // while the father of the current pointer exists, walk through the best posible alignment
    
    // cout<< current_pntr->align[0]<< " "<<current_pntr->align[1]<< "\t "<<current_pntr->cell_score<<" "<< current_pntr->kind << "\n"; 


 align_i[counter]=  current_pntr->align[0];
 align_j[counter]=  current_pntr->align[1];
 align_length ++;
 current_pntr=current_pntr->father;

 counter ++;

  }
 
  align->length= align_length;
  
  // ineffective way of annotating, I dont care.
  for ( i=align_length-1; i>=0; --i){ // walk through alignment for printing, first profile
    
  
    //  cout <<align_i[i]<<"\t";
    align->over_string[i]=align_i[align_length -i -1]; // fill in alignment in alignment-object
      if (align_i[i]== 0){ // count the number of gaps
	number_of_gaps =number_of_gaps +1;
      }  

  
  }
  // cout <<"\n";
  for ( i=align_length-1; i>=0; --i){ // walk through alignment for printing, second profile
   
    // cout <<align_j[i]<<"\t";
      align->under_string[i]=align_j[align_length-i-1]; // fill in alignment in alignment-object
 if (align_j[i]== 0){ // count the number of gaps
	number_of_gaps =number_of_gaps +1;
      }  

  }
  //cout <<"\n\n";

 align ->gaps = number_of_gaps; // fill in number of gaps in alignment-object
 
 // kill off all entries in memory

for (i=0; i<=width1; ++i){
    for (j=0; j<=width2; ++j){
      
      delete F[i][j];
     
      delete I[i][j];
     
     
      
      delete B[i][j];
      
      
      delete E[i][j];
     

    }
  }











 return (align); // return alignment object
delete align;

}



void reverse(float model[][4], int width)
{   // reverses a matrix
  // arguments: a matrix, its width
  // created matrix is global
  

  
  for (pos1=1; pos1<=width; ++pos1){
    for (nucleotide=0; nucleotide<=3; ++nucleotide){
      
      model3[width-pos1+1][3-nucleotide]= model[pos1][nucleotide];
      // cout << model3[width-pos1][3-nucleotide]<<" ";
      
    }
    //  cout<<"\n";
  }
  


}

int main(int argc, char *argv[]){

  /****
 Arguments: profile file adress,  profile ID2 v(erbose) 


  ***/

 
  int vidd1;
  int vidd2;
  int verbose=1; 
  double open_penalty;
  double ext_penalty;

  if (argv[3]== NULL){
    open_penalty=3.0;
    ext_penalty =0.01; 
  }
  else{
    open_penalty= atof(argv[3]);     // open gap penalty
    ext_penalty=atof(argv[4]);  // extend gap penalty

  }
  

 

   cout <<"open " <<open_penalty<<" ext "<<ext_penalty<<endl;

   
  int i;
  // connect to database
  // read in profiles from files
 


  // retrieve stuff
  
  // first: widths of matrices
  // define width of profiles: vidd 1 and width2
  
 
 
 
  // second: define matrices, define waht representation also
  // IMPORTANT profiles are 1 pos longer than normal ,for convinience with numbering, so ops 1 is reaaly pos 1, not 0. O is not defined.
 
  //int basecounter=0;
  //int max =10000;
  
  // retrieve first matrix
  int counter;
  int counter1; // for iteration over profile 1
  int counter2;  // for iteration over profile 2
  FILE *profile1;
  int basecounter;
  char out[9];
  //  int counter=0;
  
  if (( profile1 = fopen( argv[1] , "r"))==NULL) 
    {
      printf( "Cannot open file1\n");
      exit(1);
    }
  
   

  // try a scanf approach
  
  float temp_array[500]; // place to store data read in
  // position 0 is left to be, for simplicity when filling matrix from array
  
  counter=0;
  float floater; // for storing temporary data
  while (!feof (profile1)){
    fscanf(profile1, "%f ", &floater);
    //cout<<"floater: "<<floater <<"\n";
    // cout << counter<<"\n";
    temp_array[counter+1]=floater;
    counter ++;

  }
  // fscanf(profile1, "%f ", &floater);
  //cout<<"floater: "<<floater <<"\n";
  
  
  // cout<< "vidd: " <<counter/4<<"\n";;
  //cout<< "vidd: " <<counter/4<<"\n";;
  vidd1=counter/4;
  float matris1[vidd1+1][4];
  basecounter=0;
  int pos=1;
  float position_weights[500];  // stores the number of sequences 
                               // in each position
  // cout<< "vidd1 now: " <<vidd1<<"\n";;
  // zero it out
  for(i=0;i<=499; ++i){
    position_weights[i]=0;
  }




  // fill in the matrix with these data:
  for (i=1; i<=counter; ++i){
    
    if (pos  > vidd1){
      pos=1;
     
      // cout <<" base: "<<basecounter <<"\n";
      basecounter ++;
    }
    //cout<< "pos"<<pos<<" base" <<basecounter<<" " <<temp_array[i]<<" ";
    matris1[pos][basecounter] = temp_array[i];
    position_weights[pos] +=  temp_array[i];
    pos++;
  
  } 

  fclose (profile1);


  // check: printout of profile1
  // normalize data
  
  // try, print out  profile, diagnostic
  for (counter2=0; counter2 <=3; counter2++){
    
    // cout <<"base" <<counter2<<"\t";
    
    for(counter1=1; counter1 <= vidd1; counter1++){
      
       matris1[counter1][counter2]=matris1[counter1][counter2]/position_weights[counter1];
       //  cout<<counter1<<": " << matris1[counter1][counter2]<<"\t";
      
      
    }
    
    //   cout<<"\n";
  }
  //cout<<"\n";
  //cout<<"weights:\t"; 
 


  
  // width established, read in whole profile
  //float matris1[vidd1+1][4];
  
  counter=1;
  basecounter=0;
  

   FILE *profile2;
 
  //  int counter=0;
  
  if (( profile2 = fopen( argv[2] , "r"))==NULL) 
    {
      printf( "Cannot open file2\n");
      exit(1);
    }
  
   

  
  

  
  counter=0;
 
  while (!feof (profile2)){
    fscanf(profile2, "%f ", &floater);
    //cout<<"floater: "<<floater <<"\n";
    
    temp_array[counter+1]=floater;
    counter ++;
  }
  // fscanf(profile1, "%f ", &floater);
  //cout<<"floater: "<<floater <<"\n";
  
  
  
  // cout<< "vidd: " <<counter/4<<"\n";;
  vidd2=counter/4;
  float matris2[vidd2+1][4];
  basecounter=0;
  pos=1;
  // cout<< "vidd now"<<vidd2<<"\n";
  // cout<< "vidd1 now"<<vidd1<<"\n"; 






  // zero it out
  for(i=0;i<=499; ++i){
    position_weights[i]=0;
  }


  
  

  // fill in the matrix with these data:
  for (i=1; i<=counter; ++i){
    
    if (pos  > vidd2){
      pos=1;
     
      // cout <<" base: "<<basecounter <<"\n";
      basecounter ++;
    }
    //cout<< "pos"<<pos<<" base" <<basecounter<<" " <<temp_array[i]<<" ";
    matris2[pos][basecounter] = temp_array[i];
    position_weights[pos] +=  temp_array[i];
    pos++;
  
  } 

  fclose (profile2);


  // check: printout of profile1
  // normalize data
  
  // try, print out  profile, diagnostic
  for (counter2=0; counter2 <=3; counter2++){
    
    // cout <<"base" <<counter2<<"\t";
    
    for(counter1=1; counter1 <= vidd2; counter1++){
      
       matris2[counter1][counter2]=matris2[counter1][counter2]/position_weights[counter1];
       //  cout<<counter1<<": " << matris2[counter1][counter2]<<"\t";
      
      
    }
    
    // cout<<"\n";
  }
 
  //cout <<vidd2<<" vidd "<<vidd2<<"\n";
 
  
  alignment *score1;//= new alignment;  // the two alignment objects that the
  //cout <<vidd2<<" vidd "<<vidd2<<"\n";
  alignment *score2;//= new alignment;  // score engine will generate
  //float score1;
  //float score2;
  //cout <<vidd2<<" vidd "<<vidd2<<"\n";
  reverse (matris2, vidd2);           // reverse the second profile for +- scoring
  // as model3
  
  
  //  cout << "comparing:\n";
  // cout <<namelist[counter1] <<"\n";
  //cout <<namelist[counter2] <<"\n";
  
  //cout <<vidd2<<" vidd "<<vidd2<<"\n";
  //exit(1);
  // score the profiles against each other




  score1= score( vidd1, vidd2, matris1, matris2, open_penalty, ext_penalty);      // score profile 1 vs 2
  

 score2 = score (vidd1,vidd2, matris1, model3, open_penalty, ext_penalty );    // score profile 1 vs reversed 2
  
  // cout <<"test: score1 score: "<< score1->best_score<<" \nlength: "<< score1->length<<"\nover1:  "<<score1->over_string[0] << "\n";
  
  // cout << "\n\n\nScore1 "<< score1->best_score <<"\n";
  
  
  // see what score is highest and print out the score, orientation and alignment
  
  verbose=1;
  
  if (score1->best_score > score2->best_score)  // what final score is highest?
    { 
      if (verbose== 1){ // verbose, print alignment
	
	cout<<"PFM1\t";	
	for (i=0;  i <= score1->length -1 ; ++i){
	  cout<< score1->over_string[i]<<"\t";
	} 
	cout <<"\n";
	cout<<"PFM2\t";
	for (i=0;  i <= score1->length -1; ++i){
	  cout<< score1->under_string[i]<<"\t";
	} 
	
	cout <<"\n";
	
      }
        cout <<"INFO\t"<<argv[1]<<"\t"<<argv[2]<<"\t" << score1->best_score  <<"\t"<< vidd1 <<"\t"<< vidd2<<"\t++\t"<<score1->length <<"\t"<<score1->gaps <<"\n";
	//cout<<score1->best_score <<"\n";    
      
      
    }
  else
    { 
      
      if (verbose== 1){ // verbose, print alignment
	
	cout<<"PFM1\t";
	for (i=0;  i <= score2->length -1; ++i){
	  cout<< score2->over_string[i]<<"\t";
	} 
	cout <<"\n";	
	cout<<"PFM2\t";
	for (i=0;  i <= score2->length -1; ++i){
	  cout<< score2->under_string[i]<<"\t";
	} 
	
	cout <<"\n";
	
      }
      
      
      
      
      
      cout<<"INFO\t"<<argv[1]<<"\t"<<argv[2]<<"\t"<< score2->best_score <<"\t"<< vidd1 <<"\t"<< vidd2 <<"\t+-\t"<<score2->length<<"\t"<<score2->gaps  <<"\n";
	  //cout<<score2->best_score <<"\n";   
    }
  
   delete score1;
   delete score2;
  // numberofcomparsons++; // count number of comparisons  
}
	  
  
  
 

























