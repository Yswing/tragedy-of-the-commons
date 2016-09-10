from player import DefaultPlayer, SelfishPlayer, SuperSelfishPlayer, GenerousPlayer, ReasonablePlayer, CautiousPlayer
from model import Game, Deck, Board

def get_players(ptypes):
    plkp = {"generous": GenerousPlayer, "selfish": SelfishPlayer, "default": DefaultPlayer, "super-selfish": SuperSelfishPlayer, "reasonable": ReasonablePlayer, "cautious": CautiousPlayer}
    ps = []
    for i,p in enumerate(ptypes):
        ps.append(plkp[p](i+1, p + "-" + str(i+1)))
    return ps

def play_game(ngames=100):
    verbose = ngames == 1

    cost_of_hut = 0.05
    cost_of_station = 3
    ntrees = 9
    ngardens = 3
    ncurses = 3

    """
    IDEAL GAME SCENARIOS:
        selfish vs. selfish: RARELY WIN
        selfish vs. default: MOSTLY WIN -> SELFISH
        selfish vs. generous: ALWAYS WIN -> SELFISH
        generous vs. generous: RARELY WIN
    """
    player_types = ["reasonable", "reasonable"] # 
    # player_types = ["default", "generous"] # 
    # player_types = ["super-selfish", "super-selfish"] # 
    # player_types = ["selfish", "reasonable"] # 
    # player_types = ["selfish", "selfish"] # 
    # player_types = ["reasonable", "selfish"] # 
    # player_types = ["selfish", "super-selfish"] # 
    # player_types = ["super-selfish", "reasonable"] # 
    # player_types = ["super-selfish", "generous"] # 
    # player_types = ["selfish", "default"] # 8/10, all S
    # player_types = ["selfish", "generous"] # 5/10, all S
    # player_types = ["generous", "generous"] # 0/10
    # player_types = ["reasonable", "reasonable"] # 0/10

    board = Board((6,6), {"hut": cost_of_hut, "station": cost_of_station}, ntrees=ntrees)
    deck = Deck({"garden": ngardens, "curse": ncurses})
    g = Game(board, deck, verbose=verbose)
    ps = get_players(player_types)
    ss = []
    ws = []
    for i in xrange(ngames):
        status, winner = g.play(ps, print_end_status=False)
        ss.append(status)
        ws.append(winner)
        g.reset()

    import collections
    print '=================='
    print collections.Counter(ws)
    print collections.Counter(ss)

if __name__ == '__main__':
    play_game()
