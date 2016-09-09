import numpy as np
from player import DefaultPlayer

class Game:
    def __init__(self, board, deck, max_nturns=200, vps_to_win=11):
        self.board = board
        self.deck = deck
        self.max_nturns = max_nturns
        self.vps_to_win = vps_to_win
        self.valid_actions = ["draw", "buy"]
        self.valid_cards = ["garden", "curse"]
        assert set(self.deck.card_names) == set(self.valid_cards)

    def play(self, players):
        assert(len(set([p.index for p in players])) == len(players))
        assert all(["H" != p.index for p in players])
        for i in xrange(self.max_nturns):
            if self.game_is_over():
                self.end_game(players)
                return
            p = players[i % len(players)]
            self.next_turn(p, players)

    def next_turn(self, p, players):
        act_name, acts = p.take_action(self.board)
        assert act_name in self.valid_actions
        if act_name == "draw":
            card = self.deck.draw()
            if card == "garden":
                self.board.add_random_garden()
            elif card == "curse":
                assert len(acts) == 3 # (i,j,n)
                (i,j,n) = acts
                cs, add_curse = self.board.curse_tile((i,j), n)
                if add_curse:
                    self.deck.discard.append("curse")
                for pind in cs:
                    pcs = [pc for pc in players if pc.index == pind]
                    assert len(pcs) == 1
                    pcs[0].vps += cs[pind]
                p.money += int(n > 1) + n
        elif act_name == "buy":
            is_success = self.board.add_objects(acts, p.index)
            cost = sum([self.board.obj_cost[nm] for nm,pos in acts])
            assert p.money >= cost
            p.money -= cost
            assert is_success

    def game_is_over(self):
        return self.board.tiles.sum() == 0

    def end_game(self, players):
        if self.game_is_win():
            pi = self.winning_player(players).index
            print "Game won by Player {0}.".format(pi)
        else:
            print "Game lost."

    def game_is_win(self, players):
        return sum([p.vps for p in players]) >= self.vps_to_win

    def winning_player(self):
        return players[np.argmax([p.vps for p in players])]

class Board:
    def __init__(self, (nrows, ncols), obj_cost, ntrees=15):
        """
        costs = {name: cost, ...}
        """
        self.nrows = nrows
        self.ncols = ncols
        self.ntrees_init = ntrees
        self.obj_cost = obj_cost
        self.tiles = self.init_tiles(self.nrows, self.ncols, self.ntrees_init)
        self.grid = self.init_grid(self.tiles)
        self.obj_add = {"hut": "H", "station": "S{0}"}
        assert set(self.obj_names.keys()) == set(self.obj_cost.keys())

    def get_tree_ind(self, tiles, n=1):
        row = np.random.randint(low=0, high=tiles.shape[0], size=(n,))
        col = np.random.randint(low=0, high=tiles.shape[1], size=(n,))
        return zip(row, col)

    def init_tiles(self, nrows, ncols, ntrees):
        tiles = np.zeros([nrows, ncols])
        trees = self.get_tree_ind(tiles, ntrees)
        for (r,c) in trees:
            tiles[r,c] += 1
        return tiles

    def init_grid(self, tiles):
        # ignoring edge object tiles
        n_rows = 2*(tiles.shape[0]-1)
        n_cols = tiles.shape[1]-1
        return np.zeros([n_rows,n_cols])

    def grids_touching_tile(self, r, c):
        ro = 2*r
        co = c
        rs = [ro-2, ro-1, ro-1, ro,   ro, ro+1]
        cs = [co,   co-1, co,   co-1, co, co-1]
        inds = [(r,c) for r,c in zip(rs,cs) if 0 <= r < self.grid.shape[0] and 0 <= c < self.grid.shape[1]]
        return inds

    def tiles_touching_grid(self, r, c):
        # no boundary checks because we're ignoring edge object tiles
        inds = []
        tr = r/2
        tc = c
        if r % 2 == 0:
            inds = [(tr,tc), (tr,tc+1), (tr+1,tc)]
        else:
            inds = [(tr+1,tc+1), (tr,tc+1), (tr+1,tc)]
        return inds

    def add_objects(self, objs, player_index):
        is_success = all([nm in self.obj_cost for nm,pos in objs])
        for nm, (i,j) in objs:
            is_success = is_success and (self.grid[i,j] == 0)
            self.grid[i,j] = self.obj_names[nm].format(player_index) # e.g. "S1", "S2", ...
        return is_success

    def valid_object_inds(self):
        inds = [(i,j) for i in xrange(self.grid.shape[0]) for j in xrange(self.grid.shape[1])]
        return [(i,j) for (i,j) in inds if self.grid[i,j] > 0]

    def valid_curse_inds(self):
        return [(r,c, self.tiles[r,c]) for r in xrange(self.tiles.shape[0]) for c in xrange(self.tiles.shape[1]) if tiles[r,c] > 0]

    def add_random_garden(self):
        ind = self.get_tree_ind(self.tiles, n=1)
        r,c = ind[0]
        
        # check for hut nearby
        inds = self.grids_touching_tile(r,c)
        v = len([1 for ro,co in inds if self.grid[ro,co] == self.obj_add["hut"]])
        
        self.tiles[r,c] += (v+1)

    def curse_tile(self, (r, c), n):
        assert n >= 1
        assert tiles[r,c] >= n
        self.tiles[r,c] -= n

        # check for VPs
        cs = {} # counts of adjacent objects, per player
        inds = self.grids_touching_tile(r,c)
        for ro,co in inds:
            if "S" in self.grid[ro,co]:
                pind = self.grid[ro,co].split("S")[1]
                cs[pind] += 1

        # 2nd val notifies if we need to add a curse
        return cs, self.tiles[r,c] == 0

class Deck:
    def __init__(self, card_info):
        """
        cards = [(name, count), ...]
        """
        self.card_names = [nm for nm,n in card_info]
        self.deck = self.init_deck(card_info)
        self.discard = []

    def init_deck(self, card_info):
        deck = []
        for (name, count) in card_info:
            deck.extend([name]*count)
        np.random.shuffle(deck)
        return deck

    def draw(self):
        if len(self.deck) == 0:
            self.shuffle()
        card = deck.pop()
        discard.append(card)
        return card

    def shuffle(self):
        assert len(self.deck) == 0
        self.deck = [x for x in self.discard]
        self.discard = []
        np.random.shuffle(self.deck)

def play_game():
    board = Board((6,6), {"hut": 2, "station": 3})
    Deck = Deck(["garden", 5, "curse", 3])
    g = Game(board, deck)
    ps = [DefaultPlayer(1), DefaultPlayer(2)]
    g.play(ps)

if __name__ == '__main__':
    play_game()
