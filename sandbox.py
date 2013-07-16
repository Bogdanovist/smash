import tools
import positions

l=tools.Layout(100,50,1000)
l.xball=30
l.yball=25
# layout,x,y,jersey,team
home_runner1=positions.Runner(l,5,20,1,1)
home_runner2=positions.Runner(l,15,25,2,1)
home_runner3=positions.Runner(l,5,30,3,1)
home_runner4=positions.Runner(l,5,35,4,1)
home_bruiser1=positions.Bruiser(l,40,30,5,1)
home_bruiser2=positions.Bruiser(l,40,25,6,1)
home_bruiser3=positions.Bruiser(l,40,20,7,1)
home_catcher1=positions.Catcher(l,95,45,8,1)
#
away_runner1=positions.Runner(l,95,20,1,-1)
away_runner2=positions.Runner(l,95,26,2,-1)
away_runner3=positions.Runner(l,95,31,3,-1)
away_runner4=positions.Runner(l,95,20,4,-1)
#
#l.add_player(home_runner1)
l.add_player(home_runner2)
l.add_player(home_catcher1)
#l.add_player(home_runner3)
#l.add_player(home_runner4)
#l.add_player(home_bruiser1)
#l.add_player(home_bruiser2)
#l.add_player(home_bruiser3)
#l.add_player(away_runner1)
#l.add_player(away_runner2)
#l.add_player(away_runner3)
l.add_player(away_runner4)

l.run_game()
