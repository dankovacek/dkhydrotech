import cProfile
import re
import os 
import sys

import cProfile
import pstats
import io

path = os.path.abspath(os.path.dirname(__file__))
if not path in sys.path:
    sys.path.append(path)


# pr = cProfile.Profile()
# pr.enable()

# my_result = main()

# pr.disable()
# s = io.StringIO()
# ps = pstats.Stats(pr, stream=s).sort_stats('tottime')



p = pstats.Stats('profile_output').sort_stats('tottime')
p.strip_dirs().sort_stats('tottime').print_stats(.01)

