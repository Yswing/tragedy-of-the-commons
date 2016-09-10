import numpy as np
import collections

class Players:
    def __init__(self, players):
        self.players = players
        self.init()

    def init(self):
        self.vps = dict((p.index, 0) for p in self.players)
        self.money = dict((p.index, 0) for p in self.players)
        self.huts = dict((p.index, 0) for p in self.players)
        self.stations = dict((p.index, 0) for p in self.players)

    def get_money(self, player_index):
        return self.money[player_index]

    def get_vps(self, player_index):
        return self.vps[player_index]

    def update_money(self, player_index, delta):
        assert delta != 0
        if delta < 0:
            assert self.money[player_index] >= abs(delta)
        self.money[player_index] += delta

    def update_vps(self, player_index, delta):
        assert delta > 0
        self.vps[player_index] += delta

    def update_purchases(self, player_index, acts):
        for nm, _ in acts:
            if nm == "hut":
                self.huts[player_index] += 1
            elif nm == "station":
                self.stations[player_index] += 1
            else:
                assert False

    def player_status(self, player_index):
        p = [p for p in self.players if p.index == player_index][0]
        return "P({0}): ${1}, {2} VPs, {3} huts, {4} stations".format(p.name, self.money[p.index], self.vps[p.index], self.huts[p.index], self.stations[p.index])

    def player_with_most_vps(self):
        vmax = -1
        imax = -1
        for i,v in self.vps.iteritems():
            if v > vmax:
                vmax = v
                imax = i
        # return None if tie
        if len([v for i,v in self.vps.iteritems() if v == self.vps[imax]]) > 1:
            return None
        return [p for p in self.players if p.index == imax][0]

    def validate(self):
        assert(len(set([p.index for p in self.players])) == len(self.players))
        assert all([type(p.index) is int and p.index > 0 for p in self.players])

class Game:
    def __init__(self, board, deck, max_nturns=200, vps_to_win=11, verbose=False):
        self.board = board
        self.deck = deck
        self.max_nturns = max_nturns
        self.vps_to_win = vps_to_win
        self.valid_actions = ["draw", "buy"]
        self.valid_cards = ["garden", "curse"]
        self.verbose = verbose
        assert set(self.deck.card_names) == set(self.valid_cards)

    def play(self, players, print_end_status=True):
        Ps = Players(players)
        for i in xrange(self.max_nturns):
            if self.game_is_over():
                return self.end_game(Ps, i, False, print_end_status)
            p = players[i % len(Ps.players)]
            self.next_turn(p, Ps)
        print "Warning: Game ended due to max iterations."
        return self.end_game(Ps, i, True, print_end_status)

    def reset(self):
        self.deck.init_deck()
        self.board.init_board()

    def next_turn(self, p, Ps):
        act_name, acts = p.take_action(self.board, Ps.get_money(p.index))
        assert act_name in self.valid_actions
        card = None
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
                    Ps.update_vps(pind, cs[pind])
                Ps.update_money(p.index, int(n>1) + n)
        elif act_name == "buy":
            is_success = self.board.add_objects(acts, p.index)
            cost = sum([self.board.obj_cost[nm] for nm,pos in acts])
            Ps.update_money(p.index, -cost)
            Ps.update_purchases(p.index, acts)
            assert is_success
        if self.verbose:
            print self.board.tiles
            print "P({0}): {1} {2}".format(p.name, act_name, card if card is not None else str(acts))
            print Ps.player_status(p.index)

    def game_is_over(self):
        return self.board.tiles.sum() == 0

    def end_game(self, Ps, i, max_iters_reached=False, print_end_status=True,):
        if print_end_status:
            print "Game ended after {0} turns, ".format(i+1),
        score = '-'.join([str(v) for v in Ps.vps.values()])
        winner = None
        if self.game_is_win(Ps):
            status = "WIN"
            pi = Ps.player_with_most_vps()
            if pi is None:
                status = "TIE"
                if print_end_status:
                    print "Game TIED {0}!".format(score)
            else:
                if print_end_status:
                    print "Game WON {1} by Player {0}.".format(pi.name, score)
                winner = pi.name
        else:
            status = "LOSS"
            if print_end_status:
                print "Game LOST {0}.".format(score)
        if print_end_status:
            for i,c in Ps.huts.iteritems():
                print "    P{0}: {1} huts".format(i,c)
            for i,c in Ps.stations.iteritems():
                print "    P{0}: {1} stations".format(i,c)
        if max_iters_reached:
            status = "MAX_ITERS"
        return status, winner

    def game_is_win(self, Ps):
        return sum(Ps.vps.values()) >= self.vps_to_win

class Board:
    def __init__(self, (nrows, ncols), obj_cost, ntrees=15):
        """
        costs = {name: cost, ...}
        """
        self.nrows = nrows
        self.ncols = ncols
        self.ntrees_init = ntrees
        self.obj_cost = obj_cost
        self.obj_add = {"hut": -1}
        self.init_board()

    def init_board(self):
        self.tiles = self.init_tiles(self.nrows, self.ncols, self.ntrees_init)
        self.grid = self.init_grid(self.tiles)

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
        for nm, pos in objs:
            (i,j) = pos
            is_success = is_success and (self.grid[i,j] == 0)
            if nm in self.obj_add:
                self.grid[i,j] = self.obj_add[nm]
            else:
                self.grid[i,j] = player_index # e.g. 1,2,...
        return is_success

    def valid_object_inds(self):
        inds = [(i,j) for i in xrange(self.grid.shape[0]) for j in xrange(self.grid.shape[1])]
        return [(i,j) for (i,j) in inds if self.grid[i,j] == 0]

    def valid_curse_inds(self):
        return [(r,c, self.tiles[r,c]) for r in xrange(self.tiles.shape[0]) for c in xrange(self.tiles.shape[1]) if self.tiles[r,c] > 0]

    def add_random_garden(self, hut_multiplier=2):
        ind = self.get_tree_ind(self.tiles, n=1)
        r,c = ind[0]
        
        # check for hut nearby
        inds = self.grids_touching_tile(r,c)
        v = len([1 for ro,co in inds if self.grid[ro,co] == self.obj_add["hut"]])
        self.tiles[r,c] += (hut_multiplier*v+1)

    def curse_tile(self, (r, c), n):
        assert n >= 1
        assert self.tiles[r,c] >= n
        self.tiles[r,c] -= n

        # check for VPs
        cs = {} # counts of adjacent objects, per player
        inds = self.grids_touching_tile(r,c)
        for ro,co in inds:
            if self.grid[ro,co] > 0:
                pind = int(self.grid[ro,co])
                if pind not in cs:
                    cs[pind] = 0
                cs[pind] += 1

        # 2nd val notifies if we need to add a curse
        return cs, self.tiles[r,c] == 0

class Deck:
    def __init__(self, card_info):
        """
        cards = [(name, count), ...]
        """
        self.card_info = card_info
        self.card_names = self.card_info.keys()
        self.init_deck()

    def init_deck(self):
        deck = []
        for (name, count) in self.card_info.iteritems():
            deck.extend([name]*count)
        np.random.shuffle(deck)
        self.deck = deck
        self.discard = []

    def draw(self):
        if len(self.deck) == 0:
            self.shuffle()
        card = self.deck.pop()
        self.discard.append(card)
        return card

    def shuffle(self):
        assert len(self.deck) == 0
        self.deck = [x for x in self.discard]
        self.discard = []
        np.random.shuffle(self.deck)
        # print collections.Counter(self.deck)
