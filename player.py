import numpy as np
import math
import utils
import scipy.optimize as opt
from const import *
import matplotlib.pyplot as plt
import pylab
import pdb

class Player(object):
    """
    Player object

    Parameters
    ----------
    team : 1 or -1. Can be interpreted as team=1 -> scores to the right
    
    Units:
    
    """
    def __init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team,angle_of_motion=0):
        self.layout=layout
        self.size=size
        self.pid=0 # Actual PIDs get set when player is registered to a layout.
        self.x=float(x)
        self.y=float(y)
        self.top_speed=top_speed
        self.acc=acc
        self.strength=strength
        self.throw_power=throw_power
        self.jersey=jersey
        self.team=team
        self.angle=angle_of_motion
        # Drag model?
        self.cdrag = self.acc/self.top_speed**2
        #
        self.current_speed=0.
        self.x_objective=0.
        self.y_objective=0.
        ### Define how to resolve collisions between opposing team players
        # A player not wanting to block will instead try to evade, for instance
        # to get around a blocker to make a tackle, or get clear to make a lead
        # for a pass.
        self.want_to_block=True
        # Setup behaviours
        self.set_ai_config()
        # Set to standing
        self.state=1
        # Allocate prone counter
        self.prone=-1

    def set_ai_config(self):
        " Defines postional play."
        pass

    # Define Objective functions.
    # These are provided here as a resource for child classes.
    # Objective methods set where you are trying to go, move tries to get you
    # there within the constraints of your motion (i.e. turning rate, speed,...)
    def objective(self):
        pass

    def objective_sanity(self):
        """
        To be called after objective setting to ensure sensible.
        """
        sideline_buffer=1.
        endzone_buffer=-1.
        self.x_objective = max(self.x_objective,endzone_buffer)
        self.x_objective = min(self.x_objective,self.layout.xsize-endzone_buffer)
        self.y_objective = max(self.y_objective,sideline_buffer)  
        self.y_objective = min(self.y_objective,self.layout.ysize-sideline_buffer)

    def set_objective(self,blah):
        self.objective=blah

    def get_loose_ball(self):
        """
        Set objective to ball location
        """
        self.x_objective = self.layout.ball.x
        self.y_objective = self.layout.ball.y

    def run_to_goal(self):
        """
        Run towards offensive end zone, avoiding opponents.
        """
        # This could be replaced by angle to end zone corner?
        max_angle_to_run = 80.
        angle_step=5

        # Set defaults in case there are no obstacles in our path.
        # NOTE: This is sub-optimal in the case that any defenders behind
        # us can run faster than us.
        best_y = self.y
        if self.team == 1:
            best_x = self.layout.xsize
        else:
            best_x = 0

        ang_start = np.floor(-max_angle_to_run)
        ang_end = np.ceil(max_angle_to_run)
        if self.team == -1:
            ang_start += 180
            ang_end += 180      
        
        def distAlongAngle(ang,obj,full_return=False):
            " Finds shortest dist along this angle"
            # find eq of line from me at angle
            m=math.tan(ang*deg2rad)
            b=obj.y - m*obj.x
            # Find shortest intersection distance
            shortest_dist=-1
            for eq in pb_eqs:
                if eq[2] == -1:
                    # Case where y co-ords are equal.
                    dist=abs(obj.x-eq[1])
                    yi=obj.y
                    xi=eq[1]
                else:
                    # Find co-ords of intersection point
                    xi=(b-eq[2])/(eq[1]-m)
                    yi=m*xi+b
                    # Checks for intersection being out of bounds
                    if (yi > obj.layout.ysize):
                        # Pull back intersection point to OOB position
                        yi = obj.layout.ysize
                        xi = (yi-b)/m
                    elif (yi < 0):
                        yi = 0
                        xi = (yi-b)/m
                    # Ensure intersection points are in the field
                    xi = utils.bracket(0,xi,obj.layout.xsize)
                    #dist=np.sqrt( (x-xi)**2 + (y-yi)**2)
                    dist=xi-obj.x
                if dist < shortest_dist or shortest_dist < 0.:
                    shortest_dist=dist
                    xs=xi
                    ys=yi
            if full_return:
                return (shortest_dist,xs,ys)
            return -shortest_dist

        pb_eqs = self.layout.helpers['pb_eqs'].pb_eqs
        if len(pb_eqs) != 0: 
            best_angle = opt.fminbound(distAlongAngle,ang_start,ang_end,args=(self,))
            dist, best_x, best_y = distAlongAngle(best_angle,self,full_return=True)

        self.x_objective = best_x
        self.y_objective = best_y
        # Ensure we don't try to run out
        buff=self.size*2.
        self.x_objective = min(self.x_objective,self.layout.xsize-buff)
        self.x_objective = max(self.x_objective,buff)
        self.y_objective = min(self.y_objective,self.layout.ysize-buff)
        self.y_objective = max(self.y_objective,buff)

    def tackle_ball_carrier(self):
        """
        Run to ball carrier and try to tackle.
        """
        dill=self.layout.players[self.layout.ball.carrier]

        if self.dist_to_other(dill) < self.size*1.5:
            self.x_objective = dill.x
            self.y_objective = dill.y
        else:
            # Run to point D in front of ball carrier, where D is the distance
            # between self and the carrier.
            self.x_objective = dill.x + self.dist_to_other(dill)*(-self.team)*0.9
            self.y_objective = dill.y
        self.want_to_block=False

    def go_psycho(self):
        """
        Simply attack nearest standing opponent.
        """
        min_dist=self.layout.xsize*2.
        got_opp=False
        for p in self.layout.players.values():
            if p.team == self.team:
                continue
            elif p.state == 0:
                continue
            else:
                dist=np.sqrt( (p.x - self.x)**2 + (p.y - self.y)**2)
                if dist < min_dist:
                    got_opp=True
                    opp=p
        if got_opp:
            self.x_objective=opp.x
            self.y_objective=opp.y
        else:
            # If no standing opponents, may as well grab the ball
            self.x_objective=self.layout.ball.x
            self.y_objective=self.layout.ball.y

    def protect_ball_carrier(self):
        """
        Get between ball carrier and opponents.
        NOT FINISHED (hardly started)
        """
        carrier=self.layout.players[self.layout.ball.carrier]
        
        # Who to block? We could try and block nearest baddy to us, but they might not be
        # a threat to the carrier. We could try to block the one nearest the carrier, but
        # there might be one closer to us we could better block??

    def find_space(self):
        """
        Get in a good position for recieving a pass
        """        
        # Minimise to find best spot to head towards
        bc=self.layout.players[self.layout.ball.carrier]

        # Try starting from 3 places:
        # * Your position
        # * bc positiong
        # * goal end zone at your y
        # 
        # This help avoids getting trapped in local minima, ensuring we check for good short and
        # long pass options as well as options near to us.

        # Wrapper to hazard function
        def haz_wrap(xy):
            return self.layout.helpers['maps'].hazard(xy,self)

        res_bc = opt.fmin(haz_wrap, np.array( (bc.x,bc.y) ), disp=False, full_output=True)
        #self.layout.helpers['maps'].hazard(res_bc[0],self,debug=True)
        best_func = res_bc[1]
        best_xy = res_bc[0]
        
        res_self = opt.fmin(haz_wrap, np.array( (self.x,self.y) ),disp=False, full_output=True)
        #self.layout.helpers['maps'].hazard(res_self[0],self,debug=True)
        if res_self[1] < best_func:
            best_func = res_self[1]
            best_xy = res_self[0]
        
        if self.team == 1:
            ez_x = self.layout.xsize
        else:
            ez_x = 0
        res_ez = opt.fmin(haz_wrap, np.array( (ez_x,self.y) ),disp=False, full_output=True)
        #self.layout.helpers['maps'].hazard(res_ez[0],self,debug=True)
        if res_ez[1] < best_func:
            best_func = res_ez[1]
            best_xy = res_ez[0]

        self.x_objective = best_xy[0]
        self.y_objective = best_xy[1]
    
    def run_or_pass(self):
        """
        Throw a pass if you think someone is in a better position. Otherwise run yourself.

        TODO: Should require the rx be more than just a bit better since passes are risky.
        """

        my_hazard = self.layout.helpers['maps'].hazard((self.x,self.y),self)

        rec_hazard=list()
        for p in self.layout.helpers['maps'].receivers:
            rec_hazard.append(self.layout.helpers['maps'].hazard((p.x,p.y),p))

        imin_rec = np.argmin(rec_hazard)
        
        if my_hazard < rec_hazard[imin_rec]:
            # I'm in a better position, so I'll run it home
            self.run_to_goal()
        else:
            # Pass to the rx in a better position
            self.throw_pass(self.layout.helpers['maps'].receivers[imin_rec])
        
    def throw_pass(self,rx):
        """
        Throw the ball to the specified receiver.

        TODO: Very simplistic to throw to rx position. Instead this routine should evaluate
        the time the pass might take and project rx position. For any given target location, there
        is a locus in (angle,power) that will get us there, so this needs to be considered as well.
        Also need to introduce a skill dependant accuracy and judgement.
        
        Parameters
        ----------
        rx : The reciever (object)
        """
        # Just throw to rx position
        self.layout.ball.launch(0.,self.throw_power,rx.x,rx.y)
        
    def move(self):
        """
        Move method for each tick update.
        """
        # We are ignoring \delta_t by calling it unity, so V and A need to be in appropriate
        # units to reflect that.

        # Don't move if we are prone
        if self.state == 0:
            return

        # Don't move if we are at objective
        # NOTE: WHAT ABOUT SPEED?
        if np.sqrt((self.y_objective-self.y)**2 + (self.x_objective-self.x)**2) == 0.:
            return

        # Use Brent method to find best angle to accelerate at to reach objective.
        pi = 4.*math.atan(1.)
        # Bracket angle to be at least in hemisphere of objective
        try:
            obj_angle = np.tan((self.y_objective-self.y)/(self.x_objective-self.x))
            if not np.isfinite(obj_angle):
                print("non finite",self.y_objective,self.y,self.x_objective,self.x)
            if self.x_objective-self.x < 0:
                obj_angle += pi
        except:
            # div by zero?
            print("exc in move",self.y_objective,self.y,self.x_objective,self.x)
            obj_angle = 0.
        try:
            best_acc = opt.brent(lambda angle : self.eval_move(angle), brack=(-pi,pi))
        except:
            best_acc = obj_angle
        acc_angle = best_acc

        self.x, self.y, self.angle, self.current_speed = self.project_move(acc_angle)
 
        # Check if we can make it to objective
        #if np.sqrt((self.x_objective-self.x)**2 + (self.y_objective-self.y)**2) < self.speed:
        #    self.x = self.x_objective
        #    self.y = self.y_objective
        #else:
        #    if self.y_objective == self.y:
        #        if self.x_objective > self.x:
        #            self.x += self.speed
        #        else:
        #            self.x -= self.speed
        #    else:
        #        self.angle = math.atan2(self.y_objective-self.y,self.x_objective-self.x)
        #        self.x += self.speed * math.cos(self.angle)
        #        self.y += self.speed * math.sin(self.angle)
        # Ensure players stay in bounds
        self.x = min(self.x,self.layout.xsize)
        self.x = max(self.x,0)
        self.y = min(self.y,self.layout.ysize)
        self.y = max(self.y,0)

    def eval_move(self,acc_angle):
        """
        Utility function for acc angle optimisation.
        Returns distance between projected position given the angle and the objective.
        """
        x,y,a,b=self.project_move(acc_angle)
        return np.sqrt( (x-self.x_objective)**2 + (y-self.y_objective)**2)


    def project_move(self,acc_angle):
        """
        Projects player one tick by applying max acceleration at the given angle.
        
        Returns
        -------
        Tuple of the projected phase (x,y, angle, speed) 
        """
        vx, vy = utils.components(self.current_speed,self.angle)
        ax, ay =  utils.components(self.acc*self.layout.dt,acc_angle)
        vx_new, vy_new = (vx + ax,vy + ay)

        angle_new = math.atan2(vy_new,vx_new)
        speed_new = min(np.sqrt( vx_new**2 + vy_new**2),self.top_speed)
        
        # Speed limited components
        vx_new, vy_new = utils.components(speed_new,angle_new)

        return  (self.x + vx_new, self.y + vy_new, angle_new, speed_new)

    def unproject_move(self,acc_angle):
        """
        Reverses the effect of a projection at the specified angle.
        
        Returns
        -------
        Tuple of the projected phase (x,y, angle, speed) 
        """
        hpi = 2*math.atan(1.)
        vx, vy = utils.components(self.current_speed,self.angle+hpi)
        ax, ay =  utils.components(self.acc*self.layout.dt,acc_angle+hpi)
        vx_new, vy_new = (vx + ax,vy + ay)

        angle_new = math.atan2(vy_new,vx_new)
        speed_new = min(np.sqrt( vx_new**2 + vy_new**2),self.top_speed)
        
        # Speed limited components
        vx_new, vy_new = utils.components(speed_new,angle_new)

        return  (self.x + vx_new, self.y + vy_new, angle_new, speed_new)
    
    def move_at_angle(self,angle,amount):
        """
        Utililty method used by some collision resolutions. Just geometry.
        """
        self.x += amount * math.cos(angle)
        self.y += amount * math.sin(angle)
    
    def dist_to_goal(self,x=None):
        """
        Returns shortest distance to offensive end zone.
        """
        if x == None:
            xuse = self.x
        else:
            xuse = x     
        if self.team == 1:
            return self.layout.xsize - xuse
        else:
            return xuse

    def dist_to_their_goal(self):
        """
        Returns shortest distance to deffensive end zone.
        """
        if self.team == -1:
            return self.layout.xsize - self.x
        else:
            return self.x

    def dist_to_other(self,other):
        """
        Returns distance between self and other
        """
        return np.sqrt( (self.x-other.x)**2 + (self.y-other.y)**2)
    
    def has_ball(self):
        """
        Boolean of whether this player is carrying the ball.
        """
        if self.pid == self.layout.ball.carrier:
            return True
        else:
            return False
    
    def standup(self):
        """
        Check if player is prone and if so whether they can stand yet.
        """
        if self.state==0:
            if self.prone_counter <= 0:
                self.prone_counter = -1
                self.state=1
            else:
                self.prone_counter -= 1
            
