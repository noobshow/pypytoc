#ifndef Py_STRUCTMEMBER_H
#define Py_STRUCTMEMBER_H
#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h> /* For offsetof */
#ifndef offsetof
#define offsetof(type, member) ( (int) & ((type*)0) -> member )
#endif


typedef struct PyMemberDef {
	/* Current version, use this */
	char *name;
	int type;
	Py_ssize_t offset;
	int flags;
	char *doc;
} PyMemberDef;


/* Types */
#define T_INT		1
#define T_OBJECT	6
#define T_OBJECT_EX	16	/* Like T_OBJECT, but raises AttributeError
				   when the value is NULL, instead of
				   converting to None. */

/* Flags */
#define READONLY      1
#define RO            READONLY                /* Shorthand */


#ifdef __cplusplus
}
#endif
#endif /* !Py_STRUCTMEMBER_H */
