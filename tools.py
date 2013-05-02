import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pylab
import numpy as np
import json

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

#class move_data(object):
#    " Struct for storing moves "
#    def __init__(self,pid,x,y,angle,have_ball,state):
#        self.pid=pid
#        self.x=x
#        self.y=y
#        self.angle=angle
#        self.have_ball=have_ball
#        self.state=state
        
#class player_data(object):
#    " Struct for storing player meta data for transfer."
#    def __init__(self,jersey,team,position):
#        self.jersey=jersey
#        self.team=team
#        self.position=position

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
            

    def run_game(self):
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
        # Dump to JSON
        jfile = "/home/matt/smash/games/test_header.js"
        with open(jfile,'w') as f:
            f.write(json.dumps(self.player_header))
        jfile = "/home/matt/smash/games/test.js"
        with open(jfile,'w') as f:
            f.write(json.dumps(self.moves))        
        # Display results
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
            #add_move=move_data(p.pid,p.x,p.y,p.angle,have_ball,p.state)
            add_move=make_move_dict(p.pid,p.x,p.y,p.angle,have_ball,p.state)
            tick_moves.append(add_move)
        # Ball position,use pid=0 for ball
        ball_carried = self.ball_carrier != 0
        #add_move=move_data(0,self.xball,self.yball,0,ball_carried,0)
        add_move=make_move_dict(0,self.xball,self.yball,0,ball_carried,0)
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
                # THIS IS TURNED OFF BY THE CONTINUE
                continue
                # Conserve momentum, but completely inelastic collision
                px_before = c[0].current_speed * math.cos(c[0].angle) +\
                    c[1].current_speed* math.cos(c[1].angle)
                py_before = c[0].current_speed * math.sin(c[0].angle) +\
                    c[1].current_speed* math.sin(c[1].angle)
                p_before = np.sqrt(px_before**2 + py_before**2)
                pa_before = math.atan2(py_before,px_before)
                xb,yb = (c[0].x+c[1].x)/2., (c[0].y + c[1].y)/2.
                # Assume equal 'mass' so divide momentum by 2
                xa,ya = xb - px_before * math.cos(pa_before/2.), yb - py_before * math.sin(pa_before/2.)
                c[0].current_speed = p_before/2.
                c[1].current_speed = p_before/2.
                c[0].angle = pa_before
                c[1].angle = pa_before
                # Offset from center of mass
                ang = math.atan2( c[1].y-c[0].y, c[1].x-c[0].x)
                c[0].x = xa + c[0].size*math.cos(ang)*1.1
                c[1].x = xa - c[1].size*math.cos(ang)*1.1
                c[0].y = ya + c[0].size*math.sin(ang)*1.1
                c[1].y = ya - c[1].size*math.sin(ang)*1.1                              
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
            self.scatter_ball(scatter_amount)
        else:
            tackler.state=0
            tackler.prone_counter=tackle_count
    
    def resolve_block(self,b1,b2):
        # Magic numbers
        both_down_chance=0.2
        draw_diff=0.1
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
        self.ball_carrier=0

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

