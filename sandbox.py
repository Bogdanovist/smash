import tools
import positions

l=tools.Layout(100,50,200)
# layout,size,x,y,top_speed,acc,jersey,team
test_player=positions.Runner(l,1,47,24,0.5,0.1,1,1)
test2_player=positions.Runner(l,1,40,10,0.5,0.1,4,1)
smart_tackle=positions.Runner(l,1,98,45,0.5,0.1,2,-1)
dumb_tackle=positions.Runner(l,1,70,22,0.5,0.1,3,-1)
l.add_player(test_player)
l.add_player(test2_player)
l.add_player(smart_tackle)
l.add_player(dumb_tackle)
l.run_game()
#for i in range(100):
#    l.tick()
