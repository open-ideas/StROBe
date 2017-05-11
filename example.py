import os
import pandas as pd
strobeDir = os.path.dirname(os.path.realpath(__file__))
os.chdir(strobeDir + '\\Corpus\\')

import residential
import feeder
import ast
os.chdir(strobeDir+ "\\Data\\")

family = residential.Household("Example family")
family.parameterize()
family.simulate()

feeder.IDEAS_Feeder('Example',5,strobeDir)