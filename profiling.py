import sandbox
import cProfile
import pstats

cProfile.run('sandbox.runit(display=False)','profstats')
p = pstats.Stats('profstats')
p.sort_stats('cumulative').print_stats(20)
