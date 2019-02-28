#ifndef R_H__
#define R_H__

#ifndef LIBR
#define RAPI_EXTERN extern
#else
#define RAPI_EXTERN
#endif

// Rembedded.h
RAPI_EXTERN int (*Rf_initialize_R)(int ac, char **av);
RAPI_EXTERN void (*setup_Rmainloop)();
RAPI_EXTERN void (*run_Rmainloop)();


#endif /* end of include guard: R_H__ */
