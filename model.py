import numpy as np

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
        for i in xrange(self.max_nturns):
            if self.game_is_over():
                self.end_game(players)
                return
            p = players[i % len(players)]
            self.next_turn(p, players)

    def next_turn(self, p, players):
        a = p.choose_action(self)
        assert a in self.valid_actions
        if a == "draw":
            card = self.deck.draw()
            if card == "garden":
                self.board.random_garden_tile()
            elif card == "curse":
                (i,j,n) = p.choose_curse_tile(self)
                cs = self.board.curse_tile((i,j), n)
                for (pc,c) in cs:
                    p.vps += c
                p.money += int(n > 1) + n
        elif a == "buy":
            objs = p.buy_objects(self)
            is_success = self.board.add_objects(objs, p.index)
            cost = sum([self.board.obj_cost[nm] for nm,pos in objs])
            assert p.money >= cost
            p.money -= cost
            assert is_success

    def game_is_over(self):
        return self.board.tiles.sum() == 0

    def end_game(self, players):
        if self.game_is_win():
            p = self.winning_player(players)
        else:
            pass

    def game_is_win(self, players):
        return sum([p.vps for p in players]) >= self.vps_to_win

    def winning_player(self):
        return players[np.argmax([p.vps for p in players])]

class Board:
    def __init__(self, (nrows, ncols), obj_cost):
        """
        costs = {name: cost, ...}
        """
        self.nrows = nrows
        self.ncols = ncols
        self.obj_cost = obj_cost
        self.tiles = self.init_tiles(self.nrows, self.ncols)
        self.grid = self.init_grid(self.tiles)
        self.obj_add = {"hut": "H", "station": "S{0}"}
        assert set(self.obj_names.keys()) == set(self.obj_cost.keys())

    def init_tiles(self, nrows, ncols):
        pass

    def init_grid(self, tiles):
        pass

    def grids_touching_tile(self, i, j):
        pass

    def tiles_touching_grid(self, i, j):
        pass

    def add_objects(self, objs, player_index):
        is_success = all([nm in self.obj_cost for nm,pos in objs])
        for nm, (i,j) in objs:
            is_success = is_success and (self.grid[i,j] == 0)
            self.grid[i,j] = self.obj_names[nm].format(player_index) # e.g. "S1", "S2", ...
        return is_success

    def random_garden_tile(self):
        pass

    def curse_tile(self, (i, j), n):
        cs = [] # counts of adjacent objects, per player
        return cs

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

class Player:
    def __init__(self, index):
        self.vps = 0
        self.money = 0
        self.index = index

    def choose_action(self, game):
        return "draw"

    def choose_curse_tile(self):
        i = 0
        j = 0
        n = 1
        return (i,j,n)

    def buy_objects(self):
        objs = [] # (nm,(i,j)), ...
        return objs

    def buy_hut(self):
        pass

    def buy_station(self):
        pass

def play_game():
    board = Board((6,6), {"hut": 2, "station": 3})
    Deck = Deck(["garden", 5, "curse", 3])
    g = Game(board, deck)
    ps = [Player(1), Player(2)]
    g.play(ps)

if __name__ == '__main__':
    play_game()
