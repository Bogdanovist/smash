"""
Defines player positional behavoiour
"""
import tools
import player
import pdb

class Defender(player.Player):
    """
    Hang back to defend end zone.
    """
    def __init__(self,layout,x,y,jersey,team):
        # Class default stats
        size=1.
        top_speed=10. # m/s
        acc=3.0 # m/s/s
        strength=0.6
        throw_power=15. # m/s
        self.find_space_update_time=2. # Every 2 seconds
        forward_limit=30. # Roughly how far to push forward at most.
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))
        self.ai_config.append((tools.BallFlying,self.ball_flying))

    def ball_loose(self):
        if self.dist_to_goal(x=self.layout.ball.x) < self.forward_limit:
            # Ball near our end zone, try and recover
            self.objective = self.get_loose_ball
        else:
            # Ball out of our defensive zone
            # TODO: Dumb to compleletly ignore ball in this situation
            self.objective = self.coverage

    def ball_held(self):
        " What to do when the ball is held by some player "
        carrier = self.layout.players[self.layout.ball.carrier]
        if self.pid == carrier.pid:
            # I have the ball!
            self.objective=self.run_or_pass
        elif self.team == carrier.team:
            # team mate has ball
            # TODO: Should block for team mate, but not implemented yet.
            self.objective = self.coverage
        else:
            # opponent has ball
            if self.dist_to_goal(x=self.layout.ball.x) < self.forward_limit:
                self.objective = self.tackle_ball_carrier
            else:
                self.objective = self.coverage

    def ball_flying(self):
        self.objective = self.catch_ball

class Forward(player.Player):
    """
    Push forward and look for a pass
    """
    pass

class Runner(player.Player):
    """
    In defence goes for loose ball or carrier. In offense runs to end zone.
    ??? In offence without the ball???
    """
    def __init__(self,layout,x,y,jersey,team):
        # Class default stats
        size=1.
        top_speed=10. # m/s
        acc=3.0 # m/s/s
        strength=0.6
        throw_power=15. # m/s
        self.find_space_update_time=2. # Every 2 seconds
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))
        self.ai_config.append((tools.BallFlying,self.ball_flying))
        #self.ai_config.append((tools.BallLanded,self.ball_loose))

    def ball_loose(self):
        " Set to run straight at the ball "
        self.objective=self.get_loose_ball

    def ball_held(self):
        " What to do when the ball is held by some player "
        carrier = self.layout.players[self.layout.ball.carrier]
        if self.pid == carrier.pid:
            # I have the ball!
            self.objective=self.run_to_goal
        elif self.team == carrier.team:
            # team mate has ball
            self.objective = self.get_loose_ball
        else:
            # opponent has ball
            self.objective = self.tackle_ball_carrier

    def ball_flying(self):
        " What to do when the ball is in the air"
        self.objective = self.catch_ball

class Bruiser(player.Player):
    """
    Simply tries to knock down nearest opponent.
    """
    def __init__(self,layout,x,y,jersey,team):
        # Class default stats
        size=1.
        top_speed=6.
        acc=2.0
        strength=1.
        throw_power=15.
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))

    def ball_loose(self):
        " Attack nearest opponent "
        self.objective=self.go_psycho

    def ball_held(self):
        " If carrier then run in, otherwise go nuts "
        carrier = self.layout.players[self.layout.ball.carrier]
        if self.pid == carrier.pid:
            # I have the ball!
            self.objective=self.run_to_goal
        else:
            self.objective=self.go_psycho

class Catcher(player.Player):
    """
    Basic test position for someone trying to get into a good spot to recieve
    a pass. For now, in defence just tries to kill the dill.
    """
    def __init__(self,layout,x,y,jersey,team):
        # Class default stats
        size=1.
        top_speed=12.
        acc=4.0
        strength=0.4
        throw_power=15.
        self.find_space_update_time=2.
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))   
        self.ai_config.append((tools.BallFlying,self.ball_flying))
        #self.ai_config.append((tools.BallLanded,self.ball_loose))

    def ball_loose(self):
        " Get the ball "
        # Use base class method.
        self.objective=self.get_loose_ball
    
    def ball_held(self):
        " What to do when the ball is held by some player "
        carrier = self.layout.players[self.layout.ball.carrier]
        if self.pid == carrier.pid:
            # I have the ball!
            self.objective=self.run_to_goal
        elif self.team == carrier.team:
            # team mate has ball
            self.objective = self.find_space
        else:
            # opponent has ball
            self.objective = self.tackle_ball_carrier     
    
    def ball_flying(self):
        " What to do when the ball is in the air"
        self.objective = self.catch_ball

class Thrower(player.Player):
    """
    Basic test of someone looking to pass.

    At the moment acts like a Catcher without the ball.
    """
    def __init__(self,layout,x,y,jersey,team):
        # Class default stats
        size=1.
        top_speed=8.
        acc=8.
        strength=0.6
        throw_power=20.
        self.find_space_update_time=2.
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))
        self.ai_config.append((tools.BallFlying,self.ball_flying))
#        self.ai_config.append((tools.BallLanded,self.ball_loose))

    def ball_loose(self):
        " Get the ball "
        if self.pid == self.layout.ball.carrier:
            print("WTF")
            pdb.set_trace()
        self.objective=self.get_loose_ball

    def ball_held(self):
        " What to do when the ball is held by some player "
        if self.pid == self.layout.ball.carrier:
            print("I the carrier",self.objective)
        carrier = self.layout.players[self.layout.ball.carrier]
        if self.pid == carrier.pid:
            # I have the ball!
            self.objective=self.run_or_pass
        elif self.team == carrier.team:
            # team mate has ball
            self.objective = self.find_space
        else:
            # opponent has ball
            self.objective = self.tackle_ball_carrier 
        if self.pid == self.layout.ball.carrier:
            print("Decided",self.objective)

    def ball_flying(self):
        " What to do when the ball is in the air"
        self.objective = self.catch_ball
