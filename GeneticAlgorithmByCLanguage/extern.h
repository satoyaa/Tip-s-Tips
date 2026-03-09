#ifndef EXTERN_H
#define EXTERN_H

#define MAX_ITERATION 1000
#define POPULATION 100
#define MAX_TIPS 100
#define M_PI 3.14159265358979323846

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
    int Tag1;
    int Tag2;
    int Tag3;
    int Tag4;
    int Tag5;
} Tags;

extern void initialize();
extern void selection();
extern void calc_fitness();
extern void crossover();
extern void mutation();
extern void save(const char *filename);


extern double fitness[POPULATION];
extern TIPS genes[POPULATION][MAX_TIPS]; 
extern DataItem dataset[50];
extern double best;
extern int best_index;
extern int maxWidth;
extern int tipWidth;
extern int tipHeight;

#endif
