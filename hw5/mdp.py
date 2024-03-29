

# Components of a darts player. #

# 
 # Modify the following functions to produce a player.
 # The default player aims for the maximum score, unless the
 # current score is less than or equal to the number of wedges, in which
 # case it aims for the exact score it needs.  You can use this
 # player as a baseline for comparison.
 #

from random import *
import throw
import darts

# make pi global so computation need only occur once
PI = {}
EPSILON = .001
T_CACHE = {}

# actual
def start_game(gamma):

  infiniteValueIteration(gamma)
  #for ele in PI:
    #print "score: ", ele, "; ring: ", PI[ele].ring, "; wedge: ", PI[ele].wedge
  
  return PI[throw.START_SCORE]

def get_target(score):

  return PI[score]

# define transition matrix/ function
def T(a, s, s_prime):
  # takes an action a, current state s, and next state s_prime
  # returns the probability of transitioning to s_prime when taking action a in state s
  if (T_CACHE.has_key((a,s,s_prime))):
    return T_CACHE[(a,s,s_prime)]

  def prob(i):
    if i == 0:
      return .4
    if abs(i) == 1:
      return .2
    if abs(i) == 2:
      return .1

  # Useful local variables
  diff = s - s_prime
  wedge_index = throw.wedges.index(a.wedge)

  # Set ring
  for r in [-2,-1,0,1,2]:
    ring = abs(a.ring+r)
    if ring > 7:
      ring = 7
    # Set wedge
    for w in [-2,-1,0,1,2]:
      wedge = throw.wedges[(wedge_index+w) % len(throw.wedges)]
      # Get score
      score = throw.location_to_score(
        throw.location(ring, wedge))
      if score == diff:
        ret = prob(r) * prob(w)
        T_CACHE[(a,s,s_prime)] = ret
        return ret
  return 0.


def infiniteValueIteration(gamma):
  # takes a discount factor gamma and convergence cutoff epislon
  # returns

  V = {}
  Q = {}
  V_prime = {}
  
  states = darts.get_states()
  actions = darts.get_actions()

  notConverged = True

  # intialize value of each state to 0
  for s in states:
    V[s] = 0
    Q[s] = {}

  # until convergence is reached
  while notConverged:

    # store values from previous iteration
    for s in states:
      V_prime[s] = V[s]

    # update Q, pi, and V
    for s in states:
      for a in actions:

        # given current state and action, sum product of T and V over all states
        summand = 0
        for s_prime in states:
          summand += T(a, s, s_prime)*V_prime[s_prime]

        # update Q
        Q[s][a] = darts.R(s, a) + gamma*summand

      # given current state, store the action that maximizes V in pi and the corresponding value in V
      PI[s] = actions[0]
      V[s] = Q[s][PI[s]]
      for a in actions:
        if V[s] <= Q[s][a]:
          V[s] = Q[s][a]
          PI[s] = a

    notConverged = False
    for s in states:
      if abs(V[s] - V_prime[s]) > EPSILON:
        notConverged = True
        
  
