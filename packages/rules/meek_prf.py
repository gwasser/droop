'''
Count election using PRF Meek Reference STV

copyright 2010 by Jonathan Lundell
'''

from _rule import ElectionRule

class Rule(ElectionRule):
    '''
    Rule for counting PRF Meek Reference STV
    
    Parameters: none
    '''
    
    omega = None   # epsilon for terminating iteration
    _o = 4         # omega = 1/10^o

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return 'meek-prf'

    @classmethod
    def helps(cls, helps, name):
        "add help string for meek-prf"
        h =  "%s is the PR Foundation's Meek Reference STV.\n" % name
        h += '\nThere are no options.\n'
        h += '  arithmetic: fixed, 6-digit precision\n'
        h += '  omega=4 (iteration limit such that an interation is terminated\n'
        h += '    when surplus < 1/10^omega)\n'
        helps[name] = h
        
    @classmethod
    def options(cls, options=dict()):
        "override options"
        
        options['arithmetic'] = 'fixed' # fixed-point arithmetic
        options['precision'] = 6        # 6-digit precision
        options['omega'] = 4            # 1/10^4 omega
        return options

    @classmethod
    def info(cls):
        "return an info string for the election report"
        return "PR Foundation Meek Reference (omega = 1/10^%d)" % (cls._o)

    @classmethod
    def reportMode(cls):
        "how should this election be reported? meek or wigm"
        return 'meek'

    #########################
    #
    #   Main Election Counter
    #
    #########################
    @classmethod
    def count(cls, E):
        "count the election"
        
        #  local support functions
        #
        def countComplete():
            "test for end of count"
            return C.nHopeful <= E.seatsLeftToFill() or E.seatsLeftToFill() <= 0

        def hasQuota(E, candidate):
            '''
            Determine whether a candidate has a quota (ie, is elected).
            '''
            return candidate.vote >= E.R.quota
    
        def calcQuota(E):
            '''
            Calculate quota.
            '''
            return E.R.votes / E.V(E.electionProfile.nSeats+1) + E.V.epsilon
    
        def breakTie(E, tied, purpose=None, strong=True):
            '''
            break a tie
            
            purpose must be 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to eliminate. 
            
            Set strong to False to indicate that weak tiebreaking should be
            attempted, if relevant. Otherwise the tie is treated as strong.
            
            Not all tiebreaking methods will care about 'purpose' or 'strength',
            but the requirement is enforced for consistency of interface.
            '''
            assert purpose in ('surplus', 'elect', 'defeat')
            if not tied:
                return None
            if len(tied) == 1:
                return tied[0]
            if len(tied) > 1:
                t = tied[0]  # TODO: real tiebreaker
                s = 'Break tie (%s): [' % purpose
                s += ", ".join([c.name for c in tied])
                s += '] -> %s' % t.name
                R.log(s)
                return t

        #  iterateStatus constants
        #
        IS_none = None
        IS_omega = 1
        IS_elected = 2
        IS_stable = 3

        def iterate():
            "Iterate until surplus is sufficiently low"
            iStatus = IS_none
            lastsurplus = V(E.nBallots)
            while True:
                #
                #  distribute vote for each ballot
                #  and add up vote for each candidate
                #
                for c in C.hopefulOrElected:
                    c.vote = V0
                R.residual = V0
                for b in R.ballots:
                    b.weight = V1
                    b.residual = V(b.multiplier)
                    for c in b.ranking:
                        #
                        #  distribute surpluses
                        #
                        #  kv = w*kf rounded up * m     keep vote
                        #  w -= w*kf rounded up         new weight
                        # 
                        kw = V.mul(b.weight, c.kf, round='up')  # keep weight
                        kv = kw * b.multiplier  # exact
                        c.vote += kv
                        b.weight -= kw
                        b.residual -= kv  # residual value of ballot
                        #
                        if b.weight <= V0:
                            break
                    R.residual += b.residual    # residual for round
                R.votes = V0
                for c in C.hopefulOrElected:
                    R.votes += c.vote            # find sum of all votes

                #  D.3. update quota
                #
                R.quota = calcQuota(E)
                
                #  D.4. find winners
                #
                for c in [c for c in C.hopeful if hasQuota(E, c)]:
                    C.elect(c)
                    iStatus = IS_elected
                    
                    #  D.5. test for election complete
                    #
                    #if countComplete():
                    #    return IS_complete, None
                
                if iStatus == IS_elected:
                    return IS_elected, None
    
                #  D.6. calculate total surplus
                #
                surplus = V0
                for c in C.elected:
                    surplus += c.vote - R.quota
                R.surplus = surplus # for reporting
                
                #  D.7. test iteration complete
                #
                if surplus <= Rule.omega:
                    return IS_omega, None
                if surplus >= lastsurplus:
                    R.log("Stable state detected (%s)" % surplus) # move to caller?
                    return IS_stable, None
                lastsurplus = surplus
                    
                #  D.8. update keep factors
                #
                for c in C.elected:
                    c.kf = V.div(V.mul(c.kf, R.quota, round='up'), c.vote, round='up')
            
        #########################
        #
        #   Initialize Count
        #
        #########################
        V = E.V    # arithmetic value class
        V0 = E.V0  # constant zero
        V1 = E.V1  # constant one

        #  set omega: 1/10**4
        #
        cls.omega = V(1) / V(10**cls._o)

        E.R0.votes = V(E.electionProfile.nBallots)
        E.R0.quota = calcQuota(E)
        R = E.R0
        C = R.C   # candidate state
        for c in E.withdrawn:
            c.kf = V0
        for c in C.hopeful:
            c.kf = V1    # initialize keep factors
            c.vote = V0  # initialize round-0 vote
        for b in R.ballots:
            if b.topCand:
                b.topCand.vote += V(b.multiplier)  # count first-place votes for round 0 reporting

        while not countComplete():

            #  B. next round
            #
            R = E.newRound()
            C = R.C   # candidate state

            #  C. iterate
            #     next round if iteration elected a candidate
            #
            iterationStatus, batch = iterate()
            if iterationStatus == IS_elected:
                continue

            #  D. defeat candidate with lowest vote
            #
            #  find candidate(s) with lowest vote
            #
            low_vote = R.quota
            low_candidates = []
            for c in C.hopeful:
                if V.equal_within(c.vote, low_vote, cls.omega):
                    low_candidates.append(c)
                elif c.vote < low_vote:
                    low_vote = c.vote
                    low_candidates = [c]

            #  defeat candidate with lowest vote, breaking tie if necessary
            #
            if low_candidates:
                low_candidate = breakTie(E, low_candidates, 'defeat')
                if iterationStatus == IS_omega:
                    C.defeat(low_candidate, msg='Defeat (surplus %s < omega)' % V(R.surplus))
                else:
                    C.defeat(low_candidate, msg='Defeat (stable surplus %s)' % V(R.surplus))
                low_candidate.kf = V0
                low_candidate.vote = V0
        
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.hopeful.copy():
            if C.nElected < E.electionProfile.nSeats:
                C.elect(c, msg='Elect remaining')
            else:
                C.defeat(c, msg='Defeat remaining')
                c.kf = V0
                c.vote = V0