/* The CPU fast path of brain/engine.py (loaded by brain/kernel.py). Same arithmetic as the torch ops in
 * Engine.step, in the same order, so the two give the same spikes and the same state bit for bit
 * (tests/test_engine.py). Build with -ffp-contract=off: a fused multiply-add would round differently.
 *
 * Why it is faster: the torch step walks the (flies x neurons) state about a dozen times per step and
 * allocates full-size temporaries; lif_dense walks it once.
 */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#define BLOCK 4096

/* The dense part of a step, for all n = flies * neurons state entries:
 *     live   = free_at <= t
 *     v      = live ? v * dv + g * g2v : v        (g before its own decay)
 *     g      = live ? g * dg : g
 *     firing = live & (v > vth);   live &= ~firing
 * Returns the number of firing entries; out[0..count) holds their flat indices in ascending order.
 * out must have room for n indices. */
int64_t lif_dense(float *restrict v, float *restrict g, const int32_t *restrict free_at, uint8_t *restrict live,
                  int64_t n, int32_t t, float dv, float g2v, float dg, float vth, int64_t *restrict out)
{
    int maxt = omp_get_max_threads();
    int64_t counts[maxt];
    int T = 1;
    #pragma omp parallel if(n > 65536)
    {
        int id = omp_get_thread_num(), nt = omp_get_num_threads();
        if (id == 0) T = nt;
        int64_t lo = n * id / nt, hi = n * (id + 1) / nt, c = 0;
        int64_t *o = out + lo;                      /* this thread's spikes start at its own slice */
        for (int64_t b = lo; b < hi; b += BLOCK) {
            int64_t e = b + BLOCK < hi ? b + BLOCK : hi;
            int any = 0;
            for (int64_t i = b; i < e; i++) {       /* branch-free, so the compiler vectorises it */
                int l = free_at[i] <= t;
                float vi = l ? v[i] * dv + g[i] * g2v : v[i];
                float gi = l ? g[i] * dg : g[i];
                int f = l & (vi > vth);
                v[i] = vi;
                g[i] = gi;
                live[i] = (uint8_t)(l + f);         /* 0 refractory, 1 live, 2 firing */
                any |= f;
            }
            if (any)
                for (int64_t i = b; i < e; i++)
                    if (live[i] == 2) { o[c++] = i; live[i] = 0; }
        }
        counts[id] = c;
    }
    int64_t total = counts[0];
    for (int id = 1; id < T; id++) {                /* close the gaps between the threads' slices */
        if (counts[id]) memmove(out + total, out + n * id / T, counts[id] * sizeof(int64_t));
        total += counts[id];
    }
    return total;
}

/* Synaptic input of `spikes` (ascending flat indices fly * N + neuron), added to g of the live targets:
 *     g[fly, post] += syn * w * live[fly, post]     for every outgoing edge of every transmitting spike
 * in spike order, each spike's edges in connectome order, which is the order torch's index_add_ uses.
 * Flies never share a target, so each fly's spikes go to one thread. */
void lif_deliver(float *restrict g, const uint8_t *restrict live, const int64_t *restrict spikes, int64_t ns,
                 int64_t N, const int64_t *restrict ptr, const int64_t *restrict post, const float *restrict syn,
                 const uint8_t *restrict transmits, float w)
{
    if (ns <= 0) return;
    int64_t *start = malloc((ns + 1) * sizeof *start);
    int64_t groups = 0, prev = -1;
    for (int64_t k = 0; k < ns; k++) {
        int64_t fly = spikes[k] / N;
        if (fly != prev) { start[groups++] = k; prev = fly; }
    }
    start[groups] = ns;
    #pragma omp parallel for schedule(dynamic, 1) if(groups > 1 && ns > 32)
    for (int64_t q = 0; q < groups; q++) {
        int64_t base = spikes[start[q]] / N * N;
        float *gf = g + base;
        const uint8_t *lf = live + base;
        for (int64_t k = start[q]; k < start[q + 1]; k++) {
            int64_t pre = spikes[k] - base;
            if (!transmits[pre]) continue;
            for (int64_t e = ptr[pre]; e < ptr[pre + 1]; e++) {
                int64_t j = post[e];
                gf[j] += syn[e] * w * (float)lf[j];
            }
        }
    }
    free(start);
}
