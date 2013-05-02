"""
Defines player positional behavoiour

Experimentally a total game setup??
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
        top_speed=0.5
        acc=0.2
        strength=0.6
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))

    def ball_loose(self):
        " Set to run straight at the ball "
        self.objective=self.get_loose_ball

    def ball_held(self):
        " What to do when the ball is held by some player "
        carrier = self.layout.players[self.layout.ball_carrier]
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
        top_speed=0.4
        acc=0.15
        strength=1.
        player.Player.__init__(self,layout,size,x,y,top_speed,acc,strength,jersey,team)

    def set_ai_config(self):
        self.ai_config=list()
        self.ai_config.append((tools.BallLoose,self.ball_loose))
        self.ai_config.append((tools.BallHeld,self.ball_held))

    def ball_loose(self):
        " Attack nearest opponent "
        self.objective=self.go_psycho

    def ball_held(self):
        " If carrier, run in otherwise go nuts "
        carrier = self.layout.players[self.layout.ball_carrier]
        if self.pid == carrier.pid:
            # I have the ball!
            self.objective=self.run_to_goal
        else:
            self.objective=self.go_psycho
