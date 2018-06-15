import os

import Corpus.feeder as fee
import Corpus.residential as res

strobeDir = os.path.dirname(os.path.realpath(__file__))
os.chdir(strobeDir + '\\Corpus\\')

os.chdir(strobeDir + "\\Data\\")

family = res.Household("Example family")
family.parameterize()
family.simulate()

fee.IDEAS_Feeder('Example', 5, strobeDir)
