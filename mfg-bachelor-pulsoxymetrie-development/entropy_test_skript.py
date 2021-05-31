"""

Test skript to test the entropy function. No further meaning for the RSCD Algorithm, only for debugging/testing

author: Jonas Christiansen
"""

from RSCD import entropy

if __name__ == "__main__":
    from scipy.stats import uniform, norm, expon
    #test script
    # taking random variables from Uniform distribution

    print("=========== TEST ===========")
    print("")

    print("=========== Uniform Test ===========")
    testunif = uniform.rvs(size=100, loc=5, scale=10) # auch möglich zum testen: 'norm' statt 'uniform'
    print(entropy(testunif, 150))
    print("")

    print("=========== Norm Test ===========")
    normf = norm.rvs(size=100, loc=5, scale=10)  # auch möglich zum testen: 'norm' statt 'uniform'
    print(entropy(normf, 150))
    print("")

    print("=========== Exponential Test ===========")
    exponf = expon.rvs(size=100, loc=5, scale=10)  # auch möglich zum testen: 'norm' statt 'uniform'
    print(entropy(exponf, 150))
    print("")
