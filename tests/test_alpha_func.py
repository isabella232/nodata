import os, re

import pytest
import rasterio as rio
import numpy as np

import nodata.alphamask as alphamask

def image_reader(path):
    with rio.open(path) as src:
        return src.read()

@pytest.fixture
def imagesToTest():
    testdir = 'tests/fixtures/alpha_unit'
    return [os.path.join(testdir, i) for i in os.listdir(testdir) if re.compile('.*.tif').match(i.lower())]

@pytest.fixture
def expectedOutput():
    testdir = 'tests/expected/alpha_simple'
    return [os.path.join(testdir, i) for i in os.listdir(testdir) if re.compile('.*.tif').match(i.lower())]

@pytest.fixture
def functionArgs():
    return [
        (0, 0, 0),
        (0, 0, 0),
        (255, 255, 255),
        (0, 0, 0),
        (255, 255, 255)
        ]

def test_runner(imagesToTest, expectedOutput, functionArgs):
    assert len(imagesToTest) == len(expectedOutput), "Test fixture length %s must equal expected length %s" % (len(imagesToTest), len(expectedOutput))
    assert len(imagesToTest) == len(functionArgs), "Test fixture length %s must equal argument length %s" % (len(imagesToTest), len(expectedOutput))

    pad = 64

    for path, expected, args in zip(imagesToTest, expectedOutput, functionArgs):
        img = image_reader(path)
        depth, rows, cols = img.shape

        expectedImg = image_reader(expected)
        outputImg = np.concatenate([img, alphamask.simple_mask(img, args).reshape((1, rows, cols))])[:, pad: -pad, pad: -pad]

        assert outputImg.shape == expectedImg.shape

        assert np.array_equal(outputImg, expectedImg)


def test_alphamask_good_alphaonly():
    rRows, rCols = np.random.randint(3, 300, 2)
    fauxRGB = np.zeros((3, rRows, rCols), dtype=np.uint8) + 255

    # find a random row / col idx and only apply it to one random band
    rRowIdx = np.random.randint(0, rRows - 1, 1)[0]
    rColIdx = np.random.randint(0, rCols - 1, 1)[0]

    cBandIdx = np.random.randint(0, 3, 1)[0]
    fauxRGB[cBandIdx, rRowIdx, rColIdx] = 0

    outputA = alphamask.simple_mask(fauxRGB, (0, 0, 0))

    assert outputA.shape == (rRows, rCols)

    assert np.all(outputA[-1]), "No mask pixels should equal 0"

    # find a random row / col idx and apply it to all bands
    rRowIdx = np.random.randint(0, rRows - 1, 1)[0]
    rColIdx = np.random.randint(0, rCols - 1, 1)[0]

    fauxRGB[:, rRowIdx, rColIdx] = 0

    outputA = alphamask.simple_mask(fauxRGB, (0, 0, 0))

    assert outputA.shape == (rRows, rCols)

    createRowIdx, createColIdx = np.where(outputA == 0)

    assert len(createRowIdx) == 1
    assert rRowIdx == createRowIdx[0]

    assert len(createColIdx) == 1
    assert rColIdx == createColIdx[0]
