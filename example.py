import os

import Corpus.feeder as feeder
import Corpus.residential as res

strobeDir = os.path.dirname(os.path.realpath(__file__)) # get path where this file is (StROBe path)
os.chdir(strobeDir + '\\Corpus\\') #make Corpus the current directory

# Create and simulate a single household, with given type of members, and given year
family = res.Household("Example household", members=['FTE', 'Unemployed'])
family.simulate(year=2013, ndays=365)

family.__dict__ # list all elements of family for inspection


# Simulate households for an entire feeder
# create folder where simulations will be stored for feeder
dataDir = os.path.join(strobeDir,"Simulations")
if not os.path.exists(dataDir):
    os.mkdir(dataDir)
    
# Test feeder with 5 households, temperatures given in Kelvin, and do not save individual household result files
fee=feeder.IDEAS_Feeder(name='Neighborhood',nBui=5, path=dataDir, sh_K=True, save_indiv=False)
fee.simulate()
fee.output()

fee.__dict__ # list all elements of fee for inspection
