#include <iostream>
#include <string>

#include "check.hpp"

void counts_tests();
void json_tests();
void contract_tests();

int main() {
    counts_tests();
    json_tests();
    contract_tests();
    return textstat::check::summary();
}
