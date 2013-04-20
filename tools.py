import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pylab
import numpy as np

class Player(object):
    """
    Player object

    Parameters
    ----------
    team : 1 or -1. Can be interpreted as team=1 -> scores to the right
    """
    def __init__(self,layout,size,x,y,top_speed,acc,jersey,team,angle_of_motion=0):
        self.layout=layout
        self.size=size
        self.pid=0 # Actual PIDs get set when player is registered to a layout.
        self.x=float(x)
        self.y=float(y)
        self.top_speed=top_speed
        self.acc=acc
        self.jersey=jersey
        self.team=team
        self.angle=angle_of_motion
        # A generic tackling/blocking ability placeholder
        self.strength=1
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

    def set_ai_config(self):
        " Defines postional play."
        pass

    # Define Objective functions.
    # These are provided here as a resource for child classes.
    # Objective methods set where you are trying to go, move tries to get you
    # there within the constraints of your motion (i.e. turning rate, speed,...)
    def objective(self):
        pass

    def set_objective(self,blah):
        self.objective=blah

    def get_loose_ball(self):
        """
        Set objective to ball location
        """
        self.x_objective = self.layout.xball
        self.y_objective = self.layout.yball

    def run_to_goal(self):
        """
        Run towards offensive end zone, avoiding opponents.
        """
        # This could be replaced by angle to end zone corner?
        max_angle_to_run = 45.
        angle_step=5
        pi=4.*math.atan(1.)
        deg2rad=pi/180.

        # Set defaults in case there are no obstacles in our path.
        # NOTE: This is sub-optimal in the case that any defenders behind
        # us can run faster than us.

        best_y = self.y
        if self.team == 1:
            best_x = self.layout.xsize
        else:
            best_x = 0

        # Find equations of the p.b. of all goalward opponents
        pb_eqs=list()
        for p in self.layout.players.values():
            if self.team != p.team:
                if self.dist_to_goal() > p.dist_to_their_goal():
                    # Maths!
                    Px,Py = (self.x+p.x)/2. , (self.y+p.y)/2.
                    if self.y == p.y:
                        # m would be infinite, describe eq differently
                        # and denote by eq[3]=-1
                        pb_eqs.append((p.pid,Px,0,-1))
                    else:
                        m=-1./( (self.y-p.y)/(self.x-p.x))
                        #if p.x > self.x : m *= -1
                        b = Py - m*Px
                        pb_eqs.append((p.pid,m,b,0))
        #for e in pb_eqs: print("eqs",e)
        ang_start = np.floor(-max_angle_to_run)
        ang_end = np.ceil(max_angle_to_run)
        if self.team == -1:
            ang_start += 180
            ang_end += 180
        greatest_gain=0.
        for ang in np.arange(ang_start,ang_end,angle_step):
            # find eq of line from me at angle
            m=math.tan(ang*deg2rad)
            b=self.y - m*self.x
            # Find shortest intersection distance
            shortest_dist=-1
            for eq in pb_eqs:
                if eq[2] == -1:
                    dist=abs(self.x-eq[1])
                else:
                    xi=(b-eq[2])/(eq[1]-m)
                    yi=m*xi+b
                    dist=np.sqrt( (self.x-xi)**2 + (self.y-yi)**2)
               # print("test ",ang,m,b,dist,np.floor(xi),np.floor(yi))
                if dist < shortest_dist or shortest_dist < 0.:
                    shortest_dist=dist
                    shortest_x=xi
                    shortest_y=yi
           # print("check",shortest_dist,greatest_gain,pb_eqs)
            if shortest_dist > greatest_gain:
                greatest_gain = shortest_dist
                best_x=shortest_x
                best_y=shortest_y
               # print("gain",best_x,best_y,shortest_dist,greatest_gain)
        #print("clever",greatest_gain,best_x,best_y)
        self.x_objective = best_x
        self.y_objective = best_y

    def tackle_ball_carrier(self):
        """
        Run to ball carrier and try to tackle.
        """
        dill=self.layout.players[self.layout.ball_carrier]

        if self.dist_to_other(dill) < self.size*1.5:
            self.x_objective = dill.x
            self.y_objective = dill.y
        else:
            # Run to point D in front of ball carrier, where D is the distance
            # between self and the carrier.
            self.x_objective = dill.x + self.dist_to_other(dill)*(-self.team)
            self.y_objective = dill.y
        self.want_to_block=False

    def protect_ball_carrier(self):
        """
        Get between ball carrier and opponents.
        """
        carrier=self.layout.players[self.layout.ball_carrier]
        
        # Who to block? We could try and block nearest baddy to us, but they might not be
        # a threat to the carrier. We could try to block the one nearest the carrier, but
        # there might be one closer to us we could better block.

    def move(self):
        """
        Move method for each tick update.
        """
        # This uses some geometry from the notebook that I am not yet
        # convinced about...
        # We are ignoring \delta_t by calling it unity, so V and A need to be in appropriate
        # units to reflect that.

        pi=4.*math.atan(1.)
        vx=self.current_speed*math.cos(self.angle)
        vy=self.current_speed*math.sin(self.angle)
        acc_angle=math.atan2(self.y + vy - self.y_objective,self.x + vx - self.x_objective)
        # ???
        acc_angle += pi

        # Update velocity, ensuring we stay below speed limit
        vx_new = vx + self.acc*math.cos(acc_angle)
        vy_new = vy + self.acc*math.sin(acc_angle)
        self.angle = math.atan2(vy_new,vx_new)
        self.current_speed = min(np.sqrt( vx_new**2 + vy_new**2),self.top_speed)
        
        # Update position
        self.x += vx_new
        self.y += vy_new
        
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

    def move_at_angle(self,angle,amount):
        """
        Utililty method used by some collision resolutions. Just geometry.
        """
        self.x += amount * math.cos(angle)
        self.y += amount * math.sin(angle)
    
    def dist_to_goal(self):
        """
        Returns shortest distance to offensive end zone.
        """
        if self.team == 1:
            return self.layout.xsize - self.x
        else:
            return self.x

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
        if self.pid == self.layout.ball_carrier:
            return True
        else:
            return False

class move_data(object):
    " Struct for storing moves "
    def __init__(self,pid,x,y,angle,have_ball):
        self.pid=pid
        self.x=x
        self.y=y
        self.angle=angle
        self.have_ball=have_ball
        
class player_data(object):
    " Struct for storing player meta data for transfer."
    def __init__(self,jersey,team,position):
        self.jersey=jersey
        self.team=team
        self.position=position

class Layout(object):
    """
    Base(?) class for the backdrop in which stuff happens.
    """
    def __init__(self,xsize,ysize,nsteps):
        self.xsize=float(xsize)
        self.ysize=float(ysize)
        self.xball=self.xsize/2
        self.yball=self.ysize/2
        self.players=dict()
        self.collisions=list()
        self.nsteps=nsteps
        # 0 for no-one, PID for any other.
        self.ball_carrier=0
        # Save all moves
        self.moves=list()
        # Store step number
        self.istep=0
        # Store list of all triggers in use here, in order to loop over in one place.
        self.triggers = list()

    def add_player(self,player):
        """
        Register player to layout and instantiate AI methods.
        """
        player.pid = len(self.players)+1
        self.players[player.pid]=player
        for ai in player.ai_config:
            # Is this trigger already used?
            indx = np.where([ trig.__class__ == ai[0] for trig in self.triggers])
            if len(indx) == 0:
                self.triggers[indx].add_callback(ai[1])
            else:
                self.triggers.append(ai[0](self))
                self.triggers[len(self.triggers)-1].add_callback(ai[1])

    def frame_data(self):
        nticks=len(self.moves)
        iframe=0
        while iframe < nticks:
            moves=self.moves[iframe]
            x=list()
            y=list()
            t=list()
            for elem in moves:
                x.append(elem.x)
                y.append(elem.y)
                t.append(self.player_header[elem.pid].team)
            iframe = iframe + 1
            yield x,y,t

    def frame_display(self,frame_data):
        x,y,t = frame_data[0], frame_data[1], frame_data[2]
        hx = list()
        hy = list()
        ax = list()
        ay = list()
        bx = list()
        by = list()
        for z in zip(x,y,t):
            if z[2] == 1:
                hx.append(z[0])
                hy.append(z[1])
            elif z[2] == -1:
                ax.append(z[0])
                ay.append(z[1])
            else:
                bx.append(z[0])
                by.append(z[1])
        self.home_team_plot.set_data(hx,hy)
        self.away_team_plot.set_data(ax,ay)
        self.ball_plot.set_data(bx,by)
        #return self.home_team_plot,self.away_team_plot,self.ball_plot

    def run_game(self):
        " Run the game "
        # Setup move storage
        self.player_header=dict()
        for p in self.players.values():
            self.player_header[p.pid]=player_data(p.jersey,p.team,'null')
        # Add ball to player_header
        self.player_header[0]=player_data(0,0,'null')
        # Add inits here? I.e. special player method to set initial objectives?
        for trig in self.triggers:
            trig.init()
        for i in range(self.nsteps):
            self.tick()
        # Display results
        fig1=plt.figure()
        plt.xlim([0,self.xsize])
        plt.ylim([0,self.ysize])
        
        self.home_team_plot, = plt.plot([], [], 'ro',markersize=15)
        self.away_team_plot, = plt.plot([], [], 'bo',markersize=15)
        self.ball_plot, = plt.plot([],[],'go')
        #self.circle1 = pylab.Circle((0,0), radius=5, alpha=.5)
        #axes.add_patch(circle1)
        line_ani = animation.FuncAnimation(fig1,self.frame_display,self.frame_data,interval=9,blit=False,repeat=True)
        plt.show()

    def tick(self):
        """
        Iterate one tick.
        """
        # Run current objective functions for all players.
        for p in self.players.values():
            p.objective()
        # Move all players
        for p in self.players.values():
            p.move()
        self.detect_collisions()
        self.resolve_collisions()
        self.check_ball()
        # Run triggers
        for trig in self.triggers:
            trig.check()
        # Store moves
        # Somewhat dodgy, but this will need to be dumped to a DB soon anyway.
        tick_moves=list()
        for p in self.players.values():
            have_ball = p.pid == self.ball_carrier
            add_move=move_data(p.pid,p.x,p.y,p.angle,have_ball)
            tick_moves.append(add_move)
        # Ball position,use pid=0 for ball
        ball_carried = self.ball_carrier != 0
        add_move=move_data(0,self.xball,self.yball,0,ball_carried)
        tick_moves.append(add_move)
        #
        self.moves.append(tick_moves)
        self.istep += 1

    def check_ball(self):
        """
        Collision detection with the ball. Move ball.
        """
        if self.ball_carrier==0:
            for p in self.players.values():
                dist = np.sqrt( (p.x - self.xball)**2 + (p.y - self.yball)**2)
                if dist < p.size:
                    self.ball_carrier = p.pid        
        else:
            # Move ball with ball carrier
            p = self.players[self.ball_carrier]
            self.xball = p.x
            self.yball = p.y

    def detect_collisions(self):
        """
        Detect any collisions between objects and store a list of any.
        """
        # Simple algorithm. Could speed up many times using a domain decomposition.
        self.collisions=list()
        for thisP in self.players.values():
            for thatP in self.players.values():
                if thisP.pid == thatP.pid:
                    continue
                else:
                    dist = np.sqrt( (thisP.x-thatP.x)**2 + (thisP.y-thatP.y)**2 )\
                        - thisP.size - thatP.size
                    if dist < 0:
                        # Collision occured
                        collision = thisP, thatP, -dist
                        self.collisions.append(collision)

    def resolve_collisions(self):
        """
        Mechanistically resolves collisions.
        """
        # Very simple (and unphysical) implementations for now.
        for c in self.collisions:
            if c[0].team == c[1].team:
                # Same team, move out of the way
                if c[0].x > c[1].x:
                    c[0].x += c[0].size
                else:
                    c[1].x += c[1].size
                if c[0].y > c[1].y:
                    c[0].y += c[0].size
                else:
                    c[1].y += c[1].size                
            else:
                # Opposing team players. Test for tackle.
                if c[0].has_ball() or c[1].has_ball():
                    if c[0].has_ball():
                        tackler=c[1]
                        carrier=c[0]
                    else:
                        tackler=c[0]
                        carrier=c[1]
                    
                    # Just randomly scatter ball for now
                    self.ball_carrier=0

                elif c[0].want_to_block and c[1].want_to_block:
                    # Move each player back along angle of motion by half overlap distance
                    #c[0].move_at_angle(c[0].angle-180.,c[2]/2.)
                    #c[1].move_at_angle(c[1].angle-180.,c[2]/2.)
                    pass
                elif ~c[0].want_to_block and ~c[1].want_to_block:
                    # For now, same as blocking. No evading implemented yet..
                    #c[0].move_at_angle(c[0].angle-180.,c[2]/2.)
                    #c[1].move_at_angle(c[1].angle-180.,c[2]/2.)
                    pass
                else:
                    # No evading implemented, so just repeat double block from above
                    #c[0].move_at_angle(c[0].angle-180.,c[2]/2.)
                    #c[1].move_at_angle(c[1].angle-180.,c[2]/2.)
                    pass

    def scatter_ball(self,amount):
        """
        Scatters the ball by up to amount in a random direction.
        """
        self.xball += np.random.random()*amount-amount/2.
        self.yball += np.random.random()*amount-amount/2.
        self.xball = max(0,self.xball)
        self.yball = max(0,self.yball)
        self.xball = min(self.xsize,self.xball)
        self.yball = min(self.ysize,self.yball)
        
class Trigger:
    """
    Defines triggers that could occur.
    """
    def __init__(self,layout):
        self.layout=layout
        self.callbacks=list()

    def init(self):
        """
        To be called once all callbacks have been added.
        
        Sets all states correctly at start of game.
        """
        pass

    def add_callback(self,func):
        """
        Add a function to call when the trigger goes off
        """
        self.callbacks.append(func)

    def check(self):
        """
        Define the condition
        """
        pass

    def broadcast(self):
        """
        Broadcast triggering to all events.
        """
        for f in self.callbacks:
            f()

class BallLoose(Trigger):
    """
    Ball dropped etc
    """
    def init(self):
        " Setup state store "
        self.prev=self.condition()
        if self.prev: self.broadcast()

    def condition(self):
        if self.layout.ball_carrier ==0:
            return True
        else:
            return False

    def check(self):
        " Check if anyone has the ball "
        cond=self.condition()
        if cond and not self.prev:
            self.prev=True
            self.broadcast()
        elif cond:
            self.prev=True
        else:
            self.prev=False
            
class BallHeld(BallLoose):
    """
    Someone has the ball
    """
    # simply reverse the BallLoose condition
    def condition(self):
        if self.layout.ball_carrier ==0:
            return False
        else:
            return True

