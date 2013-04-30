import tools
import positions

l=tools.Layout(100,50,200)
l.xball=30
l.yball=25
# layout,x,y,jersey,team
home_runner1=positions.Runner(l,30,25,1,1)
home_bruiser1=positions.Bruiser(l,40,30,2,1)
home_bruiser2=positions.Bruiser(l,40,25,3,1)
home_bruiser3=positions.Bruiser(l,40,20,4,1)
#
away_runner1=positions.Runner(l,95,5,1,-1)
away_runner2=positions.Bruiser(l,95,20,2,-1)
away_runner3=positions.Bruiser(l,95,30,3,-1)
away_runner4=positions.Bruiser(l,95,45,4,-1)
#
l.add_player(home_runner1)
l.add_player(home_bruiser1)
l.add_player(home_bruiser2)
l.add_player(home_bruiser3)
l.add_player(away_runner1)
l.add_player(away_runner2)
l.add_player(away_runner3)
l.add_player(away_runner4)

l.run_game()
