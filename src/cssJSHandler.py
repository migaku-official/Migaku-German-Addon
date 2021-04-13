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


class CSSJSHandler():

    def __init__(self, mw, path):
        self.mw = mw
        self.path = path
        self.wrapperDict = False
        self.languageParserHeader = '<!--###MIGAKU GERMAN SUPPORT JS START###\nDo Not Edit If Using Automatic CSS and JS Management-->'
        self.languageParserFooter = '<!--###MIGAKU GERMAN SUPPORT JS ENDS###-->' 
        self.languageCSSHeader = '/*###MIGAKU GERMAN SUPPORT CSS STARTS###\nDo Not Edit If Using Automatic CSS and JS Management*/'
        self.languageCSSFooter = '/*###MIGAKU GERMAN SUPPORT CSS ENDS###*/'  
        self.languageCSSPattern = '\/\*###MIGAKU GERMAN SUPPORT CSS STARTS###\nDo Not Edit If Using Automatic CSS and JS Management\*\/[^*]*?\/\*###MIGAKU GERMAN SUPPORT CSS ENDS###\*\/'
        self.wrapperClass = "wrapped-german"
        self.languageParserJS = self.getLanguageParserJS()



    def updateWrapperDict(self):
        self.wrapperDict, wrapperCheck = self.getWrapperDict()

    def getLanguageParserJS(self):
        languageParser = join(self.path, "js", "languageParser.js")
        with open(languageParser, "r", encoding="utf-8") as languageParserFile:
            return languageParserFile.read() 


    def getConfig(self):
        return self.mw.addonManager.getConfig(__name__)

    
    def noteCardFieldExists(self, data):
        models = self.mw.col.models.all()
        error = ''
        note = False
        card = False
        field = False
        side = False
        if data[5] in ['both', 'front', 'back']:
            side = True
        for model in models:
            if model['name'] == data[2] and not note:
                note = True
                for t in model['tmpls']:
                    if t['name'] == data[3] and not card:
                        card = True
                for fld in model['flds']:
                    if fld['name'] == data[4] and not field:
                        field = True 
        if not note:
            return False, 'The "'+ data[2] +'" note type does not exist in this profile, if this note type exists in another profile consider setting its profile setting to the appropriate profile in the Active Fields settings menu.';
        
        if not card:
            error += 'The "'+ data[3] +'" card type does not exist.\n'
        if not field:
            error += 'The "'+ data[4] +'" field does not exist.\n'
        if not side:
            error += 'The last value must be "front", "back", or "both", it cannot be "' + data[5] + '"'

        if error == '':
            return True, False;
        return False, error;


    def fieldConflictCheck(self, item, array, dType):
        conflicts = []
        for value in array:
            valAr = value[0]
            valDType = value[1]
            if valAr == item:
                conflicts.append('In "'+ valDType +'": ' + ';'.join(valAr))
                conflicts.append('In "'+ dType +'": ' + ';'.join(item))
                return False, conflicts;
            elif valAr[2] == item[2] and valAr[3] == item[3] and valAr[4] == item[4] and (valAr[5]  == 'both' or item[5] == 'both'):
                conflicts.append('In "'+ valDType +'": ' + ';'.join(valAr))
                conflicts.append('In "'+ dType +'": ' + ';'.join(item))
                return False, conflicts;
        return True, True; 


    def getWrapperDict(self):
        wrapperDict = {}
        displayOptions = ['gender-highlighting', 'no-highlighting']
        models = self.mw.col.models.all()
        syntaxErrors = ''
        notFoundErrors = ''
        fieldConflictErrors = ''
        displayTypeError = ''
        alreadyIncluded = []
        for item in self.config['ActiveFields']:
            dataArray = item.split(";")
            displayOption = dataArray[0]
            if (len(dataArray) != 6 and len(dataArray) != 7) or  '' in dataArray:
                syntaxErrors += '\n"' + item + '" in "' + displayOption + '"\n'
            elif displayOption.lower() not in displayOptions:
                displayTypeError += '\n"' + item + '" in "ActiveFields" has an incorrect display type of "'+ displayOption +'"\n'
            else:
                if self.mw.pm.name != dataArray[1] and 'all' != dataArray[1].lower():
                    continue
                
                if dataArray[2] != 'noteTypeName' and dataArray[3] != 'cardTypeName' and dataArray[4] != 'fieldName':
                    success, errorMsg = self.noteCardFieldExists(dataArray)
                    if success:
                        conflictFree,  conflicts = self.fieldConflictCheck(dataArray, alreadyIncluded, displayOption)
                        if conflictFree:
                            if dataArray[2] not in wrapperDict:
                                alreadyIncluded.append([dataArray, displayOption])
                                wrapperDict[dataArray[2]] = [[dataArray[3], dataArray[4], dataArray[5],displayOption]]
                            else:
                                if [dataArray[3], dataArray[4], dataArray[5],displayOption, ] not in wrapperDict[dataArray[2]]:
                                    alreadyIncluded.append([dataArray, displayOption])
                                    wrapperDict[dataArray[2]].append([dataArray[3], dataArray[4], dataArray[5],displayOption])
                        else:
                            fieldConflictErrors += 'A conflict was found in this field pair:\n\n' + '\n'.join(conflicts) + '\n\n'
                    else:
                            notFoundErrors += '"' + item + '" in "ActiveFields" has the following error(s):\n' + errorMsg + '\n\n'

        if syntaxErrors != '':
            miInfo('The following entries have incorrect syntax:\nPlease make sure the format is as follows:\n"displayType;profileName;noteTypeName;cardTypeName;fieldName;side;coloringMode".\n' + syntaxErrors, level="err")
            return (wrapperDict,False);
        if displayTypeError != '':
            miInfo('The following entries have an incorrect display type. Valid display types are "Gender Highlighting" "No Highlighting".\n' + syntaxErrors, level="err")
            return (wrapperDict,False);
        # if notFoundErrors != '':
        #     miInfo('The following entries have incorrect values that are not found in your Anki collection. Please review these entries and fix any spelling mistakes.\n\n' + notFoundErrors, level="err")
        #     return (wrapperDict,False);
        if fieldConflictErrors != '':
            miInfo('You have entries that point to the same field and the same side. Please make sure that a field and side combination does not conflict.\n\n' + fieldConflictErrors, level="err")
            return (wrapperDict,False);
        return (wrapperDict, True);


    def checkProfile(self):
        if self.mw.pm.name in self.config['Profiles'] or ('all' in self.config['Profiles'] or 'All' in self.config['Profiles']):
            return True
        return False

    def injectWrapperElements(self):
        self.config = self.getConfig()
        if not self.checkProfile():
            return
        if not self.config["AutoCssJsGeneration"]:
            return
        self.wrapperDict, wrapperCheck = self.getWrapperDict()  
        models = self.mw.col.models.all()
        for model in models:
            if model['name'] in self.wrapperDict:
                model['css'] = self.editLanguageCss(model['css'])
                for idx, t in enumerate(model['tmpls']):
                    modelDict = self.wrapperDict[model['name']]
                    
                    if self.templateInModelDict(t['name'], modelDict):
                        templateDict = self.templateFilteredDict(modelDict, t['name'])
                        t['qfmt'], t['afmt'] = self.cleanFieldWrappers(t['qfmt'], t['afmt'], model['flds'], templateDict)
                        for data in templateDict: 
                            ### TemplateDict is [[cardtype (eg reading), field, front/back/both, displayType],...]

                            if data[2] == 'both' or data[2] == 'front':                              
                                t['qfmt'] =  self.overwriteWrapperElement(t['qfmt'], data[1], data[3])
                                t['qfmt'] =  self.injectWrapperElement(t['qfmt'], data[1], data[3])
                                t['qfmt'] = self.editLanguageJs(t['qfmt'])
                            if data[2] == 'both' or data[2] == 'back':          
                                t['afmt'] = self.overwriteWrapperElement(t['afmt'], data[1], data[3])
                                t['afmt'] = self.injectWrapperElement(t['afmt'], data[1], data[3])
                                t['afmt'] = self.editLanguageJs(t['afmt'])
                    else:
                        t['qfmt'] = self.removeWrappers(t['qfmt'])
                        t['afmt'] = self.removeWrappers(t['afmt'])
                         
                        
            else:
                model['css'] = self.removeLanguageCss(model['css'])
                for t in model['tmpls']:
                    t['qfmt'] = self.removeLanguageJs(self.removeWrappers(t['qfmt']))
                    t['afmt'] = self.removeLanguageJs(self.removeWrappers(t['afmt']))
            self.mw.col.models.save(model)
        return wrapperCheck 

    def fieldExists(self, field):
        models = self.mw.col.models.all()
        for model in models:
            for fld in model['flds']:
                if field == fld['name'] or field.lower() == 'none':
                    return True
        return False

    
    def newLineReduce(self, text):
        return re.sub(r'\n{3,}', '\n\n', text)

    def getLanguageCss(self):
        genderColors = self.config['LanguageGendersMFN'];
        css = '.migaku-european-word{display:inline-block}.migaku-european-word-container{display:inline-block;position:relative;cursor:pointer}.migaku-european-root-container{display:none;position:absolute;top:calc(100% + 4px);left:-10px;background-color:#fff;cursor:#000;border-radius:5px;padding:10px;box-shadow:rgba(0,0,0,.35) 0 5px 15px;z-index:100;font-family:Times!important}.ankidroid_dark_mode .migaku-european-root-container,.nightMode .migaku-european-root-container{color:#fff;background-color:#2f2f31}.migaku-european-root-hover-box{left:0;position:absolute;bottom:100%;height:7px;width:100%;z-index:100}.migaku-neuter-symbol{font-size:10px}.migaku-masculine-symbol{font-size:15px}.migaku-feminine-symbol{font-size:15px}.migaku-european-root-word{margin-top:5px;font-size:25px;}.migaku-gender-symbol{display:inline-block;margin-left:10px;position:relative;top:-4px;font-size:12px}.migaku-pos-gender{display:flex;justify-content:space-between}.migaku-pos{display:inline-block;color:gray;font-size:12px;padding:2px;height:20px;vertical-align:middle}.migaku-none-symbol{color:#ac80ff!important}.migaku-audio-loader{margin:auto;margin-top:10px;border:5px solid #d3d3d3;border-radius:50%;border-top:5px solid gray;width:20px;height:20px;-webkit-animation:spin 1s linear infinite;animation:spin 1s linear infinite}.ankidroid_dark_mode .migaku-audio-loader,.nightMode .migaku-audio-loader{border:5px solid gray;border-radius:50%;border-top:5px solid #fff}@-webkit-keyframes spin{0%{-webkit-transform:rotate(0)}100%{-webkit-transform:rotate(360deg)}}@keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}.migaku-play-icon{font-size:18px;position:relative;left:2px;line-height:25px;vertical-align:middle;height:100%}.migaku-audio-tag{display:none}.migaku-play-button{display:flex;justify-content:center;height:25px;width:25px;margin-right:5px;background-color:#bbb;border-radius:50%;color:#000;user-select:none;-moz-user-select:none;-webkit-user-select:none;-ms-user-select:none;z-index:10}.migaku-play-button:hover{background-color:gray}.ankidroid_dark_mode .migaku-play-button,.nightMode .migaku-play-button{background-color:#202020;color:#fff}.ankidroid_dark_mode .migaku-play-button:hover,.nightMode .migaku-play-button:hover{background-color:#000}.migaku-audio-source{display:flex;margin:10px;padding:5px,10px;padding-right:10px;background-color:#e0e0e0;border-radius:12.5px;font-size:16px;box-shadow:rgba(0,0,0,.24) 0 3px 8px;white-space:nowrap}.migaku-audio-details{color:#505050;line-height:22px}.migaku-audio-name{line-height:22px}.ankidroid_dark_mode .migaku-audio-source,.nightMode .migaku-audio-source{background-color:#181818}.ankidroid_dark_mode .migaku-audio-details,.nightMode .migaku-audio-details{color:#bebebe}.migaku-displayed-popup{display:block}.migaku-popup-left{right:0!important;left:unset!important}.migaku-popup-top{top:unset!important;bottom:100%!important}'
        genders = ["m", "f", "n"]
        count = 0
        for color in genderColors:
            genderInitial = genders[count]
            css += '.migaku-gender-%s, .ankidroid_dark_mode .migaku-gender-%s, .nightMode .migaku-gender-%s{color:%s;}'%(genderInitial, genderInitial, genderInitial, color)
            count += 1

        return self.languageCSSHeader + '\n' + css + '\n' + self.languageCSSFooter


    def editLanguageCss(self, css):
        pattern = self.languageCSSPattern
        languageCss = self.getLanguageCss()
        if not css:
            return languageCss
        match = re.search(pattern, css)
        if match:
            if match.group() != languageCss:
                return css.replace(match.group(), languageCss)
            else:
                return css
        else:
            return css + '\n' + languageCss

    def templateInModelDict(self, template, modelDict):
        for entries in modelDict:
            if entries[0] == template:
                return True
        return False     

    def templateFilteredDict(self, modelDict, template):
        return list(filter(lambda data, tname = template: data[0] == tname, modelDict))

    def fieldInTemplateDict(self, field, templateDict):
        sides = []
        for entries in templateDict:
            if entries[1] == field:
                sides.append(entries[2])
        return sides   

    def removeLanguageJs(self, text):
        return re.sub(self.languageParserHeader + r'.*?' + self.languageParserFooter, '', text)

    def cleanFieldWrappers(self, front, back, fields, templateDict):
        for field in fields:
            sides = self.fieldInTemplateDict(field['name'], templateDict)

            
            if len(sides) > 0:
                pattern = r'<div display-type="[^>]+?" class="' + self.wrapperClass + '">({{'+ field['name'] +'}})</div>'
                if 'both' not in sides or 'front' not in sides:
                    front = re.sub(pattern, '{{'+ field['name'] +'}}', front)
                    front = self.removeLanguageJs(front)
                if 'both' not in sides or 'back' not in sides:
                    back = re.sub(pattern, '{{'+ field['name'] +'}}', back)
                    back = self.removeLanguageJs(back)
            else:
                pattern = r'<div display-type="[^>]+?" class="' + self.wrapperClass + '">({{'+ field['name'] +'}})</div>'
                front = re.sub(pattern, '{{'+ field['name'] +'}}', front)
                back = re.sub(pattern, '{{'+ field['name'] +'}}', back)
                front = self.removeLanguageJs(front)
                back = self.removeLanguageJs(back)
        return front, back;


    def overwriteWrapperElement(self, text, field, dType):
        pattern = r'<div display-type="([^>]+?)" class="' + self.wrapperClass + '">{{'+ field + r'}}</div>'
        finds = re.findall(pattern, text)

        if len(finds) > 0:
            for find in finds:
                if dType.lower() != find[1].lower():
                    toReplace = '<div display-type="'+ find[1] + '" class="' + self.wrapperClass + '">{{'+ field + r'}}</div>'
                    replaceWith = '<div display-type="'+ dType +'" class="' + self.wrapperClass + '">{{'+ field + r'}}</div>'
                    text = text.replace(toReplace, replaceWith)
             
        return text

    def injectWrapperElement(self, text, field, dType):
        pattern = r'(?<!(?:class="' + self.wrapperClass + '">))({{'+ field + r'}})'
        replaceWith = '<div display-type="'+ dType +'" class="' + self.wrapperClass + '">{{'+ field + '}}</div>'
        text = re.sub(pattern, replaceWith,text)  
        return text

    def getLanguageJs(self):
        js = '<script>' + self.languageParserJS + '</script>'
        return self.languageParserHeader + js + self.languageParserFooter

    def editLanguageJs(self, text):
        pattern = self.languageParserHeader + r'.*?' + self.languageParserFooter
        languageJS = self.getLanguageJs()
        if not text:
            return languageJS
        match = re.search(pattern, text)
        if match:
            if match.group() != languageJS:
                return self.newLineReduce(re.sub(match.group, languageJS, text))
            else:
                return text
        else:
            return self.newLineReduce(text + '\n' + languageJS)
        return

    def removeWrappers(self, text):
        pattern = r'<div display-type="[^>]+?" class="' + self.wrapperClass + '">({{[^}]+?}})</div>'
        text = re.sub(pattern, r'\1', text)
        return text

    def removeLanguageCss(self, css):
        return re.sub(self.languageCSSPattern, '', css)


    


