import numpy as np
import scipy.fftpack as fftpack


class Guess:
    def __init__(self):
        pass


class ExpDecayGuess(Guess):
    """Guess for f(x) = a * e^(-x/b)  +  c"""

    def make_guess(self, y, x):

        length = len(y)
        val_init = y[0:round(length / 20)].mean()
        val_fin = y[-round(length / 20):].mean()

        a = val_init - val_fin

        c = val_fin

        # guess b as point where data has fallen to 1/e of init value
        idx = (np.abs(y - a / np.e - c)).argmin()
        b = x[idx]

        return [a, b, c]


class ExpDecaySinGuess(Guess):
    """Guess for f(x) = a * e^(-x/b) sin(wx+p)  + c"""

    def make_guess(self, y, x):

        a = y.max() - y.min()

        c = y.mean()

        # guess b as point half way point in data
        b = x[round(len(x) / 2)]

        # Get initial guess for frequency from a fourier transform
        yhat = fftpack.rfft(y - y.mean())
        idx = (yhat**2).argmax()
        freqs = fftpack.rfftfreq(len(x), d=(x[1] - x[0]) / (2 * np.pi))
        w = freqs[idx]

        p = 0

        return [a, b, w, p, c]


class PowerDecayGuess(Guess):

    """Guess for f(x) = a * b^x + c"""

    def make_guess(self, y, x):

        length = len(y)
        val_init = y[0:round(length / 20)].mean()
        val_fin = y[-round(length / 20):].mean()

        a = val_init - val_fin

        c = val_fin

        # find index where data has fallen to 1/e of init value
        idx = (np.abs(y - a / np.e - c)).argmin()
        # guess b as e^(-1/x[idx]):
        b = np.e ** (-1 / x[idx])

        return [a, b, c]


class RabiT1Guess(Guess):

    """Guess for f(x) = e^(-x/b) cos^2(wx/2 + p)"""

    def make_guess(self, y, x):

        # guess b as point half way point in data
        b = x[round(len(x) / 2)]

        # Get initial guess for frequency from a fourier transform
        yhat = fftpack.rfft(y - y.mean())
        idx = (yhat ** 2).argmax()
        freqs = fftpack.rfftfreq(len(x), d=(x[1] - x[0]) / (2 * np.pi))
        w = freqs[idx] * 2

        return [b, w]


class CosineGuess(Guess):

    """Guess for f(x) = a * cos(wx + p) + b"""

    def make_guess(self, y, x):

        b = y.mean()

        a = y.max() - y.min()

        # Get initial guess for frequency from a fourier transform
        yhat = fftpack.rfft(y - y.mean())
        idx = (yhat ** 2).argmax()
        freqs = fftpack.rfftfreq(len(x), d=(x[1] - x[0]) / (2 * np.pi))
        w = freqs[idx]

        p = 0

        return [a, w, p, b]

class LinearGuess(Guess):
    """Guess for f(x) = m*x  +  b"""

    def make_guess(self, y, x):

        length = len(y)
        y1 = y[np.argmax(x)]
        y2 = y[np.argmin(x)]
        m = (y1 - y2)/length

        idx = np.argmin(abs(x))
        b = y[idx]



        return [m, b]