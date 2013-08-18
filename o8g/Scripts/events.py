    # Python Scripts for the Android:Netrunner LCG definition for OCTGN
    # Copyright (C) 2012  Konstantine Thoukydides

    # This python script is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with this script.  If not, see <http://www.gnu.org/licenses/>.

###==================================================File Contents==================================================###
# This file contains the basic table actions in ANR. They are the ones the player calls when they use an action in the menu.
# Many of them are also called from the autoscripts.
###=================================================================================================================###

import re
import collections
import time

flipBoard = 1 # If True, it signifies that the table board has been flipped because the runner is on the side A
ds = None # The side of the player. 'runner' or 'corp'
flipModX = 0
flipModY = 0

def chkTwoSided():
   if not table.isTwoSided(): information(":::WARNING::: This game is designed to be played on a two-sided table. Things will be extremely uncomfortable otherwise!! Please start a new game and make sure  the appropriate button is checked")

def checkDeck(player,groups):
   debugNotify(">>> checkDeck(){}".format(extraASDebug())) #Debug
   #confirm("raw groups = {}".format(groups))
   #confirm("group names= {}".format([g.name for g in groups]))
   if player != me: return # We only want the owner of to run this script
   mute()
   global totalInfluence, Identity, ds
   notify (" -> Checking deck of {} ...".format(me))
   ok = True
   group = me.piles['R&D/Stack']
   ds = None
   for card in me.hand:
      if card.Type != 'Identity':
         whisper(":::Warning::: You are not supposed to have any non-Identity cards in your hand when you start the game")
         card.moveToBottom(me.piles['R&D/Stack'])
         continue
      else:
         ds = card.Side.lower()
         storeSpecial(card)
         Identity = card
         me.setGlobalVariable('ds', ds)
   debugNotify("About to fetch Identity card", 4) #Debug
   if not Identity: 
      delayed_whisper(":::ERROR::: Please Reset and load a deck with an Identity included. Aborting!")
      return
   loDeckCount = len(group)
   debugNotify("About to check Identity min deck size.", 4) #Debug
   if loDeckCount < num(Identity.Requirement): # For identities, .Requirement is the card minimum they have.
      ok = False
      notify ( ":::ERROR::: Only {} cards in {}'s Deck. {} Needed!".format(loDeckCount,me,num(Identity.Requirement)))
   mute()
   loAP = 0
   loInf = 0
   loRunner = False
   agendasCount = 0
   debugNotify("About to move cards into me.ScriptingPile", 4) #Debug
   for card in group: card.moveTo(me.ScriptingPile)
   if len(players) > 1: random = rnd(1,100) # Fix for multiplayer only. Makes Singleplayer setup very slow otherwise.
   debugNotify("About to check each card in the deck", 4) #Debug
   counts = collections.defaultdict(int)
   CardLimit = {}
   professorsRig = [] # This is used by "The Professor" to avoid counting influence for the first instance of a program.
   for card in me.ScriptingPile:
      counts[card.name] += 1
      if counts[card.name] > 3:
         notify(":::ERROR::: Only 3 copies of {} allowed.".format(card.name))
         ok = False
      if card.Type == 'Agenda':
         if ds == 'corp':
            loAP += num(card.Stat)
            agendasCount += 1
         else:
            notify(":::ERROR::: Agendas found in {}'s Stack.".format(me))
            ok = False
      elif card.Type in CorporationCardTypes and Identity.Faction in RunnerFactions:
         notify(":::ERROR::: Corporate cards found in {}'s Stack.".format(me))
         ok = False
      elif card.Type in RunnerCardTypes and Identity.Faction in CorporateFactions:
         notify(":::ERROR::: Runner cards found in {}'s R&Ds.".format(me))
         ok = False
      if num(card.Influence) and card.Faction != Identity.Faction:
         if Identity.model == 'bc0f047c-01b1-427f-a439-d451eda03029' and card.Type == 'Program' and card.model not in professorsRig:
            debugNotify("adding {} to prof. rig. card type = {}".format(card,card.Type))
            professorsRig.append(card.model) # First instance of a card is free of influence costs.
         else: 
            debugNotify("adding influence of {}. card type = {}".format(card,card.Type))
            loInf += num(card.Influence)
      else:
         if card.Type == 'Identity':
            notify(":::ERROR::: Extra Identity Cards found in {}'s {}.".format(me, pileName(group)))
            ok = False
         elif card.Faction != Identity.Faction and card.Faction != 'Neutral':
            notify(":::ERROR::: Faction-restricted card ({}) found in {}'s {}.".format(fetchProperty(card, 'name'), me, pileName(group)))
            ok = False
      if Identity.model == 'bc0f047c-01b1-427f-a439-d451eda03002' and card.Faction == 'Jinteki':
         notify(":::ERROR::: Jinteki cards found in a {} deck".format(Identity))
         ok = False
      if card.model in LimitedCard:
         if card.model not in CardLimit: CardLimit[card.model] = 1
         else: CardLimit[card.model] += 1
         if CardLimit[card.model] > 1: 
            notify(":::ERROR::: Duplicate Limited card ({}) found in {}'s {}.".format(card,me,pileName(group)))
            ok = False
   if len(players) > 1: random = rnd(1,100) # Fix for multiplayer only. Makes Singleplayer setup very slow otherwise.
   for card in me.ScriptingPile: card.moveToBottom(group) # We use a second loop because we do not want to pause after each check
   if ds == 'corp':
      requiredAP = 2 + 2 * int(loDeckCount / 5)
      if loAP not in (requiredAP, requiredAP + 1):
         notify(":::ERROR::: {} cards requires {} or {} Agenda Points, found {}.".format(loDeckCount, requiredAP, requiredAP + 1, loAP))
         ok = False
   if loInf > num(Identity.Stat):
      notify(":::ERROR::: Too much rival faction influence in {}'s R&D. {} found with a max of {}".format(me, loInf, num(Identity.Stat)))
      ok = False
   deckStats = (loInf,loDeckCount,agendasCount) # The deck stats is a tuple that we stored shared, and stores how much influence is in the player's deck, how many cards it has and how many agendas
   me.setGlobalVariable('Deck Stats',str(deckStats))
   debugNotify("Total Influence used: {} (Influence string stored is: {}".format(loInf, me.getGlobalVariable('Influence')), 2) #Debug
   if ok: notify("-> Deck of {} is OK!".format(me))
   else: 
      notify("-> Deck of {} is _NOT_ OK!".format(me))
      information("We have found illegal cards in your deck. Please load a legal deck!")
   debugNotify("<<< checkDeckNoLimit()") #Debug
   chkSideFlip()
  
def chkSideFlip():
   mute()
   debugNotify(">>> chkSideFlip()")
   debugNotify("Checking Identity", 3)
   global flipBoard, flipModX, flipModY
   if not ds:
      information(":::ERROR::: No Identity found! Please load a deck which contains an Identity card before proceeding to setup.")
      return
   chooseSide()
   debugNotify("Checking side Flip", 3)
   if (ds == 'corp' and me.hasInvertedTable()) or (ds == 'runner' and not me.hasInvertedTable()):
      debugNotify("Flipping Board")
      if flipBoard == 1:
         flipBoard = -1
         flipModX = -61
         flipModY = -77
         table.setBoardImage("table\\Tabletop_flipped.png")
   elif flipBoard == -1: 
      debugNotify("Restroring Board Orientation")
      flipBoard = 1
      flipModX = 0
      flipModY = 0
      table.setBoardImage("table\\Tabletop.png") # If they had already reversed the table before, we set it back proper again
   else: debugNotify("Leaving Board as is")

def parseNewCounters(player,counter,oldValue):
   mute()
   debugNotify(">>> parseNewCounters() for player {} with counter {}. Old Value = {}".format(player,counter.name,oldValue))
   if counter.name == 'Tags' and player == me: chkTags()
   debugNotify("<<< parseNewCounters()")

def checkMovedCard(player,card,fromGroup,toGroup,oldIndex,index,oldX,oldY,x,y):
   mute()
   global scriptedPlay 
   #debugNotify("scriptedPlay = {}".format(scriptedPlay))
   if fromGroup == me.hand and toGroup == table: 
      return # Doesn't work. Too many outlier scenarios. See https://github.com/kellyelton/OCTGN/issues/984
      if not scriptedPlay: 
         intPlay(card)
         scriptedPlay -= 1
      else: 
         scriptedPlay -= 1
         if scriptedPlay < 0: scriptedPlay = 0 # Just in case
   if fromGroup == table and toGroup != table and card.owner == me: # If the player dragged a card manually from the table to their discard pile...
      debugNotify("Clearing card attachments")
      clearAttachLinks(card)
      
      