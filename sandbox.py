import tools
import positions

def runit(display=True):
    l=tools.Layout(100,50,50.,0.1)
    l.ball.x=30
    l.ball.y=25
    # layout,x,y,jersey,team
    home_runner1=positions.Runner(l,5,20,1,1)
    home_runner2=positions.Runner(l,15,25,2,1)
    home_runner3=positions.Runner(l,5,30,3,1)
    home_runner4=positions.Runner(l,5,35,4,1)
    home_bruiser1=positions.Bruiser(l,40,30,5,1)
    home_bruiser2=positions.Bruiser(l,40,25,6,1)
    home_bruiser3=positions.Bruiser(l,40,20,7,1)
    home_catcher1=positions.Catcher(l,95,45,8,1)
    home_thrower1=positions.Thrower(l,40,10,9,1)
    home_thrower2=positions.Thrower(l,40,20,9,1)
    home_thrower3=positions.Thrower(l,40,30,9,1)
    home_thrower4=positions.Thrower(l,40,40,9,1)
    #
    away_runner1=positions.Runner(l,95,20,1,-1)
    away_runner2=positions.Runner(l,95,26,2,-1)
    away_runner3=positions.Runner(l,95,31,3,-1)
    away_runner4=positions.Runner(l,95,20,4,-1)
    away_thrower1=positions.Thrower(l,90,10,9,-1)
    away_thrower2=positions.Thrower(l,90,20,9,-1)
    away_thrower3=positions.Thrower(l,90,30,9,-1)
    away_thrower4=positions.Thrower(l,90,40,9,-1)
    #
    l.add_player(home_thrower1)
    l.add_player(home_thrower2)
    l.add_player(home_thrower3)
    l.add_player(home_thrower4)
    l.add_player(away_thrower1)
    l.add_player(away_thrower2)
    l.add_player(away_thrower3)
    l.add_player(away_thrower4)
    #l.add_player(home_runner1)
    #l.add_player(home_runner2)
    #l.add_player(home_catcher1)
    #l.add_player(home_thrower)
    #l.add_player(home_runner3)
    #l.add_player(home_runner4)
    #l.add_player(home_bruiser1)
    #l.add_player(home_bruiser2)
    #l.add_player(home_bruiser3)
    #l.add_player(away_runner1)
    #l.add_player(away_runner2)
    #l.add_player(away_runner3)
    #l.add_player(away_runner4)

    l.run_game(display)

#runit()
