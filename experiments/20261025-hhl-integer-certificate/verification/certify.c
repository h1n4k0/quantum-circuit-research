/* Exact integer numerical certificate for the frozen HHL datapath.
 * Circuit semantics derive from andigu/uncompute 64b5a13 (Apache-2.0).
 * This independently written evaluator imports no simulator/model code.
 * Requires an unsigned 128-bit integer type; no floating-point operations.
 */
#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "generated.h"

typedef unsigned __int128 u128;
#define SCALE (UINT64_C(1) << 60)
#define OUTPUT_SCALE (UINT64_C(1) << 28)
#define MODULUS (UINT64_C(1) << 33)

static uint64_t down(uint64_t a, uint64_t b) {
    assert(a < 2*SCALE && b <= SCALE);
    return (uint64_t)(((u128)a*b) >> 60);
}
static uint64_t up(uint64_t a, uint64_t b) {
    assert(a < 2*SCALE && b <= SCALE);
    return (uint64_t)((((u128)a*b) + SCALE-1) >> 60);
}

/* asin(z) = z sum c_n z^(2n). All coefficients are nonnegative.
 * 32 terms; the omitted tail is <= (1/2)^65/(1-1/4) < 2^-60.
 * Every lower operation rounds down, every upper operation rounds up.
 */
static void enclose(uint32_t x, uint64_t *lo, uint64_t *hi) {
    u128 numerator=(u128)32768*SCALE;
    uint64_t zl=(uint64_t)(numerator/x);
    uint64_t zu=(uint64_t)((numerator+x-1)/x);
    assert(zu <= SCALE/2);
    uint64_t tl=down(zl,zl), tu=up(zu,zu);
    uint64_t pl=COEF_LO[31], pu=COEF_HI[31];
    for(int n=30;n>=0;--n) {
        pl=COEF_LO[n]+down(pl,tl);
        pu=COEF_HI[n]+up(pu,tu);
    }
    *lo=down(pl,zl);
    *hi=up(pu,zu)+1;
    assert(*lo <= *hi && *hi < SCALE);
}

static unsigned getbit(uint32_t value,int i) {
    return i<0 ? 0 : ((value>>i)&1);
}
/* Explicit Booth truth table indexed by low/middle/high input bits. */
static int digit(uint32_t value,unsigned s) {
    const int recode[8]={0,1,1,2,-2,-1,-1,0};
    unsigned i=getbit(value,2*(int)s-1)
             +2*getbit(value,2*(int)s)+4*getbit(value,2*(int)s+1);
    return recode[i];
}
static int64_t signed_row(uint32_t operand,int d,int shift) {
    if(!d) return 0;
    uint64_t v=operand;
    if(d==2 || d==-2) ++shift;
    v=shift<0 ? v>>(-shift) : v<<shift;
    return d<0 ? -(int64_t)v : (int64_t)v;
}
static uint64_t addend(uint32_t x,const struct Leaf *leaf,
                       int64_t *minimum_window,int64_t *maximum_window) {
    /* Actual cyclic left rotation of the low 15 X bits, rather than
     * importing the upstream leaf_dn simplification. */
    unsigned shift=leaf->shift;
    uint32_t low=x&32767;
    uint32_t dn=shift ? ((low<<shift)|(low>>(15-shift)))&32767 : low;
    int64_t w=((int64_t)leaf->g1<<4)+(1<<16);
    int64_t q=0;
    const unsigned order[3]={2,1,0};
    for(unsigned i=0;i<3;++i) {
        unsigned s=order[i];
        q+=signed_row(dn>>3,digit(leaf->g2,s),2*(int)s-4);
        int64_t window=(w&131071)-q;
        assert(window>=0 && window<131072);
        if(window<*minimum_window) *minimum_window=window;
        if(window>*maximum_window) *maximum_window=window;
    }
    int64_t slope=w-q;
    assert(slope>=0 && slope<(1<<20));
    int64_t product=0;
    for(unsigned s=0;s<7;++s) {
        int sig=PRODUCT_B4[s]+11-2-2*(int)s;
        product+=signed_row((uint32_t)slope,digit(dn>>2,s),-sig)
                 * (INT64_C(1)<<PRODUCT_B4[s]);
    }
    int64_t result=(int64_t)leaf->g0-product+((int64_t)(dn>>2)<<7);
    return ((uint64_t)result)&(MODULUS-1);
}
static void put64(FILE *f,uint64_t x) {
    unsigned char b[8];
    for(unsigned i=0;i<8;++i) b[i]=(unsigned char)(x>>(8*i));
    assert(fwrite(b,1,8,f)==8);
}
static uint64_t distance(uint64_t a,uint64_t b) {return a>b?a-b:b-a;}

int main(int argc,char **argv) {
    assert(argc==2);
    FILE *out=fopen(argv[1],"wb"); assert(out);
    uint32_t cursor=65536, worst_x=0;
    uint64_t count=0,max_lo=0,max_hi=0,max_width=0,max_integer=0;
    uint64_t ambiguity=0,worst_addend=0,worst_asin_lo=0,worst_asin_hi=0;
    int64_t min_window=INT64_MAX,max_window=INT64_MIN;
    for(unsigned j=0;j<LEAF_COUNT;++j) {
        const struct Leaf *leaf=LEAVES+j;
        uint32_t width=1u<<leaf->bits;
        assert(leaf->lo==cursor && leaf->lo%width==0);
        assert(leaf->shift==15-leaf->bits && leaf->shift<=7);
        assert(leaf->g0%64==0 && leaf->g1>=1 && leaf->g1<61440 && leaf->g2<32);
        cursor+=width;
        assert(cursor<=2097152);
        for(uint32_t x=leaf->lo;x<cursor;++x) {
            uint64_t delta=addend(x,leaf,&min_window,&max_window),lo,hi;
            enclose(x,&lo,&hi);
            assert(delta<UINT64_C(1)<<32);
            uint64_t value=delta*OUTPUT_SCALE;
            uint64_t lower=value<lo ? lo-value : (value>hi ? value-hi : 0);
            uint64_t upper=distance(value,lo)>distance(value,hi)
                            ? distance(value,lo) : distance(value,hi);
            if(lower>max_lo) max_lo=lower;
            if(upper>max_hi) {
                max_hi=upper; worst_x=x; worst_addend=delta;
                worst_asin_lo=lo; worst_asin_hi=hi;
            }
            if(hi-lo>max_width) max_width=hi-lo;
            /* An integer interval check establishes the real-angle bound. */
            assert(upper<429*OUTPUT_SCALE);
            uint64_t rounded_lo=(lo+OUTPUT_SCALE/2)/OUTPUT_SCALE;
            uint64_t rounded_hi=(hi+OUTPUT_SCALE/2)/OUTPUT_SCALE;
            if(rounded_lo!=rounded_hi) ++ambiguity;
            uint64_t error=distance(delta,rounded_lo)>distance(delta,rounded_hi)
                         ? distance(delta,rounded_lo) : distance(delta,rounded_hi);
            if(error>max_integer) max_integer=error;
            assert(error<=429);
            put64(out,delta); put64(out,lo); put64(out,hi); ++count;
        }
    }
    assert(cursor==2097152 && count==2031616 && !fclose(out));
    printf("{\n  \"status\": \"PASS\",\n  \"domain_values\": %"PRIu64",\n",count);
    printf("  \"max_real_error_numerator_lower\": %"PRIu64",\n",max_lo);
    printf("  \"max_real_error_numerator_upper\": %"PRIu64",\n",max_hi);
    printf("  \"real_error_denominator_output_units\": %"PRIu64",\n",OUTPUT_SCALE);
    printf("  \"max_interval_width_numerator\": %"PRIu64",\n",max_width);
    printf("  \"rounded_ideal_ambiguities\": %"PRIu64",\n",ambiguity);
    printf("  \"max_rounded_real_integer_error\": %"PRIu64",\n",max_integer);
    printf("  \"worst_upper_bound_X\": %u,\n  \"worst_addend\": %"PRIu64",\n",worst_x,worst_addend);
    printf("  \"worst_asin_lower_Q60\": %"PRIu64",\n  \"worst_asin_upper_Q60\": %"PRIu64",\n",worst_asin_lo,worst_asin_hi);
    printf("  \"curvature_window_min\": %"PRId64",\n  \"curvature_window_max\": %"PRId64"\n}\n",min_window,max_window);
    return 0;
}
