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
        if self.layout.ball_carrier == 0:
            self.pb_eqs=list()
            return
    
        self.pb_eqs=list()
        bc=self.layout.players[self.layout.ball_carrier]
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
        if self.layout.ball_carrier == 0:
            return
        bc=self.layout.players[self.layout.ball_carrier]
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
