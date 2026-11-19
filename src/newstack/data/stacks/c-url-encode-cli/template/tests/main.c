#include <stdio.h>

int run_urlenc_tests(void);

int main(void) {
    int failures = 0;
    failures += run_urlenc_tests();
    if (failures != 0) {
        fprintf(stderr, "%d check(s) failed\n", failures);
        return 1;
    }
    printf("all checks passed\n");
    return 0;
}
