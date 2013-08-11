import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pylab
import numpy as np
import json
import helpers
import itertools
import utils
import pdb

def make_move_dict(pid,x,y,angle,have_ball,state):
    """
    Utility function to make a small dictionary to store a single move.
    """
    return dict(zip(['pid','x','y','angle','have_ball','state'],[pid,x,y,angle,have_ball,state]))

def make_player_dict(jersey,team,position):
    """
    Utility function for making player data as a small dict
    """
    return dict(zip(['jersey','team','position'],[jersey,team,position]))

class Ball(object):
    """
    Ball object.

    In all functions, 'power' means initial launch velocity.
    """
    g=10 #ms^-2
    # NOTE: We fake up air resistance by increasing gravity. This lets us have fast travelling passes
    # but still with a realistic range. With no resistance and standard gravity a pass that is fast 
    # enough to outpace a fast player travels way too far.
    def __init__(self,layout,x,y):
        self.layout=layout
        self.x=float(x)
        self.y=float(y)
        self.z=0
        self.flying = False
        self.carrier = 0
        self.throw_pending = False
        self.xland = None
        self.yland = None

    def move(self):
        """
        Collision detection with the ball. Move ball.
        
        TODO: Implement catching properly, at the moment anyone will catch if the ball is nearby,
        regardless of z.
        """
        if self.throw_pending:
            self.throw_pending=False
            # Check if thrower was tackled just before release
            if self.carrier != 0:
                p=self.throw_params
                self.launch(p[0],p[1],p[2],p[3])

        if self.flying:
            self.fly_tick()
        elif self.carrier==0:
            # Check for loose ball pickup
            for p in self.layout.players.values():
                dist = np.sqrt( (p.x - self.x)**2 + (p.y - self.y)**2)
                if dist < p.size:
                    self.carrier = p.pid
        else:
            # Move ball with ball carrier
            p = self.layout.players[self.carrier]
            self.x = p.x
            self.y = p.y

    def fly_tick(self):
        " Iterate one flight tick "
        # Check for potential catchers
        # Assume we can only catch if z <= 2 metres.
        # TODO: Player heights and jumping??

        addx, addy = utils.components(self.speed*self.layout.dt,self.angle)

        if self.z <= 2:
            # Ball at catchable height
            # Eqn of ball travelling line as ax + bx + c = 0
            x2 = self.x + addx
            y2 = self.y + addy
            a = self.y - y2
            b = x2 - self.x
            c = (self.x - x2)*self.y + (y2 - self.y)*self.x
            midx = (self.x + x2)/2.
            midy = (self.y + y2)/2.
            dflight = self.speed*self.layout.dt
            def catch_score(p):
                # Returns postion along flight path of ball for given player
                # Returns None if the player can't catch ball from their position
                if not p.want_to_catch: 
                    return None
                dist = abs(a*p.x + b* p.y + c)/np.sqrt(a**2 + b**2)
                if dist > p.size: 
                    return None
                # Check the position is bracketted in the flight delta
                elif np.sqrt( (midx-p.x)**2 + (midy-p.y)**2) > dflight/2. + p.size:
                    return None
                else:
                    return np.sqrt((p.x-self.x)**2 + (p.y-self.y)**2)
            # TODO: At the moment, first eligble catcher automatically catches. Need to implement skill
            # based chance, constested catches, etc.    
            best_score=1000.
            pcatch=None
            for p in self.layout.players.values():
                s = catch_score(p)
                if s != None:
                    if s < best_score:
                        best_score=s
                        pcatch=p
            if pcatch != None:
                # Player had made catch
                print("caught it",pcatch.pid)
                self.carrier=pcatch.pid
                self.flying=False
                self.x = pcatch.x
                self.y = pcatch.y
                return
        
        self.x += addx
        self.y += addy
        # Check for out of bounds
        oob=False
        if self.x < 0:
            self.x = 0
            oob = True
        elif self.x > self.layout.xsize:
            self.x = self.layout.xsize
            oob = True
        if self.y < 0:
            self.y = 0
            oob = True
        elif self.y > self.layout.ysize:
            self.y = self.layout.ysize
            oob = True

        if oob:
            self.flying = False
            self.vspeed=0
            self.speed=0
            self.z=0
            self.xland=self.x
            self.yland=self.y
        else:
            self.vspeed += -self.g * self.layout.dt
            self.z += self.vspeed * self.layout.dt
            if self.z <= 0.:
                self.flying = False

    def throw(self,elv,power,target_x,target_y):
        """
        Sets a throw up, but doesn't execute. Allows delayed execution to avoid messing up
        player objectives (i.e. allow predictable triggering of state changes).
        """
        self.throw_params=[elv,power,target_x,target_y]
        self.throw_pending=True

    def launch(self,elv,power,target_x,target_y):
        """
        Initialise throw with given angle and power from current ball position.
        """
        self.carrier=0
        self.z=2. # Assume passes start 2m off the ground.
        self.angle = math.atan2(target_y-self.y,target_x-self.x)
        self.speed = power*math.cos(elv)
        self.vspeed = power*math.sin(elv)
        self.flying = True
        dist = power**2 * math.sin(2.*elv)/self.g
        dx, dy = utils.components(dist,self.angle)
        self.xland = self.x + dx
        self.yland = self.y + dy

    def find_launch_angle(self,power,x_target,y_target):
         """
         Returns the angle to launch at for a throw with a given power to a given target location. 
         """
         d = np.sqrt( (self.x-x_target)**2 + (self.y-y_target)**2)
         # If we can't reach, throw at 45 degrees to at least maximise distance
         if d > power**2/self.g:
             return math.acos(0.)/2. # 45 degrees in radians
         else:
             return math.asin(d * self.g / power**2)/2.
        
    def scatter(self,amount):
        """
        Scatters the ball by up to amount in a random direction.
        """
        self.x += np.random.random()*amount-amount/2.
        self.y += np.random.random()*amount-amount/2.
        self.x = utils.bracket(0,self.x,self.layout.xsize)
        self.y = utils.bracket(0,self.y,self.layout.ysize)

class Layout(object):
    """
    Base(?) class for the backdrop in which stuff happens.
    """
    def __init__(self,xsize,ysize,game_length,dt=0.1):
        self.xsize=float(xsize)
        self.ysize=float(ysize)       
        self.ball=Ball(self,self.xsize/2.,self.ysize/2.)
        self.players=dict()
        self.collisions=list()
        self.game_length=game_length
        self.dt=dt
        self.nsteps = int(self.game_length/self.dt)
        # Save all moves
        self.moves=list()
        # Store step number
        self.istep=0
        # Store list of all triggers in use here, in order to loop over in one place.
        self.triggers = list()
        # Init list of helpers
        self.helpers = dict()
        self.helpers['pb_eqs']=helpers.BallCarrierPBeqs(self)
        self.helpers['maps']=helpers.Maps(self)
        #self.helpers['maps']=helpers.HazardMaps(self)

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
            iframe = iframe + 1
            yield moves

    def frame_display(self,frame_data):
        for move, p in zip(frame_data,self.plots):
            if move['state'] == 0:
                shape='v'
            else:
                shape='o'

            if self.player_header[move['pid']]['team'] == 1:
                col='r'
            elif self.player_header[move['pid']]['team'] == -1:
                col='b'
            else:
                col='g'
                shape='o'
            p.set_data(move['x'],move['y'])
            p.set_marker(shape)
            p.set_color(col)
            

    def run_game(self,display=True):
        " Run the game "
        # Setup move storage
        self.player_header=dict()
        for p in self.players.values():
            #self.player_header[p.pid]=player_data(p.jersey,p.team,'null')
            self.player_header[p.pid]=make_player_dict(p.jersey,p.team,'null')
        # Add ball to player_header
        self.player_header[0]=make_player_dict(0,0,'null')#player_data(0,0,'null')
        # Add inits here? I.e. special player method to set initial objectives?
        for trig in self.triggers:
            trig.init()
        # Run it
        for i in range(self.nsteps):
            self.tick()
            if self.check_scoring():
                break
        # Dump to JSON
        jfile = "/home/matt/smash/games/test_header.js"
        with open(jfile,'w') as f:
            f.write(json.dumps(self.player_header))
        jfile = "/home/matt/smash/games/test.js"
        with open(jfile,'w') as f:
            f.write(json.dumps(self.moves))        
        # Display results
        if display:
            fig1=plt.figure()
            plt.xlim([0,self.xsize])
            plt.ylim([0,self.ysize])

            self.plots=list()
            for p in self.players.values():
                if p.team == 1:
                    plot_now, = plt.plot([], [], 'ro',markersize=15)
                else:
                    plot_now, = plt.plot([], [], 'bo',markersize=15)
                self.plots.append(plot_now)
            plot_now, =  plt.plot([],[],'go')
            self.plots.append(plot_now)
            line_ani = animation.FuncAnimation(fig1,self.frame_display,self.frame_data,interval=20,blit=False,repeat=True)
            plt.show()

    def tick(self):
        """
        Iterate one tick.
        """
        # Stand prone players up
        for p in self.players.values():
            p.standup()
        # update helpers
        for h in self.helpers.values():
            h.update()
        # Run current objective functions for all players.
        for p in self.players.values():
            p.objective()
            p.objective_sanity()
        # Ensure players on the same team are not attempting to run into each other
        self.prevent_friendly_collisions()
        # Move all players
        for p in self.players.values():
            p.move()
        self.detect_collisions()
        self.resolve_collisions()
        self.ball.move()
        # Run triggers
        for trig in self.triggers:
            trig.check()
        # Store moves
        # Somewhat dodgy, but this will need to be dumped to a DB soon anyway.
        tick_moves=list()
        for p in self.players.values():
            have_ball = p.pid == self.ball.carrier
            #add_move=move_data(p.pid,p.x,p.y,p.angle,have_ball,p.state)
            add_move=make_move_dict(p.pid,p.x,p.y,p.angle,have_ball,p.state)
            tick_moves.append(add_move)
        # Ball position,use pid=0 for ball
        ball_carried = self.ball.carrier != 0
        add_move=make_move_dict(0,self.ball.x,self.ball.y,0,ball_carried,0)
        tick_moves.append(add_move)
        #
        self.moves.append(tick_moves)
        self.istep += 1

    def check_scoring(self):
        """
        Has a team scored?
        """
        end_zone_size=2.
        if self.ball.carrier == 0:
            return False
        else:
            if self.ball.x < end_zone_size or self.ball.x > (self.xsize - end_zone_size):
                return True
            else:
                return False

    def prevent_friendly_collisions(self):
        """
        Ensure objective locations of same team players are spaced.
        """
        # Change objectives to pointing just in front of player, rather than
        # potentially a long way away.
        for p in self.players.values():
            angle = math.atan2(p.y_objective-p.y,p.x_objective-p.x)
            xadd, yadd = utils.components(p.top_speed*self.dt,angle)
            p.x_objective = p.x + xadd
            p.y_objective = p.y + yadd
        for thisP, thatP in itertools.combinations(self.players.values(), 2):
            if thisP.state == 0 or thatP.state == 0:
                continue # Prone players don't count
            elif thisP.team != thatP.team:
                continue # Different teams, probably WANT to collide...
            else:
                dist = np.sqrt( (thisP.x_objective-thatP.x_objective)**2 +\
                                    (thisP.y_objective-thatP.y_objective)**2 )\
                                    - thisP.size - thatP.size
                if dist < 0:
                    # We need to adjust the objectives.
                    # Find mid-point of current positions
                    cx = (thisP.x + thatP.x)/2.
                    cy = (thisP.y + thatP.y)/2.
                    # Find mid-point of objectives
                    ox = (thisP.x_objective + thatP.x_objective)/2.
                    oy = (thisP.y_objective + thatP.y_objective)/2.
                    # Find angle of line between two objectives.
                    hpi=2*math.atan(1.)
                    angle = math.atan2(cy-oy,cx-ox)
                    # Find angle of p.b. of this line
                    pb_angle = -1/angle
                    # Project along the p.b. line enough to seperate the two objectives
                    pdist = -dist/2.
                    thisx_delta, thisy_delta =  utils.components(pdist,pb_angle)
                    thatx_delta, thaty_delta =  utils.components(pdist,pb_angle+hpi)
                    thisP.x_objective += thisx_delta
                    thisP.y_objective += thisy_delta
                    thatP.x_objective += thatx_delta
                    thatP.y_objective += thaty_delta
                        
    def detect_collisions(self):
        """
        Detect any collisions between objects and store a list of any.
        """
        # Simple algorithm. Could speed up many times using a domain decomposition.
        self.collisions=list()
        for thisP in self.players.values():
            for thatP in self.players.values():
                # Ensure we don't double count collisions (i.e. by exchange of this and that)
                if thisP.pid >= thatP.pid:
                    continue
                elif thisP.state == 0 or thatP.state == 0:
                    # Prone players can be run over
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
                # Conserve momentum, but completely inelastic collision
                continue
                # Set back to pre collision positions
                c[0].x, c[0].y, c[0].angle, c[0].current_speed = c[0].unproject_move(c[0].angle)
                c[1].x, c[1].y, c[1].angle, c[1].current_speed = c[1].unproject_move(c[1].angle)

                px_before = c[0].current_speed * math.cos(c[0].angle) +\
                    c[1].current_speed* math.cos(c[1].angle)
                py_before = c[0].current_speed * math.sin(c[0].angle) +\
                    c[1].current_speed* math.sin(c[1].angle)
                p_before = np.sqrt(px_before**2 + py_before**2)
                pa_before = math.atan2(py_before,px_before)
                xb,yb = (c[0].x+c[1].x)/2., (c[0].y + c[1].y)/2.
                # Assume equal 'mass' so divide momentum by 2
                xa,ya = xb + px_before * math.cos(pa_before)/2., yb + py_before * math.sin(pa_before)/2.
                c[0].current_speed = p_before/2.
                c[1].current_speed = p_before/2.
                c[0].angle = pa_before
                c[1].angle = pa_before
                # Offset from center of mass
                ang = math.atan2( c[1].y-c[0].y, c[1].x-c[0].x)
                c[0].x = xa + c[0].size*math.cos(ang)*1.
                c[1].x = xa - c[1].size*math.cos(ang)*1.
                c[0].y = ya + c[0].size*math.sin(ang)*1.
                c[1].y = ya - c[1].size*math.sin(ang)*1.                              
                # Same team, move out of the way
                #if c[0].x > c[1].x:
                #    c[0].x += c[0].size
                #else:
                #    c[1].x += c[1].size
                #if c[0].y > c[1].y:
                #    c[0].y += c[0].size
                #else:
                #    c[1].y += c[1].size                
            else:
                # Opposing team players. Test for tackle.
                if c[0].has_ball() or c[1].has_ball():
                    if c[0].has_ball():
                        tackler=c[1]
                        carrier=c[0]
                    else:
                        tackler=c[0]
                        carrier=c[1]
                    self.resolve_tackle(tackler,carrier)
                elif c[0].want_to_block or c[1].want_to_block:
                    self.resolve_block(c[0],c[1])
                else:
                    # No one wants to block.
                    # For now, let them run through each other.
                    pass

    def resolve_tackle(self,tackler,carrier):
        # Magic numbers
        scatter_amount=10
        tackle_count=5
        
        tackle_odds = tackler.strength/carrier.strength
        log_odds = np.log(tackle_odds)
        tackle_chance = np.exp(log_odds)/(1 + np.exp(log_odds))
        
        roll = np.random.random()
        if roll < tackle_chance:
            carrier.state=0
            carrier.prone_counter=tackle_count
            self.ball.scatter(scatter_amount)
            self.ball.carrier=0
        else:
            tackler.state=0
            tackler.prone_counter=tackle_count
    
    def resolve_block(self,b1,b2):
        # Magic numbers
        both_down_chance=0.02
        draw_diff=0.5
        push_back_amount = 1
        pi=4.*math.atan(1.)
        block_count=5

        b1_odds = b1.strength/b2.strength
        log_odds = np.log(b1_odds)
        b1_chance = np.exp(log_odds)/(1. + np.exp(log_odds))

        # First determine if someone 'wins' and knocks down opponent.
        # In case of a a draw in that regard, then assess push backs.
        win_roll=np.random.random()

        if abs(win_roll-b1_chance) < draw_diff:
            # Draw on knock downs. See pushbacks
            both_down_roll=np.random.random()
            if both_down_roll < both_down_chance:
                b1.state=0
                b2.state=0
                b1.prone_counter=block_count
                b2.prone_counter=block_count
            else:
                if win_roll < b1_chance:
                    b2.move_at_angle(b2.angle+pi,push_back_amount)
                else:
                    b1.move_at_angle(b1.angle+pi,push_back_amount)
        else:
            # Someone is going down
            if win_roll < b1_chance:
                b2.state=0
                b2.prone_counter=block_count
            else:
                b1.state=0
                b1.prone_counter=block_count

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
        if self.condition():
            self.broadcast()

    def add_callback(self,func):
        """
        Add a function to call when the trigger goes off
        """
        self.callbacks.append(func)

    def condition(self):
        """
        Define condition
        """
        pass

    def check(self):
        """
        Check for change in condition
        """
        if self.condition():
            self.broadcast()
        #cond=self.condition()
        #if cond and not self.prev:
        #    self.prev=True
        #    self.broadcast()
        #elif cond:
        #    self.prev=True
        #else:
        #    self.prev=False

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
    def condition(self):
        if self.layout.ball.carrier ==0 and not self.layout.ball.flying:
            return True
        else:
            return False
            
class BallHeld(BallLoose):
    """
    Someone has the ball
    """
    # simply reverse the BallLoose condition
    def condition(self):
        if self.layout.ball.carrier ==0:
            return False
        else:
            return True

class BallFlying(Trigger):
    """
    Ball in the air.
    """
    def condition(self):
        return self.layout.ball.flying

#class BallLanded(Trigger):
#    def condition(self):
#        if self.layout.ball.flying:
#            return False
#        else:
#            return True 
