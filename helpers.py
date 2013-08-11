"""
Helper objects that get updated periodically.
"""
import numpy as np
import matplotlib.pyplot as plt

class Helper(object):
    """
    Helper base class.
    """
    def __init__(self,layout):
        self.update_freq=1
        self.layout=layout

    def update(self):
        pass

class BallCarrierPBeqs(Helper):
    """
    Computes equations for perpendicular bisectors of ball carrier and opponents.

    These equations are used by ball runners and defenders to decide where to go.
    """
    def __init__(self,layout):
        Helper.__init__(self,layout)
        
    def update(self):
        """
        Find equations of the p.b. of all goalward opponents
        """
        if self.layout.ball.carrier == 0:
            self.pb_eqs=list()
            return
    
        self.pb_eqs=list()
        bc=self.layout.players[self.layout.ball.carrier]
        for p in self.layout.players.values():
            if bc.team != p.team:
                if bc.dist_to_goal() > p.dist_to_their_goal():
                    # Maths!
                    Px,Py = (bc.x+p.x)/2. , (bc.y+p.y)/2.
                    if bc.y == p.y:
                        # m would be infinite, describe eq differently
                        # and denote by eq[3]=-1
                        self.pb_eqs.append((p.pid,Px,0,-1))
                    else:
                        m=-1./( (bc.y-p.y)/(bc.x-p.x))
                        #if p.x > self.x : m *= -1
                        b = Py - m*Px
                        self.pb_eqs.append((p.pid,m,b,0))
        # Now find projected 'strike point' of BC with opponents
        # TODO

class Maps(Helper):

    def __init__(self,layout):
        Helper.__init__(self,layout)    

        # Good positions are a trade off between the following:
        # * Distance to ball carrier (length of pass)
        # * Distance to end zone
        # * Distance to defenders (consider their motion?)
        # * Distance to other recievers (don't crowd the gaps)
        #
        # There are many different kernels (gaussian, parabola,...) that could be used for
        # these as well as tuneable parameters to those kernels. Implement something then
        # worry later about fine tuning the details.

    def update(self):

        if self.layout.ball.carrier == 0:
            return

        self.bc=self.layout.players[self.layout.ball.carrier]

        # make list of defenders
        self.defenders=list()
        for p in self.layout.players.values():
            if p.team != self.bc.team:
                self.defenders.append(p)

        # make list of recievers
        # For now, all bc friends are receivers.
        self.receivers=list()
        for p in self.layout.players.values():
            if p.team == self.bc.team:
                self.receivers.append(p)        
        
    # Here are some kernels.
    # parabolic with weight for now
    # Ensure the sign is such that "small is good spot for receiver to be"
    # in other words can interpret as a "hazard map for receiver"
    def end_zone_kern(self,p,x,y,w=1):
        return w*p.dist_to_goal(x=x)**2

    def pass_dist_kern(self,x,y,w=1):
        dsq=(self.bc.x-x)**2 + (self.bc.y-y)**2
        return w*dsq
    
    def def_dist_kern(self,thisPlayer,x,y,w=1):
        " Uses minimimum distance only, no weighting for number of defenders "
        # Find all the distances
        dlist=list()
        for p in self.defenders:
            if p.pid == thisPlayer.pid:
                continue
            dlist.append(np.sqrt((x-p.x)**2 + (y-p.y)**2))
        return -min(dlist)

    def rec_dist_kern(self,thisPlayer,x,y,w=1):
        # Find all the distances
        rlist=list()
        for p in self.receivers:
            if p.pid == thisPlayer.pid:
                continue
            rlist.append(np.sqrt((x-p.x)**2 + (y-p.y)**2))
        return -min(rlist)

    # Pull all the kernels together including a weight vector
    def rec_hazard_relative(self,xy,p,w=(0.01,0.0001,1,1)):
        """
        Hazard function for recievers when determining where to move.
        """
        x=xy[0]
        y=xy[1]
        return self.end_zone_kern(p,x,y,w[0]) + self.pass_dist_kern(x,y,w[1]) + self.def_dist_kern(p,x,y,w[2]) +\
            self.rec_dist_kern(p,x,y,w[3])

    def rec_hazard_absolute(self,xy,p,w=(0.01,0.02,1)):
        """
        Hazard function for recievers for comparing different players.
        """
        x=xy[0]
        y=xy[1]
        return self.end_zone_kern(p,x,y,w[0]) + self.pass_dist_kern(x,y,w[1]) + self.def_dist_kern(p,x,y,w[2])
    
    def throw_hazard_absolute(self,xy,p,w=(0.01,1)):
        """
        Hazard function for throwers to compare their location to rxs.
        """
        x=xy[0]
        y=xy[1]
        return self.end_zone_kern(p,x,y,w[0]) + self.def_dist_kern(p,x,y,w[1])


# This is the early, experimental and slow(!) approach.
class HazardMaps(Helper):
    """
    Computes are stores hazard maps for use by catchers and possibly also
    runners, defenders and throwers to determine what parts of the pitch
    are open for attack.

    Note that it is too inefficient to use these in practice, these are just
    for debugging/development and may differ from real player implementations.
    """
    # Set class default grid spacing
    nx=100
    ny=50
    def __init__(self,layout):
        Helper.__init__(self,layout)
        # 
    def update(self):
        # Ultimately, computing and stroing on a grid may not be the best solution,
        # continous functions that can be minimised may be better. For now, maps
        # make visualisation for debugging easy.
        self.maps=dict()
        if self.layout.ball.carrier == 0:
            return
        bc=self.layout.players[self.layout.ball.carrier]
        self.maps['EZ_dist'] = self.EZ_dist_compute(bc)
        self.maps['pass_dist'] = self.pass_dist_compute(bc)
        self.maps['def_dist'] = self.def_dist_compute(bc)
        best=self.maps['EZ_dist']**2+0.5*self.maps['pass_dist']**2 - self.maps['def_dist']**2
        plt.contour(range(self.nx),range(self.ny),best.transpose(),50)
        for p in self.layout.players.values():
            plt.plot(p.x,p.y,'bo')
        plt.show()

    def EZ_dist_compute(self,bc):
        " Distance to end zone map "
        dx=float(self.layout.xsize)/self.nx
        dy=float(self.layout.ysize)/self.ny
        dmap=np.empty((self.nx,self.ny))
        for ix in range(self.nx):
            x=ix*dx
            for iy in range(self.ny):
                y=iy*dy
                dmap[ix,iy] = bc.dist_to_goal(x=x)
        return dmap
    
    def pass_dist_compute(self,bc):
        " Distance of a potential pass "
        dx=float(self.layout.xsize)/self.nx
        dy=float(self.layout.ysize)/self.ny
        dmap=np.empty((self.nx,self.ny))
        for ix in range(self.nx):
            x=ix*dx
            for iy in range(self.ny):
                y=iy*dy
                dmap[ix,iy] = np.sqrt((bc.x-x)**2 + (bc.y-y)**2)
        return dmap

    def def_dist_compute(self,bc):
        " Distance to nearest defender "
        dx=float(self.layout.xsize)/self.nx
        dy=float(self.layout.ysize)/self.ny
        dmap=np.empty((self.nx,self.ny))
        # make list of defenders
        defenders=list()
        for p in self.layout.players.values():
            if p.team != bc.team:
                defenders.append(p)
                #print(p.x,p.y)
        for ix in range(self.nx):
            x=ix*dx
            for iy in range(self.ny):
                y=iy*dy
                # Find all the distances
                dlist=list()
                for p in defenders:
                    dlist.append(np.sqrt((x-p.x)**2 + (y-p.y)**2))
                dmap[ix,iy] = min(dlist)
        return dmap    
