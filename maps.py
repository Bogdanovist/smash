import numpy as np
import math
import utils
import scipy.optimize as opt
from const import *
import player

        bc=self.layout.players[self.layout.ball_carrier]

        # make list of defenders
        defenders=list()
        for p in self.layout.players.values():
            if p.team != bc.team:
                defenders.append(p)

        # make list of recievers
        # For now, all friends are receivers.
        receivers=list()
        for p in self.layout.players.values():
            if p.team == bc.team:
                receivers.append(p)        
        
        # Here are some kernels.
        # parabolic with weight for now
        # Ensure the sign is such that "small is good spot to be"
        # in other words can interpret as a "hazard map"
        def end_zone_kern(x,y,w=1):#,d=False):
            #if d:
            #    return -2*w*bc.dist_to_goal(x=x)*bc.team , 0
            #else:
            return w*bc.dist_to_goal(x=x)**2

        def pass_dist_kern(x,y,w=1):
            dsq=(bc.x-x)**2 + (bc.y-y)**2
            return w*dsq
        
        def def_dist_kern(x,y,w=1):
            # Find all the distances
            dlist=list()
            for p in defenders:
                dlist.append(np.sqrt((x-p.x)**2 + (y-p.y)**2))
            return -min(dlist)

        def rec_dist_kern(x,y,w=1):
            # Find all the distances
            rlist=list()
            for p in receivers:
                rlist.append(np.sqrt((x-p.x)**2 + (y-p.y)**2))
            return -min(rlist)

        # Pull all the kernels together including a weight vector
        def rec_hazard(xy,w=(1,1,1,1)):
            x=xy[0]
            y=xy[1]
            return end_zone_kern(x,y,w[0]) + pass_dist_kern(x,y,w[1]) + def_dist_kern(x,y,w[2]) +\
                rec_dist_kern(x,y,w[3])
        
        # Minimise to find best spot to head towards
        best_xy = opt.fmin(rec_hazard, np.array( (bc.x,bc.y) ), disp=False)
        self.x_objective = best_xy[0]
        self.y_objective = best_xy[1]

    
