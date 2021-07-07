# -*- coding: utf-8 -*-
import sys

import numpy as np
import pytest

from sktime.datasets import load_gunpoint
from sktime.transformations.panel.dictionary_based._sfa import SFA
from sktime.utils.data_processing import from_nested_to_2d_array


# Check the transformer has changed the data correctly.
@pytest.mark.parametrize(
    "binning_method", ["equi-depth", "equi-width", "information-gain", "kmeans"]
)
def test_transformer(binning_method):
    # load training data
    X, y = load_gunpoint(split="train", return_X_y=True)

    word_length = 6
    alphabet_size = 4

    p = SFA(
        word_length=word_length,
        alphabet_size=alphabet_size,
        binning_method=binning_method,
    )
    p.fit(X, y)

    assert p.breakpoints.shape == (word_length, alphabet_size)
    i = sys.float_info.max if binning_method == "information-gain" else 0
    assert np.equal(i, p.breakpoints[1, :-1]).all()  # imag component is 0 or inf
    _ = p.transform(X, y)


@pytest.mark.parametrize("fourier_transform", ["fft", "dft"])
@pytest.mark.parametrize("norm", [True, False])
def test_dft_mft(fourier_transform, norm):
    # load training data
    X, y = load_gunpoint(split="train", return_X_y=True)
    X_tab = from_nested_to_2d_array(X, return_numpy=True)

    word_length = 6
    alphabet_size = 4

    # Single DFT transformation
    window_size = np.shape(X_tab)[1]

    p = SFA(
        word_length=6,
        alphabet_size=4,
        window_size=window_size,
        norm=norm,
        fourier_transform=fourier_transform,
    ).fit(X, y)

    if fourier_transform == "fft":
        dft = p._fast_fourier_transform(X_tab[0])
    else:
        dft = p._discrete_fourier_transform(X_tab[0], word_length, norm, 1, True)
    mft = p._mft(X_tab[0])

    assert (mft - dft < 0.0001).all()

    # Windowed DFT transformation
    window_size = 140

    p = SFA(
        word_length=word_length,
        alphabet_size=alphabet_size,
        window_size=window_size,
        norm=norm,
        fourier_transform=fourier_transform,
    ).fit(X, y)

    mft = p._mft(X_tab[0])
    for i in range(len(X_tab[0]) - window_size + 1):
        if fourier_transform == "fft":
            dft = p._fast_fourier_transform(X_tab[0, i : window_size + i])
        else:
            dft = p._discrete_fourier_transform(
                X_tab[0, i : window_size + i], word_length, norm, 1, True
            )

        assert (mft[i] - dft < 0.001).all()

    assert len(mft) == len(X_tab[0]) - window_size + 1
    assert len(mft[0]) == word_length


@pytest.mark.parametrize("binning_method", ["equi-depth", "information-gain"])
def test_sfa_anova(binning_method):
    # load training data
    X, y = load_gunpoint(split="train", return_X_y=True)

    word_length = 6
    alphabet_size = 4

    # SFA with ANOVA one-sided test
    window_size = 32
    p = SFA(
        word_length=word_length,
        anova=True,
        alphabet_size=alphabet_size,
        window_size=window_size,
        binning_method=binning_method,
    ).fit(X, y)

    assert p.breakpoints.shape == (word_length, alphabet_size)
    _ = p.transform(X, y)

    # SFA with first feq coefficients
    p2 = SFA(
        word_length=word_length,
        anova=False,
        alphabet_size=alphabet_size,
        window_size=window_size,
        binning_method=binning_method,
    ).fit(X, y)

    assert p.dft_length != p2.dft_length
    assert (p.breakpoints != p2.breakpoints).any()
    _ = p2.transform(X, y)


# test word lengths larger than the window-length
@pytest.mark.parametrize("word_length", [6, 7])
@pytest.mark.parametrize("alphabet_size", [4, 5])
@pytest.mark.parametrize("window_size", [5, 6])
@pytest.mark.parametrize("bigrams", [True, False])
@pytest.mark.parametrize("levels", [1, 2])
@pytest.mark.parametrize("fourier_transform", ["fft", "dft"])
def test_word_lengths(
    word_length, alphabet_size, window_size, bigrams, levels, fourier_transform
):
    # load training data
    X, y = load_gunpoint(split="train", return_X_y=True)

    p = SFA(
        word_length=word_length,
        alphabet_size=alphabet_size,
        window_size=window_size,
        bigrams=bigrams,
        levels=levels,
        fourier_transform=fourier_transform,
    ).fit(X, y)

    assert p.breakpoints is not None
    _ = p.transform(X, y)


def test_typed_dict():
    # load training data
    X, y = load_gunpoint(split="train", return_X_y=True)

    word_length = 6
    alphabet_size = 4

    p = SFA(
        word_length=word_length,
        alphabet_size=alphabet_size,
        levels=2,
        typed_dict=True,
    )
    p.fit(X, y)
    word_list = p.bag_to_string(p.transform(X, y)[0][0])

    word_length = 6
    alphabet_size = 4

    p2 = SFA(
        word_length=word_length,
        alphabet_size=alphabet_size,
        levels=2,
        typed_dict=False,
    )
    p2.fit(X, y)
    word_list2 = p2.bag_to_string(p2.transform(X, y)[0][0])

    assert word_list == word_list2

