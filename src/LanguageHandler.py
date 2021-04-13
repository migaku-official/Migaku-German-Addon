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
from aqt.utils import shortcut, saveGeom, saveSplitter
import aqt.editor
import json
from aqt import mw
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
from .miutils import miInfo, miAsk


class LanguageHandler():

    def __init__(self, mw, path,  db, cssJSHandler):
        self.mw = mw 
        self.cssJSHandler = cssJSHandler
        self.path = path
        self.db = db
        self.commonJS = self.getCommonJS()
        self.insertHTMLJS = self.getInsertHTMLJS()
        self.insertToFieldJS = self.getInsertToFieldJS()
        self.fetchTextJS = self.getFetchTextJS()
        self.bracketsFromSelJS = self.getBracketFromSelJs()
        self.removeBracketsJS = self.getRemoveBracketJS()
        self.config = self.getConfig()

     

    def refreshConfig(self):
        self.config = self.getConfig()

    def getProgressWidget(self):
        progressWidget = QWidget(None)
        layout = QVBoxLayout()
        progressWidget.setFixedSize(400, 70)
        progressWidget.setWindowModality(Qt.ApplicationModal)
        progressWidget.setWindowIcon(QIcon(join(self.path, 'icons', 'migaku.png')))
        bar = QProgressBar(progressWidget)
        bar.setFixedSize(390, 50)
        bar.move(10,10)
        per = QLabel(bar)
        per.setAlignment(Qt.AlignCenter)
        progressWidget.show()
        return progressWidget, bar;


    def massGenerate(self, og, dest,  om, notes, generateWidget):
        self.mw.checkpoint('German Reading Generation')
        if not miAsk('Are you sure you want to generate from the "'+ og +'" field into  the "'+ dest +'" field?.'):
            return
        generateWidget.close() 
        progWid, bar = self.getProgressWidget()   
        bar.setMinimum(0)
        bar.setMaximum(len(notes))
        val = 0;  
        for nid in notes:
            note = mw.col.getNote(nid)
            fields = mw.col.models.fieldNames(note.model())
            if og in fields and dest in fields:

                text = note[og] 
                newText = self.finalizeReadings(text,note, og)
                note[dest] = self.applyOM(om, note[dest], newText)
                note.flush()
            val+=1;
            bar.setValue(val)
            mw.app.processEvents()
        mw.progress.finish()
        mw.reset()


    def applyOM(self, addType, dest, text): ##overwrite mode/addtype
        if text:
            if addType == 'If Empty':
                if dest == '':
                    dest = text
            elif addType == 'Add':
                if dest == '':
                    dest = text
                else:
                    dest += '<br>' + text
            else:
                dest = text    
        return dest

    def massRemove(self, field,  notes, generateWidget):
        if not miAsk('####WARNING#####\nAre you sure you want to mass remove special syntax from the "'+ field +'" field? Please make sure you have selected the correct field as this will remove all "[" and "]" and text in between from a field.'):
                return
        generateWidget.close() 
        progWid, bar = self.getProgressWidget()   
        bar.setMinimum(0)
        bar.setMaximum(len(notes))
        val = 0
        for nid in notes:
            note = mw.col.getNote(nid)
            fields = mw.col.models.fieldNames(note.model())
            if field in fields:
                text = note[field] 
                text =  self.removeBrackets(text)

                note[field] = text
                note.flush()
            val+=1
            bar.setValue(val)
            mw.app.processEvents()
        mw.progress.finish()
        mw.reset()


    def editorText(self, editor):    
        text = editor.web.selectedText()
        if not text:
            return False
        else:
            return text

    def cleanField(self, editor):
        if self.editorText(editor):
            editor.web.eval(self.commonJS + self.bracketsFromSelJS)
        else:
            editor.web.eval(self.commonJS + self.removeBracketsJS)

    def getBracketFromSelJs(self):
        bracketsFromSel = join(self.path, "js", "bracketsFromSel.js")
        with open(bracketsFromSel, "r") as bracketsFromSelFile:
            return bracketsFromSelFile.read()

    def getRemoveBracketJS(self):    
        removeBrackets = join(self.path, "js", "removeBrackets.js")
        with open(removeBrackets, "r") as removeBracketsFile:
            return removeBracketsFile.read()

    def getFetchTextJS(self):
        fetchText = join(self.path, "js", "fetchText.js")
        with open(fetchText, "r") as fetchTextFile:
            return fetchTextFile.read()  

    def addLanguageReadings(self, editor):
        editor.web.eval(self.commonJS + self.fetchTextJS)

    def getCommonJS(self):
        common_utils_path = join(self.path, "js", "common.js")
        with open(common_utils_path, "r") as common_utils_file:
            return common_utils_file.read()

    def getInsertHTMLJS(self):
        insertHTML = join(self.path, "js", "insertHTML.js")
        with open(insertHTML, "r", encoding="utf-8") as insertHTMLFile:
            return insertHTMLFile.read() 

    def getInsertToFieldJS(self):
        insertHTML = join(self.path, "js", "insertHTMLToField.js")
        with open(insertHTML, "r", encoding="utf-8") as insertHTMLFile:
            return insertHTMLFile.read() 



    def getConfig(self):
        return self.mw.addonManager.getConfig(__name__)

    def getGenderTextFromNumber(self, genderNumber):
        genderOptions = ["x", "n", "f", "m"]
        return genderOptions[genderNumber]

    def getWordWithSyntax(self, word, extraInfo):
        root = extraInfo[0]
        pos = extraInfo[1]
        gender = extraInfo[2]
        genderText = self.getGenderTextFromNumber(gender)
        return word + "[" + root + "," + pos + "," + genderText + "]"
    
    def fetchParsed(self, html, field, note):
        return self.finalizeReadings(html, field, note)


    def finalizeReadings(self, text, field, note, editor = False):
        if text == '':
            return
        text = self.removeBrackets(text)
        text = text.replace('\n', '◱')
        replacedHTML, text = self.htmlRemove(text)
        wordPattern = r'([^\d\W]+)|([\d\W\s]+)'
        words = re.findall(wordPattern, text)
        textList = []
        for word, otherText in words:
            if word:
                extraInfo = self.db.getDeclensionMatch(word)
                print([word, extraInfo])
                if extraInfo:
                    textList.append(self.getWordWithSyntax(word, extraInfo))
                else:
                    textList.append(word)
            elif otherText:
                textList.append(otherText)
        text = ''.join(textList)        
        text = self.replaceHTML(text, replacedHTML)
        if editor:
            editor.web.eval(self.commonJS +  self.insertHTMLJS % text.replace('"', '\\"').replace("'", "\\'"))
        else:
            return text

    def htmlRemove(self, text):
        pattern = r"(?:<[^<]+?>)"
        finds = re.findall(pattern, text)
        text = re.sub(r"<[^<]+?>", "◲", text)
        return finds,text

    def replaceHTML(self, text, matches):
        if matches:
            for match in matches:
                text = text.replace("◲", match, 1)
        return text

    def cleanSpaces(self, text):
        return text.replace('  ', '')
        
    def removeBrackets(self, text, returnSounds = False, removeAudio = False):
        if '[' not in text and ']' not in text:
            if returnSounds:
                return text, [];
            return text
        matches, text = self.htmlRemove(text)
        if removeAudio:
            text = self.cleanSpaces(text)
            text = self.replaceHTML(text, matches)
            return re.sub(r'\[[^]]*?\]', '', text)
        else:
            pattern = r"(?:\[sound:[^\]]+?\])|(?:\[\d*\])"
            finds = re.findall(pattern, text)

            text = re.sub(r"(?:\[sound:[^\]]+?\])|(?:\[\d*\])", "-_-AUDIO-_-", text)
            text  = re.sub(r'\[[^]]*?\]', '', text)
            text = self.cleanSpaces(text)
            text = self.replaceHTML(text, matches)
            if returnSounds:
                return text, finds;
            for match in finds:
                text = text.replace("-_-AUDIO-_-", match, 1)
            return text

