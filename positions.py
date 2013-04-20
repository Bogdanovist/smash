"""
Defines player positional behavoiour

Experimentally a total game setup??
"""
import tools

class Runner(tools.Player):
    """
    In defence goes for loose ball or carrier. In offense runs to end zone.
    """
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
            
