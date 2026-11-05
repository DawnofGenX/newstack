#include <stdio.h>

/* Each suite lives in its own translation unit and returns its failure count. */
int run_counters_tests(void);
int run_json_tests(void);
int run_contract_tests(void);

int main(void)
{
    int failures = 0;

    failures += run_counters_tests();
    failures += run_json_tests();
    failures += run_contract_tests();

    if (failures != 0) {
        fprintf(stderr, "%d check(s) failed\n", failures);
        return 1;
    }

    printf("all checks passed\n");
    return 0;
}
