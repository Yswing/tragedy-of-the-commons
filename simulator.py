
# coding: utf-8

# the script simulate the tragedy of the commons

# In[7]:

import random
import numpy as np


# In[400]:

def get_tree_ind(tiles, n=1):
    row = np.random.randint(low=0, high=tiles.shape[0], size=(n,))
    col = np.random.randint(low=0, high=tiles.shape[1], size=(n,))
    return zip(row, col)

def init_board(n_tile_rows, n_tile_cols, n_trees_init):
    tiles = np.zeros([n_tile_rows,n_tile_cols])
    trees = get_tree_ind(tiles, n_trees_init)
    for (r,c) in trees:
        tiles[r,c] += 1
    return tiles

def print_deck_info(deck):
    ncs = len([1 for x in deck if x == 'curse'])
    ngs = len(deck) - ncs
    print "Distribution: {0} curses, {1} gardens".format(ncs, ngs)

def init_deck(n_curses, n_gardens):
    gardens = ["garden" for i in xrange(n_gardens)]
    curses = ["curse" for i in xrange(n_curses)]
    deck = gardens + curses
    np.random.shuffle(deck)
    return deck

def shuffle_deck(deck, discard):
    assert len(deck) == 0
    deck = [x for x in discard]
    discard = []
    np.random.shuffle(deck)
    return deck, discard

def take_card(deck, discard, is_verbose):
    if len(deck) == 0:
        if is_verbose:
            print "SHUFFLING."
        deck, discard = shuffle_deck(deck, discard)
    draw = deck.pop()
    discard.append(draw)
    return draw, deck, discard

def draw_garden(tiles, obj_tiles, money, vps, discard, player_ind, is_verbose):
    ind = get_tree_ind(tiles, n=1)
    r,c = ind[0]
    
    # check for hut nearby
    inds = objects_touching_inds((r,c), obj_tiles)
    v = len([1 for ro,co in inds if obj_tiles[ro,co] == HUT_VAL])
    
    tiles[r,c] += (v+1)
    action = "Garden ({0},{1}). Adding {2}".format(r,c, v+1)
    return tiles, discard, action, money, vps

def valid_curse_inds(tiles):
    return [(r,c,tiles[r,c]) for r in xrange(tiles.shape[0]) for c in xrange(tiles.shape[1]) if tiles[r,c] > 0]
    
def choose_tree_ind(tiles, obj_tiles, player_ind):
    options = valid_curse_inds(tiles)
    # find tile with most trees and also with a logging station
    max_score = 0
    r = 0
    c = 0
    for rc,cc,nts in options:
        inds = objects_touching_inds((rc,cc), obj_tiles)
        v = len([1 for ro,co in inds if obj_tiles[ro,co] == LOG_VAL+player_ind])
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
    n = max(1, tiles[r,c]-1)
    return r,c,n

def draw_curse(tiles, obj_tiles, money, vps, discard, player_ind, is_verbose):
    r,c,n = choose_tree_ind(tiles, obj_tiles, player_ind)
    assert tiles[r,c] >= n
    assert n >= 1
    tiles[r,c] -= n
    action = "curse. Extracting {2} from ({0},{1})".format(r,c,n)
    
    if tiles[r,c] == 0:
        discard.append("curse")
        action += " and cursing"
        
    profit = n
    if n > 1:
        profit += 1
    money += profit
    action += ". Made ${0}".format(profit)
    
    # check for VPs
    inds = objects_touching_inds((r,c), obj_tiles)
    oldvps = vps
    for ro,co in inds:
        if obj_tiles[ro,co] >= LOG_VAL:
            vps[int(obj_tiles[ro,co]-LOG_VAL)] += 1
    if (np.array(vps) - np.array(oldvps)).sum() > 0:
        action += ". Earned {0} VP(s)".format((np.array(vps) - np.array(oldvps)))
#     nlgs = len([1 for ro,co in inds if obj_tiles[ro,co] == LOG_VAL+player_ind])
#     if nlgs > 0:
#         vps += n*nlgs
#         action += ". Earned {0} VP(s)".format(vps)

    return tiles, discard, action, money, vps


# In[401]:

HUT_VAL = 1
LOG_VAL = 2

def init_object_tiles(tiles):
    # ignoring edge object tiles
    n_rows = 2*(tiles.shape[0]-1)
    n_cols = tiles.shape[1]-1
    return np.zeros([n_rows,n_cols])

def tiles_touching_inds(r,c):
    # no boundary checks because we're ignoring edge object tiles
    inds = []
    tr = r/2
    tc = c
    if r % 2 == 0:
        inds = [(tr,tc), (tr,tc+1), (tr+1,tc)]
    else:
        inds = [(tr+1,tc+1), (tr,tc+1), (tr+1,tc)]
    return inds

def objects_touching_inds((r,c), obj_tiles):
    ro = 2*r
    co = c
    rs = [ro-2, ro-1, ro-1, ro,   ro, ro+1]
    cs = [co,   co-1, co,   co-1, co, co-1]
    inds = [(r,c) for r,c in zip(rs,cs) if 0 <= r < obj_tiles.shape[0] and 0 <= c < obj_tiles.shape[1]]
    return inds

def get_most_valuable_empty_inds(tiles, obj_tiles):
    """
    should also account for whether a tile has a hut nearby
    """
    vals = []
    max_val = 0
    max_ind = [0,0]
    backup_ind = []
    inds = [(i,j) for i in xrange(obj_tiles.shape[0]) for j in xrange(obj_tiles.shape[1])]
    for (i,j) in inds:
#         print (i,j,obj_tiles[i,j])
        if obj_tiles[i,j] > 0:
            continue
        inds_t = tiles_touching_inds(i,j)
        v = np.sum([tiles[x,y] for (x,y) in inds_t])
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

def place_hut(tiles, obj_tiles, money, cost_of_hut, player_ind):
    ind = get_most_valuable_empty_inds(tiles, obj_tiles)
    if ind is None:
        return "ERROR", money, obj_tiles
    assert(obj_tiles[ind[0],ind[1]] == 0)
    obj_tiles[ind[0],ind[1]] = HUT_VAL
    money -= cost_of_hut
    action = "added hut to ({0},{1})".format(ind[0], ind[1])
    return action, money, obj_tiles

def place_log(tiles, obj_tiles, money, cost_of_log, player_ind):
    ind = get_most_valuable_empty_inds(tiles, obj_tiles)
    if ind is None:
        return "ERROR", money, obj_tiles
    assert(obj_tiles[ind[0],ind[1]] == 0)
    obj_tiles[ind[0],ind[1]] = LOG_VAL+player_ind
    money -= cost_of_log
    action = "added log to ({0},{1})".format(ind[0], ind[1])
    return action, money, obj_tiles

def buy_and_place_items(actions, money, cost_of_hut, cost_of_log, tiles, obj_tiles, player_ind):
    if money >= cost_of_log and money >= cost_of_hut:
        if not actions:
            return place_hut(tiles, obj_tiles, money, cost_of_hut, player_ind)
        elif "hut" in actions[-1]:
            return place_log(tiles, obj_tiles, money, cost_of_log, player_ind)
        else:
            return place_hut(tiles, obj_tiles, money, cost_of_hut, player_ind)
    elif money >= cost_of_log:
        return place_log(tiles, obj_tiles, money, cost_of_log, player_ind)
    elif money >= cost_of_hut:
        return place_hut(tiles, obj_tiles, money, cost_of_hut, player_ind)
    return "done", money, obj_tiles

def draw_card(deck, discard, tiles, obj_tiles, money, vps, player_ind, is_verbose):
    draw, deck, discard = take_card(deck, discard, is_verbose)
    if draw == 'curse':
        tiles, discard, action, money, vps = draw_curse(tiles, obj_tiles, money, vps, discard, player_ind, is_verbose)
    elif draw == 'garden':
        tiles, discard, action, money, vps = draw_garden(tiles, obj_tiles, money, vps, discard, player_ind, is_verbose)
    action = "Player {0} drew ".format(player_ind) + action
    return tiles, deck, discard, action, money, vps

def choose_action(money, vps, cost_of_hut, cost_of_log, tiles, obj_tiles, deck, discard, player_ind, is_verbose):
    """
    draw if not enough money
    otherwise, buy as many huts and logs as possible,
        alternating between the two if you can buy multiples
    """
    # check if any room on board for huts/logs
    must_draw = len([x for x in obj_tiles.flatten() if x == 0]) == 0
#     print obj_tiles.flatten()
    
    if must_draw or money < np.min([cost_of_log, cost_of_hut]):
        tiles, deck, discard, action, money, vps = draw_card(deck, discard, tiles, obj_tiles, money, vps, player_ind, is_verbose)
    else:
        actions = []
        # while not if!
        max_plays = 5
        cp = 0
        while money >= np.min([cost_of_log, cost_of_hut]) and cp < max_plays:
            cp += 1
            action, money, obj_tiles = buy_and_place_items(actions, money, cost_of_hut, cost_of_log, tiles, obj_tiles, player_ind)
            actions.append(action)
        action = 'Player {0} '.format(player_ind) + ', '.join(actions)
    return action, money, vps, tiles, obj_tiles, deck, discard


# In[363]:

xs = np.array([(1,2,3), (4,5,6), (2,2,4)])
print xs.flatten()


# In[433]:

n_tile_rows = 6
n_tile_cols = 6
n_trees_init = 10
n_gardens = 5
n_curses = 3

# n_players = 2
cost_of_hut = 2
cost_of_log = 3

n_games = 1000
nplays = []
max_nplays = 200
is_verbose = n_games <= 2
all_vps = []
all_maxms = []

for i in xrange(n_games):
    if is_verbose:
        print '================'
    
    deck = init_deck(n_curses, n_gardens)
    discard = []
    tiles = init_board(n_tile_rows, n_tile_cols, n_trees_init)
    obj_tiles = init_object_tiles(tiles)

    c = 0
    moneys = [0,0]
    vps = [0,0]
    max_moneys = [0,0]
    while tiles.sum() > 0 and c < max_nplays:
        if len(deck) == 0 and is_verbose:
            print_deck_info(discard)
        if is_verbose:
            print tiles
        
        player_ind = c % 2
        money = moneys[player_ind]
#         vps = avps[player_ind]
        action, money, avps, tiles, obj_tiles, deck, discard = choose_action(money, vps, cost_of_hut, cost_of_log, tiles, obj_tiles, deck, discard, player_ind, is_verbose)
        moneys[player_ind] = money
        
        if money > max_moneys[player_ind]:
            max_moneys[player_ind] = money
        
#         avps[player_ind] = vps
        
        if is_verbose:
            print action
        c += 1
        
        if is_verbose:
            print '--------------'    
    if is_verbose:
        print "Game ended after {0} plays and {1} VPs".format(c, vps)
    nplays.append(c)
    all_vps.append(vps)
    all_maxms.append(max_moneys)
    if is_verbose:
        print '================'

print "Play counts: {0}".format(np.percentile(nplays, [0, 10, 50, 90, 100]))

print "Max money P0: {0}".format(np.percentile(np.array(all_maxms)[:,0], [0, 10, 50, 90, 100]))
print "Max money P1: {0}".format(np.percentile(np.array(all_maxms)[:,1], [0, 10, 50, 90, 100]))

print "VPs total: {0}".format(np.percentile(np.array(all_vps).sum(axis=1), [0, 10, 50, 90, 100]))
print "VPs P0: {0}".format(np.percentile(np.array(all_vps)[:,0], [0, 10, 50, 90, 100]))
print "VPs P1: {0}".format(np.percentile(np.array(all_vps)[:,1], [0, 10, 50, 90, 100]))
print "mean VPs: {0}".format(np.mean(all_vps, axis=0))

print "corrs total={0}, P0={1}, P1={2}".format(np.corrcoef(nplays, np.array(all_vps).sum(axis=1))[0,1], np.corrcoef(nplays, np.array(all_vps)[:,0])[0,1], np.corrcoef(nplays, np.array(all_vps)[:,1])[0,1])

print "{0} games did not complete".format(len([x for x in nplays if x == max_nplays]))



# In[441]:

np.sort(all_maxms, axis=0)[:,0]


# In[422]:

np.array(all_vps).sum(axis=1)


# In[ ]:



