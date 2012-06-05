import numpy 
import scipy.stats
avg_ker_per_app = 2
ker_num = 10
ker_perf_mean = 80
ker_perf_std = 10
app_num = 1000

#rvs = numpy.linspace(0.5*ker_perf_mean, 1.5*ker_perf_mean, ker_num-1)
#cdfs = scipy.stats.norm.cdf(rvs, ker_perf_mean, ker_perf_std)
##print cdfs
##probs1 = numpy.roll(cdfs, 1)
#probs1 = numpy.insert(cdfs, 0, 0)
##print probs1
##probs2 = numpy.roll(cdfs, -1)
#probs2 = numpy.append(cdfs, 1)
##print probs2
#probs = probs2-probs1
#probs = probs * avg_ker_per_app
##prob_mean = float(avg_ker_per_app)/float(ker_num)
##probs_adj = numpy.random.uniform(0, prob_mean, size=ker_num/2)
##probs_adj = numpy.linspace(0, prob_mean, ker_num/2+1, endpoint=False)[1:]
##print probs_adj
##probs1 = probs_adj + prob_mean
##probs2 = - (probs_adj - prob_mean)
#probs0 = numpy.linspace(0.1,0.9, ker_num)
#probs = probs0
#probs = numpy.concatenate((probs1, probs2))
#print probs
probs = numpy.array([0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.9])
occ = [0,1,0,0,1,0,1,1,0,1]
cov = 0.4
accs = ['gen%d'%i for i in xrange(10)]
active_k = dict()
for o,p,acc in zip(occ, probs, accs):
    if o:
        active_k[p] = acc
ks= sorted(active_k.items())
kr = ks[:]
kr.reverse()
print ks
print kr

#kernel_occ = [ scipy.stats.bernoulli.rvs(p, size=app_num) for p in probs ]

#for cov in zip(*kernel_occ):
    #print cov.count(1), cov

#print probs
