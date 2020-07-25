# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import time

from FinTestCases import FinTestCases, globalTestCaseMode

from financepy.finutils.FinDate import FinDate
from financepy.models.FinModelRatesHW import FinModelRatesHW
from financepy.market.curves.FinDiscountCurve import FinDiscountCurve
from financepy.products.bonds.FinBond import FinBond
from financepy.finutils.FinFrequency import FinFrequencyTypes
from financepy.finutils.FinDayCount import FinDayCountTypes
from financepy.finutils.FinGlobalVariables import gDaysInYear
from financepy.finutils.FinHelperFunctions import printTree

testCases = FinTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_HullWhiteExampleOne():
    # HULL BOOK INITIAL EXAMPLE SECTION 28.7 HW EDITION 6

    times = [0.0, 0.5000, 1.00000, 1.50000, 2.00000, 2.500000, 3.00000]
    zeros = [0.03, 0.0343, 0.03824, 0.04183, 0.04512, 0.048512, 0.05086]
    times = np.array(times)
    zeros = np.array(zeros)
    dfs = np.exp(-zeros*times)

    startDate = FinDate(1, 12, 2019)
    endDate = FinDate(1, 12, 2022)
    sigma = 0.01
    a = 0.1
    numTimeSteps = 3
    model = FinModelRatesHW(sigma, a, numTimeSteps)
    treeMat = (endDate - startDate)/gDaysInYear
    model.buildTree(treeMat, times, dfs)
#   printTree(model._Q)
#   print("")
#   printTree(model._rt)
#   print("")

###############################################################################


def test_HullWhiteExampleTwo():
    # HULL BOOK ZERO COUPON BOND EXAMPLE 28.1 SEE TABLE 28.3
    # Replication may not be exact as I am using dates rather than times

    zeroDays = [0, 3, 31, 62, 94, 185, 367, 731, 1096, 1461,
                1826, 2194, 2558, 2922, 3287, 3653]

    zeroRates = [5.0, 5.01772, 4.98282, 4.97234, 4.96157, 4.99058, 5.09389,
                 5.79733, 6.30595, 6.73464, 6.94816, 7.08807, 7.27527,
                 7.30852, 7.39790, 7.49015]

    times = np.array(zeroDays) / 365.0
    zeros = np.array(zeroRates) / 100.0
    dfs = np.exp(-zeros*times)

    startDate = FinDate(1, 12, 2019)
    sigma = 0.01
    a = 0.1
    strike = 63.0
    face = 100.0

    expiryDate = startDate.addTenor("3Y")
    maturityDate = startDate.addTenor("9Y")

    texp = (expiryDate - startDate)/gDaysInYear
    tmat = (maturityDate - startDate)/gDaysInYear

    numTimeSteps = 100
    model = FinModelRatesHW(sigma, a, numTimeSteps)
    vAnal = model.optionOnZCB(texp, tmat, strike, face, times, dfs)

    # Test convergence
    numStepsList = range(100, 500, 10)
    analVector = []
    treeVector = []

    testCases.header("NUMTIMESTEP", "VTREE", "VANAL","PERIOD")
    for numTimeSteps in numStepsList:
        start = time.time()
        model.buildTree(texp, times, dfs)
        vTree = model.optionOnZeroCouponBond_Tree(texp, tmat, strike, face)
        end = time.time()
        period = end-start
        treeVector.append(vTree['put'])
        analVector.append(vAnal['put'])
        testCases.print(numTimeSteps, vTree, vAnal, period)

 #   plt.plot(numStepsList, treeVector)
 #   plt.plot(numStepsList, analVector)

###############################################################################


def test_HullWhiteBondOption():
    # Valuation of a European option on a coupon bearing bond

    settlementDate = FinDate(1, 12, 2019)
    expiryDate = settlementDate.addTenor("18m")
    maturityDate = settlementDate.addTenor("10Y")
    coupon = 0.05
    frequencyType = FinFrequencyTypes.SEMI_ANNUAL
    accrualType = FinDayCountTypes.ACT_ACT_ICMA
    bond = FinBond(maturityDate, coupon, frequencyType, accrualType)

    bond.calculateFlowDates(settlementDate)
    couponTimes = []
    couponFlows = []
    cpn = bond._coupon/bond._frequency
    for flowDate in bond._flowDates[1:]:
        flowTime = (flowDate - settlementDate) / gDaysInYear
        couponTimes.append(flowTime)
        couponFlows.append(cpn)
    couponTimes = np.array(couponTimes)
    couponFlows = np.array(couponFlows)

    strikePrice = 105.0
    face = 100.0

    tmat = (maturityDate - settlementDate) / gDaysInYear
    times = np.linspace(0, 10, 21)
    dates = settlementDate.addYears(times)
    dfs = np.exp(-0.05*times)
    curve = FinDiscountCurve(settlementDate, dates, dfs)

    #price = bond.valueBondUsingDiscountCurve(settlementDate, curve)
    #print("Spot Bond Price:", price)

    #price = bond.valueBondUsingDiscountCurve(expiryDate, curve)
    #print("Fwd Bond Price:", price)

    sigma = 0.01
    a = 0.1

    #  Test convergence
    numStepsList = [100, 200, 300, 400, 500]
    texp = (expiryDate - settlementDate)/gDaysInYear

    testCases.header("NUMSTEPS", "FAST TREE", "FULLTREE", "TIME")

    for numTimeSteps in numStepsList:
        start = time.time()
        model = FinModelRatesHW(sigma, a, numTimeSteps)
        model.buildTree(texp, times, dfs)

        americanExercise = False
        v1 = model.americanBondOption_Tree(texp, strikePrice, face,
                                           couponTimes, couponFlows,
                                           americanExercise)

        v2 = model.europeanBondOption_Tree(texp, strikePrice, face,
                                           couponTimes, couponFlows)

        end = time.time()
        period = end-start

        testCases.print(numTimeSteps, v1, v2, period)

#    plt.plot(numStepsList, treeVector)

    if 1 == 0:
        print("RT")
        printTree(model._rt, 5)
        print("BOND")
        printTree(model._bondValues, 5)
        print("OPTION")
        printTree(model._optionValues, 5)

    v = model.europeanBondOption_Jamshidian(texp, strikePrice, face,
                                            couponTimes, couponFlows,
                                            times, dfs)

###############################################################################


def test_HullWhiteCallableBond():
    # Valuation of a European option on a coupon bearing bond

    settlementDate = FinDate(1, 12, 2019)
    maturityDate = settlementDate.addTenor("10Y")
    coupon = 0.05
    frequencyType = FinFrequencyTypes.SEMI_ANNUAL
    accrualType = FinDayCountTypes.ACT_ACT_ICMA
    bond = FinBond(maturityDate, coupon, frequencyType, accrualType)

    bond.calculateFlowDates(settlementDate)
    couponTimes = []
    couponFlows = []
    cpn = bond._coupon/bond._frequency
    for flowDate in bond._flowDates[1:]:
        flowTime = (flowDate - settlementDate) / gDaysInYear
        couponTimes.append(flowTime)
        couponFlows.append(cpn)
    couponTimes = np.array(couponTimes)
    couponFlows = np.array(couponFlows)

    ###########################################################################
    # Set up the call and put times and prices
    ###########################################################################

    callDates = []
    callPrices = []
    callPx = 120.0
    callDates.append(settlementDate.addTenor("5Y")); callPrices.append(callPx)
    callDates.append(settlementDate.addTenor("6Y")); callPrices.append(callPx)
    callDates.append(settlementDate.addTenor("7Y")); callPrices.append(callPx)
    callDates.append(settlementDate.addTenor("8Y")); callPrices.append(callPx)

    callTimes = []
    for dt in callDates:
        t = (dt - settlementDate) / gDaysInYear
        callTimes.append(t)

    putDates = []
    putPrices = []
    putPx = 98.0
    putDates.append(settlementDate.addTenor("5Y")); putPrices.append(putPx)
    putDates.append(settlementDate.addTenor("6Y")); putPrices.append(putPx)
    putDates.append(settlementDate.addTenor("7Y")); putPrices.append(putPx)
    putDates.append(settlementDate.addTenor("8Y")); putPrices.append(putPx)

    putTimes = []
    for dt in putDates:
        t = (dt - settlementDate) / gDaysInYear
        putTimes.append(t)

    ###########################################################################

    tmat = (maturityDate - settlementDate) / gDaysInYear
    times = np.linspace(0, 10.0, 21)
    dates = settlementDate.addYears(times)
    dfs = np.exp(-0.05*times)
    curve = FinDiscountCurve(settlementDate, dates, dfs)

    ###########################################################################

    v1 = bond.valueBondUsingDiscountCurve(settlementDate, curve)

    sigma = 0.02  # basis point volatility
    a = 0.1

    # Test convergence
    numStepsList = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    tmat = (maturityDate - settlementDate)/gDaysInYear

    testCases.header("NUMSTEPS", "BOND_ONLY", "CALLABLE_BOND", "TIME")

    for numTimeSteps in numStepsList:
        start = time.time()
        model = FinModelRatesHW(sigma, a, numTimeSteps)
        model.buildTree(tmat, times, dfs)

        v2 = model.callablePuttableBond_Tree(couponTimes, couponFlows,
                                             callTimes, callPrices,
                                             putTimes, putPrices, 100.0)

        end = time.time()
        period = end-start
        testCases.print(numTimeSteps, v1, v2, period)

    if 1 == 0:
        print("RT")
        printTree(model._rt, 5)
        print("BOND")
        printTree(model._bondValues, 5)
        print("OPTION")
        printTree(model._optionValues, 5)

###############################################################################


test_HullWhiteExampleOne()
test_HullWhiteExampleTwo()
test_HullWhiteBondOption()
test_HullWhiteCallableBond()
testCases.compareTestCases()