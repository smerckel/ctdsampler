import multiprocessing as mp
import sys
sys.path.insert(0, ".")

import ctdsampler.graphs as graphs
import ctdsampler.scripts as scripts


if __name__ == '__main__':
    mp.set_start_method('spawn')
    graph = graphs.Graph()
    scripts.main(graph)







