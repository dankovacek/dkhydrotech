import numpy as np
import scipy.stats as st


def calculate_Q(data):
    mean = np.mean(data)
    stdev = np.std(data)
    
    return np.power(10,mean + K * stdev)

def calculate_skew(data):
    """
    Calculate weighted skew.
    Reference: CFA2 Manual.
    Based on (Wallis, Matalas, and Slack)
    K_n is 'standard normal deviate' which I'm assuming means standard deviation
    """

    g = abs(np.log10(st.skew(data)))

    mu = np.mean(np.log10(data))
    s = np.std(np.log10(data))
    alpha = 4 / g**2
    beta = 0.5 * s * g
    epsilon = mu - 2 * s / g

    return K, MSE_g

def calculate_K_weighted(data):
    g = abs(np.log10(st.skew(data)))

    if g == 0: 
        print('Skew cannot equal zero.')
        return None

    if g <= 0.9:
        A = -0.33 + 0.08 * g
    else:
        A = -0.52 + 0.3 * g

    if g <= 1.5:
        B = 0.94 - 0.26 * g
    else:
        B = 0.55

    # assuming 'standard normal deviate'
    K_n = np.std(data)

    K = (2 / g) * (((K_n - g/6)*g/6 + 1)**3 - 1)

    # MSE_g = (A - B * (np.log10(len(data)/10)))
    return K