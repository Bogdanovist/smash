"""
Defines player positional behavoiour
"""
import tools
import player

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
        throw_power=60. # m/s
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))

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
        throw_power=50.
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))

    def ball_loose(self):
        " Attack nearest opponent "
        self.objective=self.go_psycho

    def ball_held(self):
        " If carrier, run in otherwise go nuts "
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
        throw_power=50.
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))   

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

class Thrower(player.Player):
    """
    Basic test of someone looking to pass.

    At the moment acts like a Catcher without the ball.
    """
    def __init__(self,layout,x,y,jersey,team):
        # Class default stats
        size=1.
        top_speed=8.
        acc=2.5
        strength=0.6
        throw_power=80.
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,throw_power,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self,ball_held))

    def ball_loose(self):
        " Get the ball "
        self.objective=self.get_loose_ball

    def ball_held(self):
        " What to do when the ball is held by some player "
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
