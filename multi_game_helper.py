import os
import contextlib
import matplotlib
import re
import itertools
from engine import Game
from tqdm import tqdm
import matplotlib.pyplot as plt


NUM_ITERS = 50
results = []

for _ in tqdm(range(NUM_ITERS)):
	#Run Engine with print() output suppressed
	with open(os.devnull, 'w') as devnull:
		with contextlib.redirect_stdout(devnull):
			Game().run()

	#Get Last File Line
	with open('gamelog.txt') as f:
		for line in f:
			pass
		last_line = line

	#Parse Last File Line
	scores = re.findall(r'-?\d+', line)
	results.append({'A':int(scores[0]), 'B':int(scores[1])})

a_wins = sum(1 for x in results if x['A'] > x['B'])
b_wins = NUM_ITERS - a_wins

a_scores = [x['A'] for x in results]
plt.hist(a_scores, density=True, bins=50)
plt.savefig('hist_a.png')
# plt.show()

# plt.clf()

# b_scores = [x['B'] for x in results]
# plt.hist(b_scores, density=True, bins=50)
# plt.savefig('hist_b.png')


print(f"A won {a_wins} times. B won {b_wins} times.")