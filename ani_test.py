"""
This short code snippet utilizes the new animation package in
matplotlib 1.1.0; it's the shortest snippet that I know of that can
produce an animated plot in python. I'm still hoping that the
animate package's syntax can be simplified further. 
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class AnObject(object):
    
    def simData(self):
# this function is called as the argument for
# the simPoints function. This function contains
# (or defines) and iterator---a device that computes
# a value, passes it back to the main program, and then
# returns to exactly where it left off in the function upon the
# next call. I believe that one has to use this method to animate
# a function using the matplotlib animation package.
        t_max = 10.0
        dt = 0.05
        x = 0.0
        t = 0.0
        while t < t_max:
            x = np.sin(np.pi*t)
            t = t + dt
            yield x, t
 
    def simPoints(self,simData):
        x, t = simData[0], simData[1]
        self.time_text.set_text(self.time_template%(t))
        self.line.set_data(t, x)
        return self.line, self.time_text

    def do_plot(self):
##
##   set up figure for plotting:
##
        fig = plt.figure()
        ax = fig.add_subplot(111)
# I'm still unfamiliar with the following line of code:
        self.line, = ax.plot([], [], 'bo', ms=10)
        ax.set_ylim(-1, 1)
        ax.set_xlim(0, 10)
##
        self.time_template = 'Time = %.1f s'    # prints running simulation time
        self.time_text = ax.text(0.05, 0.9, '', transform=ax.transAxes)
## Now call the animation package: (simData is the user function
## serving as the argument for simPoints):

        ani = animation.FuncAnimation(fig, self.simPoints, self.simData, blit=False,\
                                          interval=10, repeat=True)
        plt.show()

obj=AnObject()
obj.do_plot()
