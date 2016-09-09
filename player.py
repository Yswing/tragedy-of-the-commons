import random

class DefaultPlayer:
    def __init__(self, index):
        self.vps = 0 # should be read-only
        self.money = 0 # should be read-only
        self.index = index
        self.purchases = []

    def take_action(self, board):
        if any([self.money >= v for v in board.obj_cost.values()]):
            return "buy", self.buy_objects(board)
        else:
            return "draw", self.choose_curse_tile(board)

    def choose_curse_tile(self, board):
        options = board.valid_curse_inds()
        max_score = 0
        (r,c) = (0,0)
        for rc,cc,nts in options:
            inds = board.grids_touching_tile(rc,cc)
            v = len([1 for ro,co in inds if self.index in self.grid[ro,co]])
            if v > 0 and v*nts > max_score:
                r = rc
                c = cc
                max_score = v*nts
        if max_score == 0:
            top_opts = [(r,c,nts) for r,c,nts in options if nts > 1]
            if top_opts:
                r,c,nts = random.choice(top_opts)
            else:
                r,c,nts = random.choice(options)
        n = max(1, board.tiles[r,c]-1)
        return r,c,n

    def get_most_valuable_empty_inds(self, board):
        """
        should also account for whether a tile already has a hut nearby
        """
        vals = []
        max_val = 0
        max_ind = [0,0]
        backup_ind = []
        inds = board.valid_object_inds()
        for (i,j) in inds:
            inds_t = board.tiles_touching_grid(i,j)
            v = np.sum([board.tiles[x,y] for (x,y) in inds_t])
            vals.append((i,j,v))
            if v > max_val:
                max_ind = [i,j]
                max_val = v
            else:
                backup_ind = [i,j]
        if max_val == 0:
            max_ind = backup_ind
            if len(backup_ind) == 0:
                return None
        return max_ind

    def choose_hut_pos(self, board):
        return self.get_most_valuable_empty_inds(board)

    def choose_station_pos(self, board):
        return self.get_most_valuable_empty_inds(board)

    def buy_object(self, board, money, cost_of_hut, cost_of_log):
        if money >= cost_of_log and money >= cost_of_hut:
            if not self.purchases:
                name = "hut"
            elif "hut" == self.purchases[-1][0]:
                name = "station"
            else:
                name = "hut"
        elif money >= cost_of_log:
            name = "station"
        elif money >= cost_of_hut:
            name = "hut"
        else:
            assert False
        if name == "hut":
            pos = self.choose_hut_pos(board)
        elif name == "station"
            pos = self.choose_station_pos(board)
        else:
            assert False
        return name, pos

    def buy_objects(self, board):
        cost_of_hut = board.obj_cost["hut"]
        cost_of_log = board.obj_cost["station"]
        objs = [] # (nm,(i,j)), ...
        cur_money = self.money
        while cur_money >= min(cost_of_hut, cost_of_log):
            name, pos = self.buy_object(board, cur_money, cost_of_hut, cost_of_log)
            assert name in ["hut", "station"]
            if name == "hut":
                cur_money -= cost_of_hut
            elif name == "station":
                cur_money -= cost_of_log
            self.purchases.append((name, pos))
            objs.append((name, pos))
        return objs
