/* Tiny test harness: no dependencies, exit code != 0 on any failed check. */
#ifndef NWTEST_H
#define NWTEST_H
#include <stdio.h>
extern int nwtest_failed, nwtest_checked;
#define CHECK(c) do { nwtest_checked++; if (!(c)) { nwtest_failed++; printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)
#define CHECK_EQ(a, b) do { long long _a = (long long)(a), _b = (long long)(b); nwtest_checked++; \
    if (_a != _b) { nwtest_failed++; printf("FAIL %s:%d  %s == %s  (%lld vs %lld)\n", __FILE__, __LINE__, #a, #b, _a, _b); } } while (0)
#endif
