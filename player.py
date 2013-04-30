
class Player(object):
    """
    Player object

    Parameters
    ----------
    team : 1 or -1. Can be interpreted as team=1 -> scores to the right
    """
    def __init__(self,layout,size,x,y,top_speed,acc,strength,jersey,team,angle_of_motion=0):
        self.layout=layout
        self.size=size
        self.pid=0 # Actual PIDs get set when player is registered to a layout.
        self.x=float(x)
        self.y=float(y)
        self.top_speed=top_speed
        self.acc=acc
        self.strength=strength
        self.jersey=jersey
        self.team=team
        self.angle=angle_of_motion
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
            self.x_objective=self.layout.xball
            self.y_objective=self.layout.yball

    def protect_ball_carrier(self):
        """
        Get between ball carrier and opponents.
        """
        carrier=self.layout.players[self.layout.ball_carrier]
        
        # Who to block? We could try and block nearest baddy to us, but they might not be
        # a threat to the carrier. We could try to block the one nearest the carrier, but
        # there might be one closer to us we could better block??

    def move(self):
        """
        Move method for each tick update.
        """
        # This uses some geometry from the notebook that I am not yet
        # convinced about...
        # We are ignoring \delta_t by calling it unity, so V and A need to be in appropriate
        # units to reflect that.

        # Don't move if we are prone
        if self.state == 0:
            return

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
            
