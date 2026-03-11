#ifndef EXTERN_H
#define EXTERN_H

#define MAX_ITERATION 1000
#define POPULATION 100
#define M_PI 3.14159265358979323846
#define LOOPS 30
#define MAX_TIPS 100
//#define MUTATION_RATE 0.1
//#define CROSSOVER_RATE 0.7

typedef struct {
    double x;
    double y;
} TIPS;

typedef struct {
    double x;
    double y;
    char tags[3][10]; 
    double rotate;
} DataItem;

typedef struct {
    double Tag1;
    double Tag2;
    double Tag3;
    double Tag4;
    double Tag5;
} Tags;

extern void initialize();
extern void selection();
extern void calc_fitness();
extern void crossover();
extern void mutation();
extern void save(const char *filename);


extern int max_tips;
extern int num_tags;
extern char Taglist[100][64];
extern double fitness[POPULATION];
extern TIPS genes[POPULATION][MAX_TIPS]; 
extern DataItem dataset[50];
extern double best;
extern int best_index;
extern int maxWidth;
extern int tipWidth;
extern int tipHeight;
extern double crossover_rate;
extern double mutation_rate;

#endif
