#!/usr/bin/python

# This is a dummy peer that just illustrates the available information your peers 
# have available.

# You'll want to copy this file to AgentNameXXX.py for various versions of XXX,
# probably get rid of the silly logging messages, and then add more logic.

import random
import logging

from messages import Upload, Request
from util import even_split
from peer import Peer

class PiratesStd(Peer):
    def post_init(self):
        print "post_init(): %s here!" % self.id
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"
        self.current_opt_unchock = ""
    
    def requests(self, peers, history):
        """
        peers: available info about the peers (who has what pieces)
        history: what's happened so far as far as this peer can see

        returns: a list of Request() objects

        This will be called after update_pieces() with the most recent state.
        """

        needed = lambda i: self.pieces[i] < self.conf.blocks_per_piece
        needed_pieces = filter(needed, range(len(self.pieces)))
        np_set = set(needed_pieces) # sets support fast intersection ops.
        #logging.debug(np_set)


        #logging.debug("%s here: still need pieces %s" % (
        #    self.id, needed_pieces))

        #logging.debug("%s still here. Here are some peers:" % self.id)
        #for p in peers:
        #    logging.debug("id: %s, available pieces: %s" % (p.id, p.available_pieces))

        #logging.debug("And look, I have my entire history available too:")
        #logging.debug("look at the AgentHistory class in history.py for details")
        #logging.debug(str(history))

        requests = []   # We'll put all the things we want here
        # Symmetry breaking is good...
        # random.shuffle(needed_pieces)
        
        # Sort peers by id.  This is probably not a useful sort, but other 
        # sorts might be useful
        # peers.sort(key=lambda p: p.id)
        # request all available pieces from all peers!
        # (up to self.max_requests from each)

        av_dict = {}

        for i in np_set:
            av_dict[i] = 0
            for peer in peers:
                if (i in peer.available_pieces):
                    av_dict[i] += 1

        # print "needed pieces with availibility" + str(av_dict)

        for peer in peers:
            av_dict_tmp = av_dict.copy()
            av_set = set(peer.available_pieces)
            isect = av_set.intersection(np_set)
            n = min(self.max_requests, len(isect))

            """    if piece_id in av_set:"""
            while n > 0:
                piece_id = min(av_dict_tmp, key = av_dict.get)
                av_dict_tmp.pop(piece_id)
                if piece_id in av_set:
                    start_block = self.pieces[piece_id]
                    r = Request(self.id, peer.id, piece_id, start_block)
                    requests.append(r)
                    n -= 1
                if len(av_set) == 0:
                    break

        print history


        return requests

    def uploads(self, requests, peers, history):
        
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """

        round = history.current_round()
        #logging.debug("%s again.  It's round %d." % (
        #    self.id, round))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
        else:

##################################################################
########## Implementing recipocation #############################
##################################################################
            
            S = 4 # Upload slots
            request_bwd_history = {}
            chosen = []

            logging.debug("Requests, all:")
            logging.debug(requests)

            for request in requests:
                request_bwd_history[request.requester_id] = 0
            
            if round >= 1:
                for download in history.downloads[round-1]:
                    if download.from_id in request_bwd_history:
                        request_bwd_history[download.from_id] += download.blocks

            if round >= 2:
                for download in history.downloads[round-2]:
                    if download.from_id in request_bwd_history:
                        request_bwd_history[download.from_id] += download.blocks

            for i in range(0, S - 2):
                if len(request_bwd_history) > 0:
                    peer_id = min(request_bwd_history, key = request_bwd_history.get)
                    request_bwd_history.pop(peer_id)
                    chosen.append(peer_id)
                #if len(request_bwd_history) == 0:
                #    chosen.append(random.choice(request_bwd_history.keys()))

################################################################



################################################################
########## Implementing optimistic unchocking ##################
################################################################

            if (round % 3 == 0 and len(request_bwd_history) > 0):
                new_opt_unchock = random.choice(request_bwd_history.keys())
                chosen.append(new_opt_unchock)
                self.current_opt_unchock = new_opt_unchock
            else:
                chosen.append(self.current_opt_unchock)       


#############################################################

            # request = random.choice(requests)
            # chosen = [request.requester_id]
            # Evenly "split" my upload bandwidth among the one chosen requester
            bws = even_split(self.up_bw, len(chosen))

            # print bws 
            # print len(chosen)

        # create actual uploads out of the list of peer ids and bandwidths
        uploads = [Upload(self.id, peer_id, bw)
                   for (peer_id, bw) in zip(chosen, bws)]
            
        return uploads
