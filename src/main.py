# -*- coding: utf-8 -*-
# 
from os.path import dirname, join, basename, exists, join
import sys, os, platform, re, subprocess, aqt.utils
from anki.utils import stripHTML, isWin, isMac
from . import Pyperclip 
import re

import unicodedata
import urllib.parse
from shutil import copyfile
from anki.hooks import addHook, wrap, runHook, runFilter
from aqt.utils import shortcut, saveGeom, saveSplitter, showInfo, askUser
import aqt.editor
import json
from aqt import mw
from aqt.theme import theme_manager
from aqt.qt import *
from . import dictdb
sys.path.append(join(dirname(__file__), 'lib'))
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import time
from urllib.request import Request, urlopen
from .misettings import SettingsGui
from .miutils import miInfo, miAsk
import requests
from aqt.main import AnkiQt
from anki import Collection
from .models import MILanguageModels
from .LanguageHandler import LanguageHandler
from .cssJSHandler import CSSJSHandler
from .forvodl import Forvo
from aqt.reviewer import Reviewer
from aqt.previewer import Previewer


forvoHandler= Forvo("German")
 
def getConfig():
    return mw.addonManager.getConfig(__name__)

def updateMigakuLanguageConfig():
    mw.migakuGermanConfig = getConfig()

def reorderByCountry(audioList):
    targetCountry = "Germany"
    audioFromTargetCountry = []
    audioFromElsewhere = []
    for entry in audioList:
        source = entry[1]
        if targetCountry in source:
            audioFromTargetCountry.append(entry)
        else:
            audioFromElsewhere.append(entry)
    return audioFromTargetCountry + audioFromElsewhere


def getAudioHtml(word):
    audioList = forvoHandler.search(word)
    if len(audioList) == 0:
        return ""
    htmlList = []
    sortedAudioList = reorderByCountry(audioList)
    count = 0
    for audioEntry in sortedAudioList:
        if count > 2:
            break
        count += 1
        name = audioEntry[0]
        source = audioEntry[1].replace("(", "").replace(")","")
        url = audioEntry[2]
        htmlList.append('<div class="migaku-audio-source"><div onclick="migakuPlayChildAudio(this)" class="migaku-play-button"><audio class="migaku-audio-tag" src="%s"></audio><div class="migaku-play-icon">▶</div></div><span class="migaku-audio-name">%s</span>　<span class="migaku-audio-details">%s</span></div>' % ( url, name, source))
    return ''.join(htmlList)
        
def loadAudioOptionsIntoPage(page, word, elementId):
    html = getAudioHtml(word)
    js = "loadMigakuAudioIntoId('%s', '%s');" % (elementId, html)
    page.eval(js)


def migakuLanguageBridge(self, cmd, ogBridge):
    if cmd.startswith("requestMigakuGermanAudio"):
        values = cmd.split("◱")
        word = values[1]
        elementId = values[2]
        if hasattr(self, "web"):
            target = self.web
        else:
            target = self._web
        loadAudioOptionsIntoPage(target, word, elementId)
    elif cmd.startswith("migakuLanguageSearch"):
        values = cmd.split("◱")
        term = values[1]
        if not (hasattr(mw, "migakuDictionary")):
            return
        if mw.migakuDictionary and mw.migakuDictionary.isVisible():
            mw.migakuDictionary.initSearch(term)
        elif mw.MigakuDictConfig['openOnGlobal']:
            mw.dictionaryInit(term)
    else:
        ogBridge(self, cmd)  

def reviewerBridge(self, cmd):
    migakuLanguageBridge(self, cmd, ogReviewerBridge)

def previewerBridge(self, cmd):
   migakuLanguageBridge(self, cmd, ogPreviewerBridge)



ogReviewerBridge = Reviewer._linkHandler 
Reviewer._linkHandler = reviewerBridge

ogPreviewerBridge = Previewer._on_bridge_cmd
Previewer._on_bridge_cmd = previewerBridge

languageModeler = MILanguageModels(mw)
addHook("profileLoaded", languageModeler.addModels)
mw.miGermanSettings = False
db = dictdb.DictDB()
addonPath = dirname(__file__)
autoCssJs = CSSJSHandler(mw,addonPath)
mw.MigakuGerman = LanguageHandler(mw,addonPath, db, autoCssJs)
mw.migakuGermanConfig = getConfig()
mw.updateMigakuGermanConfig = updateMigakuLanguageConfig
# addHook("profileLoaded", autoCssJs.loadWrapperDict)
addHook("profileLoaded", autoCssJs.injectWrapperElements)
addHook("profileLoaded", autoCssJs.updateWrapperDict)

requests.packages.urllib3.disable_warnings()

currentNote = False 
currentField = False
currentKey = False
wrapperDict = False
colArray = False

def loadCollectionArray(self = None, b = None):
    global colArray
    colArray = {}
    loadAllProfileInformation()

def loadAllProfileInformation():
    global colArray
    for prof in mw.pm.profiles():
        cpath = join(mw.pm.base, prof,  'collection.anki2')
        try:
            tempCol = Collection(cpath)
            noteTypes = tempCol.models.all()
            tempCol.close()
            tempCol = None
            noteTypeDict = {}
            for note in noteTypes:
                noteTypeDict[note['name']] = {"cardTypes" : [], "fields" : []}
                for ct in note['tmpls']:
                    noteTypeDict[note['name']]["cardTypes"].append(ct['name'])
                for f in note['flds']:
                    noteTypeDict[note['name']]["fields"].append(f['name'])
            colArray[prof] = noteTypeDict
        except:
            miInfo('<b>Warning:</b><br>One of your profiles could not be loaded. This usually happens if you\'ve just created a new profile and are opening it for the first time.The issue should be fixed after restarting Anki.If it persists, then your profile is corrupted in some way.\n\nYou can fix this corruption by exporting your collection, importing it into a new profile, and then deleting your previous profile. <b>', level='wrn')


AnkiQt.loadProfile = wrap(AnkiQt.loadProfile, loadCollectionArray, 'before')


def openLanguageSettings():
    if not mw.miGermanSettings:
        mw.miGermanSettings = SettingsGui(mw, addonPath, colArray, languageModeler, autoCssJs, openLanguageSettings, "miGermanSettings")
    mw.miGermanSettings.show()
    if mw.miGermanSettings.windowState() == Qt.WindowMinimized:
            # Window is minimised. Restore it.
           mw.miGermanSettings.setWindowState(Qt.WindowNoState)
    mw.miGermanSettings.setFocus()
    mw.miGermanSettings.activateWindow()


def setupGuiMenu():
    addMenu = False
    if not hasattr(mw, 'MigakuMainMenu'):
        mw.MigakuMainMenu = QMenu('Migaku',  mw)
        addMenu = True
    if not hasattr(mw, 'MigakuMenuSettings'):
        mw.MigakuMenuSettings = []
    if not hasattr(mw, 'MigakuMenuActions'):
        mw.MigakuMenuActions = []
    
    setting = QAction("German Settings", mw)
    setting.triggered.connect(openLanguageSettings)
    mw.MigakuMenuSettings.append(setting)

    mw.MigakuMainMenu.clear()
    for act in mw.MigakuMenuSettings:
        mw.MigakuMainMenu.addAction(act)
    mw.MigakuMainMenu.addSeparator()
    for act in mw.MigakuMenuActions:
        mw.MigakuMainMenu.addAction(act)

    if addMenu:
        mw.form.menubar.insertMenu(mw.form.menuHelp.menuAction(), mw.MigakuMainMenu)

setupGuiMenu()


def setupButtons(righttopbtns, editor):
  if not checkProfile():
        return righttopbtns
  editor._links["Entfernen"] = lambda editor: mw.MigakuGerman.cleanField(editor)

  if theme_manager.night_mode == True:
    readingPath = os.path.join(addonPath, "icons", "languageNight.svg")
    deletePath = os.path.join(addonPath, "icons", "languageDeleteNight.svg")
  else:
    readingPath = os.path.join(addonPath, "icons", "language.svg")
    deletePath = os.path.join(addonPath, "icons", "languageDelete.svg")

  righttopbtns.insert(0, editor._addButton(
                icon=deletePath,
                cmd='Entfernen',
                tip="Hotkey: F10",
                id=u"Entfernen"
            ))
  editor._links["Deutsche"] = lambda editor: mw.MigakuGerman.addLanguageReadings(editor)
  righttopbtns.insert(0, editor._addButton(
                icon=readingPath,
                cmd='Deutsche',
                tip="Hotkey: F9",
                id=u"Deutsche"
            ))
  return righttopbtns

def shortcutCheck(x, key):
    if x == key:
        return False
    else:
        return True

def setupShortcuts(shortcuts, editor):
    if not checkProfile():
        return shortcuts
    # config = getConfig()
    pitchData = []
    pitchData.append({ "hotkey": "F10", "name" : 'extra', 'function' : lambda  editor=editor: mw.MigakuGerman.cleanField(editor)})
    pitchData.append({ "hotkey": "F9", "name" : 'extra', 'function' : lambda  editor=editor: mw.MigakuGerman.addLanguageReadings(editor)})
    newKeys = shortcuts;
    for pitch in pitchData:
        newKeys = list(filter(lambda x: shortcutCheck(x[0], pitch['hotkey']), newKeys))
        newKeys += [(pitch['hotkey'] , pitch['function'])]
    shortcuts.clear()
    shortcuts += newKeys
    return 


def onRegenerate(browser):
    import anki.find
    notes = browser.selectedNotes()
    if notes:
        fields = anki.find.fieldNamesForNotes(mw.col, notes)
        generateWidget = QDialog(None, Qt.Window)
        layout = QHBoxLayout()
        og = QLabel('Origin:')
        cb = QComboBox()
        cb.addItems(fields)
        dest = QLabel('Destination:')
        destCB = QComboBox()
        destCB.addItems(fields)
        om = QLabel('Output Mode:')
        omCB = QComboBox()
        omCB.addItems(['Add', 'Overwrite', 'If Empty'])
        b4 =  QPushButton('Add Readings')
        b4.clicked.connect(lambda: mw.MigakuGerman.massGenerate(cb.currentText(), destCB.currentText(), omCB.currentText(),  notes, generateWidget))##add in the vars
        b5 =  QPushButton('Remove Readings')
        b5.clicked.connect(lambda: mw.MigakuGerman.massRemove(cb.currentText(), notes, generateWidget))
        layout.addWidget(og)
        layout.addWidget(cb)
        layout.addWidget(dest)
        layout.addWidget(destCB)
        layout.addWidget(om)
        layout.addWidget(omCB)
        layout.addWidget(b4)
        layout.addWidget(b5)
        generateWidget.setWindowIcon(QIcon(join(addonPath, 'icons', 'migaku.png')))
        generateWidget.setWindowTitle("Generate German Readings")
        generateWidget.setLayout(layout)
        generateWidget.exec_()
    else:
        miInfo('Please select some cards before attempting to mass generate.')

def setupMenu(browser):
    if not checkProfile():
        return
    a = QAction("Generate German Readings", browser)
    a.triggered.connect(lambda: onRegenerate(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)

current_path = os.path.abspath('.')
parent_path = os.path.dirname(current_path)
sys.path.append(parent_path)


def checkProfile():
    config = mw.migakuGermanConfig
    if mw.pm.name in config['Profiles'] or ('all' in config['Profiles'] or 'All' in config['Profiles']):
        return True
    return False

def supportAccept(self):
    if self.addon != os.path.basename(addonPath):
        ogAccept(self)
    txt = self.form.editor.toPlainText()
    try:
        new_conf = json.loads(txt)
    except Exception as e:
        showInfo(_("Invalid configuration: ") + repr(e))
        return

    if not isinstance(new_conf, dict):
        showInfo(_("Invalid configuration: top level object must be a map"))
        return

    if new_conf != self.conf:
        self.mgr.writeConfig(self.addon, new_conf)
        # does the add-on define an action to be fired?
        act = self.mgr.configUpdatedAction(self.addon)
        if act:
            act(new_conf)
        if not autoCssJs.injectWrapperElements():
            return

    saveGeom(self, "addonconf")
    saveSplitter(self.form.splitter, "addonconf")
    self.hide()

ogAccept = aqt.addons.ConfigEditor.accept 
aqt.addons.ConfigEditor.accept = supportAccept
    
addHook("browser.setupMenus", setupMenu)
addHook("setupEditorButtons", setupButtons)
addHook("setupEditorShortcuts", setupShortcuts)

def getFieldName(fieldId, note):
    fields = mw.col.models.fieldNames(note.model())
    field = fields[int(fieldId)]
    return field;


def bridgeReroute(self, cmd):
    global currentKey
    if checkProfile():
        if cmd.startswith('textToGermanReading:'):
            splitList = cmd.split(':||:||:')
            if self.note.id == int(splitList[3]):
                field = getFieldName(splitList[2], self.note)
                mw.MigakuGerman.finalizeReadings(splitList[1], field, self.note, self)
            return
    ogReroute(self, cmd)

ogReroute = aqt.editor.Editor.onBridgeCmd 
aqt.editor.Editor.onBridgeCmd = bridgeReroute