# -*- coding: utf-8 -*-
# Copyright: Arthur Milchior arthur@milchior.fr
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Select any number of cards in the card browser and create exact copies of each card in the deck
# Feel free to contribute to this code on https://github.com/Arthur-Milchior/anki-copy-note
# Anki's add-on number: 1566928056
# This add-ons is heavily based on Kealan Hobelmann's addon 396494452

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from anki.hooks import addHook
from aqt import mw
from .config import getConfig
from aqt.utils import tooltip, showWarning
from anki.utils import timestampID, intTime
import anki.notes
#import profile


def copyCards(nids,review):
    mw.checkpoint("Copy Notes")
    mw.progress.start()


    # Copy notes
    for nid in nids:
        note = mw.col.getNote(nid)
        model = note._model

        # Create new note
        note_copy = anki.notes.Note(mw.col,model=model)
        # Copy tags and fields (all model fields) from original note
        note_copy.tags = note.tags
        note_copy.fields = note.fields
        note_copy.id = timestampID(note.col.db, "notes", note.id)
        # Refresh note and add to database
        note_copy.flush()
        mw.col.addNote(note_copy)
        nid_copy = note_copy.id

        cards_copy= note_copy.cards()
        cards= note.cards()
        ord_to_card = {card.ord:card for card in cards}
        ord_to_card_copy = {card.ord:card for card in cards_copy}
        if review:
            for card in cards:
                ord = card.ord
                card_copy = ord_to_card_copy.get(ord)
                if card_copy:
                    card.id=card_copy.id
                    card.nid = nid_copy
                else:
                    tooltip("We copy a card which should not exists.")
                    card.id=timestampID(mw.col.db,"cards")
                    card.nid=nid_copy
                card.flush()
        else:
            for card_copy in cards_copy:
                ord = card_copy.ord
                card = ord_to_card.get(ord)
                if card:
                    card_copy.did=card.odid or card.did
                    card_copy.flush()

    # Reset collection and main window
    mw.progress.finish()
    mw.col.reset()
    mw.reset()

    tooltip(_("""Cards copied."""))


def setupMenu(browser):
    a = QAction("Note Copy", browser)
    shortCut = getConfig("Shortcut: simple copy","Ctrl+C")
    if shortCut:
        a.setShortcut(QKeySequence(shortCut))
    a.triggered.connect(lambda : onCopyCards(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)
    a = QAction("Full Notes Copy", browser)
    shortCut = getConfig("Shortcut: full copy","Ctrl+Alt+C")
    if shortCut:
        a.setShortcut(QKeySequence(shortCut))
    a.triggered.connect(lambda : onCopyCards(browser,review=True))
    browser.form.menuEdit.addAction(a)

def onCopyCards(browser, review=False):
    copyCards(browser.selectedNotes(),review)

addHook("browser.setupMenus", setupMenu)

def timestampID(db, table, t=None):
    "Return a non-conflicting timestamp for table."
    # be careful not to create multiple objects without flushing them, or they
    # may share an ID.
    t = t or intTime(1000)
    while db.scalar("select id from %s where id = ?" % table, t):
        t += 1
    return t
