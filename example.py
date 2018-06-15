import os

import Corpus.feeder as fee
import Corpus.residential as res

strobeDir = os.path.dirname(os.path.realpath(__file__))
cleanup = True

os.chdir(strobeDir + '\\Corpus\\')

os.chdir(strobeDir + "\\Data\\")

# Test Household.parametrize() and .simulate()
family = res.Household("Example family")
family.parameterize()
family.simulate()

# Test feeder
fee.IDEAS_Feeder('Example', 5, strobeDir)

# cleanup
if cleanup:
    for file in os.listdir(strobeDir):
        print file
        if file.endswith(('.p', '.txt')):
            os.remove(os.path.join(strobeDir, file))
