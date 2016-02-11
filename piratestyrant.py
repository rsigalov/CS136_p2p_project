#!/usr/bin/python

# This is a dummy peer that just illustrates the available information your peers 
# have available.

# You'll want to copy this file to AgentNameXXX.py for various versions of XXX,
# probably get rid of the silly logging messages, and then add more logic.

import random
import logging

from messages import Upload, Request
from util import even_split, proportional_split, mean
from peer import Peer

class PiratesTyrant(Peer):
    def post_init(self):
        print "post_init(): %s here!" % self.id
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"
        self.downloadRate = {}
        self.uploadRate = {}
        self.slots = {}
        self.downloadUploadRatio = {}
        self.bandwidthHistory = []
    
    def requests(self, peers, history):
        self.bandwidthHistory.append(self.up_bw)

        """
        peers: available info about the peers (who has what pieces)
        history: what's happened so far as far as this peer can see

        returns: a list of Request() objects

        This will be called after update_pieces() with the most recent state.
        """
        needed = lambda i: self.pieces[i] < self.conf.blocks_per_piece
        needed_pieces = filter(needed, range(len(self.pieces)))
        np_set = set(needed_pieces)  # sets support fast intersection ops.

        round = history.current_round()


        logging.debug("%s here: still need pieces %s" % (
            self.id, needed_pieces))

        logging.debug("%s still here. Here are some peers:" % self.id)
        for p in peers:
            logging.debug("id: %s, available pieces: %s" % (p.id, p.available_pieces))

        logging.debug("And look, I have my entire history available too:")
        logging.debug("look at the AgentHistory class in history.py for details")
        logging.debug(str(history))

        requests = []   # We'll put all the things we want here
        # Symmetry breaking is good...
        random.shuffle(needed_pieces)
        
        # Sort peers by id.  This is probably not a useful sort, but other 
        # sorts might be useful
        peers.sort(key=lambda p: p.id)
        # request all available pieces from all peers!
        # (up to self.max_requests from each)
        for peer in peers:
            av_set = set(peer.available_pieces)
            isect = av_set.intersection(np_set)
            n = min(self.max_requests, len(isect))
            # More symmetry breaking -- ask for random pieces.
            # This would be the place to try fancier piece-requesting strategies
            # to avoid getting the same thing from multiple peers at a time.
            for piece_id in random.sample(isect, n):
                # aha! The peer has this piece! Request it.
                # which part of the piece do we need next?
                # (must get the next-needed blocks in order)
                start_block = self.pieces[piece_id]
                r = Request(self.id, peer.id, piece_id, start_block)
                requests.append(r)

        return requests


    def uploads(self, requests, peers, history):
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """
        ##################################################################
        ########### updating d_js ########################################
        ##################################################################

        alpha = 0.2
        gamma = 0.1
        round = history.current_round()
        self.bandwidthHistory.append(self.up_bw)

        if round == 0:
            for peer in peers:
                self.downloadRate[peer.id] = 1
                self.uploadRate[peer.id] = 1
                self.slots[peer.id] = 4
                self.downloadUploadRatio[peer.id] = self.downloadRate[peer.id]/self.uploadRate[peer.id] 
        else:
            for peer in peers:
                for download in history.downloads[round-1]:
                    if peer.id == download.from_id:
                        self.downloadRate[peer.id] = download.blocks
                        if download.blocks == 0: print "!!!!!! %s uploaded %s block(s)" % (peer.id, download.blocks)
                        self.slots[peer.id] = mean(self.bandwidthHistory)/float(self.downloadRate[peer.id]) # Find how to find out max and min bw or infer from personal history
                        
                        if round >= 3:
                            peer_download = 0
                            for download2 in history.downloads[round-2]:
                                if peer.id == download2.from_id:
                                    for download3 in history.downloads[round-3]:
                                        if peer.id == download3.from_id:
                                            peer_download += 1
                            if peer_download > 0:
                                self.uploadRate[peer.id] *= 1 - gamma
                        break 
                    
                    if len(peer.available_pieces) > 0:
                        av_pieces = float(len(peer.available_pieces))
                        rnd = float(round)
                        slots = float(self.slots[peer.id])
                        self.downloadRate[peer.id] = av_pieces/(rnd * slots)
                        #self.downloadRate[peer.id] = float((len(peer.available_pieces)/float(round)))/float(self.slots[peer.id])
                        self.uploadRate[peer.id] *= 1 + alpha
                        if self.downloadRate[peer.id] == 0:
                            print str(peer.id) + ": " + str(peer.available_pieces)
                            print "Peer %s has %s available pieces" % (peer.id, len(peer.available_pieces))

        print "downloadUploadRatio"
        print self.downloadUploadRatio
        ########### updating current ratio ###############################

        if round == 0:
            for peer in peers:
                self.downloadUploadRatio[peer.id] = 1
        else:
            for peer in peers:
                self.downloadUploadRatio[peer.id] =  self.downloadRate[peer.id]/self.uploadRate[peer.id]   

        ###################################################################

        print "download rates"
        print self.downloadRate
        print "Upload rates"
        print self.uploadRate
        print "donwload upload ratio"
        print self.downloadUploadRatio
        print "slots"
        print self.slots

        
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
            uploads = []
        else:
            logging.debug("Still here: uploading to a random peer")
            # change my internal state for no reason
            self.dummy_state["cake"] = "pie"

        ########### Building upload list #################################

            sumUpload = 0
            chosen = {}
            downloadUploadRatio_tmp = {}
            
            # creating list with ratios for only peers in requests
            for request in requests:
                downloadUploadRatio_tmp[request.requester_id] = self.downloadUploadRatio[request.requester_id]
                print self.downloadUploadRatio[request.requester_id]

            while (sumUpload <= len(peers) and len(downloadUploadRatio_tmp) > 0):
                peer_id = max(downloadUploadRatio_tmp, key = downloadUploadRatio_tmp.get)
                chosen[peer_id] = downloadUploadRatio_tmp.pop(peer_id)
                sumUpload += self.uploadRate[peer_id]
                # print "sumUpload of %s" % (peer_id)
                # print sumUpload
                # print downloadUploadRatio_tmp[peer_id]
                # print self.uploadRate[peer_id]

            """ Calculate the total proportional BW allocated to other peers """
            totalUploadBW = 0
            for choice in chosen:
                totalUploadBW += chosen[choice]
                # print chosen[choice]

            """ Make each BW as a proportion of totalUploadBW """
            for choice in chosen:
                chosen[choice] = 100 * float(chosen[choice]) / float(totalUploadBW)

            # print "Vector of choices for this round:"
            # print chosen

            """ Now need to divide our BW as integers according to chosen vector """
            peerWeights = [value for (key, value) in sorted(chosen.items())]
            peerNames = sorted(chosen)

            # print "original chosen: %s" % (chosen)
            # print "names: %s" % (peerNames)
            # print "weights: %s" % (peerWeights)

            # request = random.choice(requests)
            # chosen = [request.requester_id]
            # Evenly "split" my upload bandwidth among the one chosen requester
            # bws = even_split(self.up_bw, len(chosen))

            bws = proportional_split(self.up_bw, peerWeights)

            # create actual uploads out of the list of peer ids and bandwidths
            uploads = [Upload(self.id, peer_id, bw)
                for (peer_id, bw) in zip(chosen, bws)]

            
        


        return uploads


