# -*- coding: utf-8 -*-
# 
# 
import json
import sys
import math
from anki.hooks import addHook
from aqt.qt import *
from aqt.utils import openLink, tooltip
from anki.utils import isMac, isWin, isLin
from anki.lang import _
from aqt.webview import AnkiWebView
import re
import platform
from . import Pyperclip 
import os
from os.path import dirname, join
import platform
from .miutils import miInfo, miAsk
from operator import itemgetter


versionNumber = "ver. 1.2.4"

class MigakuSVG(QSvgWidget):
    clicked=pyqtSignal()
    def __init__(self, parent=None):
        QSvgWidget.__init__(self, parent)

    def mousePressEvent(self, ev):
        self.clicked.emit()

class MigakuLabel(QLabel):
    clicked=pyqtSignal()
    def __init__(self, parent=None):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, ev):
        self.clicked.emit()

class SettingsGui(QScrollArea):
    def __init__(self, mw, path, colArray, modeler, cssJSHandler, reboot, settingsManagerName):
        super(SettingsGui, self).__init__()
        self.cssJSHandler = cssJSHandler
        self.modeler = modeler
        self.reboot = reboot
        self.settingsManagerName = settingsManagerName
        self.sides = {'Front' : 'Front: Applies the display type to the front of the card.', 'Back' :'Back: Applies the display type to the back of the card.' , 'Both' : 'Both: Applies the display type to the front and back of the card.'}
        self.displayTypes = {
            'Gender Highlighting' : ['gender-highlighting', 'Noun Gender Highlighting: Highlights nouns based on the gender of that noun']
            , 'No Highlighting' : ['no-highlighting', '']
        }
        self.displayTranslation = {
            'gender-highlighting' : 'Gender Highlighting'
            , 'no-highlighting' : 'No Highlighting'
            }
        self.mw = mw
        self.sortedProfiles = False
        self.sortedNoteTypes = False
        self.selectedRow = False
        self.initializing = False
        self.changingProfile = False
        self.buttonStatus = 0
        self.config = self.getConfig()
        self.cA = self.updateCurrentProfileInfo(colArray)
        self.tabs = QTabWidget()
        self.allFields = self.getAllFields()
        # self.setMinimumSize(800, 550);
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setWindowTitle("Migaku German Settings (%s)"%versionNumber)
        self.addonPath = path
        self.setWindowIcon(QIcon(join(self.addonPath, 'icons', 'migaku.png')))
        self.selectedProfiles = []
        self.selectedGraphFields = []
        self.resetButton = QPushButton('Restore Defaults')
        self.cancelButton = QPushButton('Cancel')
        self.applyButton = QPushButton('Apply')
        self.layout = QVBoxLayout()
        self.innerWidget = QWidget()
        self.setupMainLayout()
        self.tabs.addTab(self.getOptionsTab(), "Options")
        self.tabs.addTab(self.getAFTab(), "Active Fields")
        self.tabs.addTab(self.getAboutTab(), "About")
        self.initTooltips()
        self.loadProfileCB()
        self.loadFontSize()
        self.loadProfilesList()
        self.loadColors()
        self.initActiveFieldsCB()
        self.loadAutoCSSJS()
        self.loadModelAdditions()
        self.loadActiveFields()
        self.hotkeyEsc = QShortcut(QKeySequence("Esc"), self)
        self.hotkeyEsc.activated.connect(self.hide)
        self.handleAutoCSSJS()
        self.initHandlers()
        if isWin:
            self.resize(900, 605)
            self.innerWidget.setFixedSize(880,590)
        else:
            self.resize(900, 625)
            self.innerWidget.setFixedSize(880, 600)
        self.setWidgetResizable(True)
        self.setWidget(self.innerWidget)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.show()


    def resetDefaults(self):
        if miAsk('Are you sure you would like to restore the default settings? This cannot be undone.'):
            conf = self.mw.addonManager.addonConfigDefaults(dirname(__file__))
            self.mw.addonManager.writeConfig(__name__, conf)
            self.close()
            setattr(self.mw, self.settingsManagerName, None) 
            self.reboot()

    def loadFontSize(self):
        self.fontSize.setValue(self.config['FontSize'])

    def loadAutoCSSJS(self):
        self.autoCSSJS.setChecked(self.config['AutoCssJsGeneration'])

    def loadModelAdditions(self):
        self.addLanguage.setChecked(self.config['addLanguageNote'])


    def getAllFields(self):
        fieldList = []
        for prof in self.cA:
            for name, note in self.cA[prof].items():
                for f in note['fields']:
                    if f not in fieldList:
                        fieldList.append(f)
              
        return self.ciSort(fieldList)

    def ciSort(self, l):
        return sorted(l, key=lambda s: s.lower())

    def updateCurrentProfileInfo(self, colA):
        pn = self.mw.pm.name
        noteTypes = self.mw.col.models.all()
        noteTypeDict = {}
        for note in noteTypes:
            noteTypeDict[note['name']] = {"cardTypes" : [], "fields" : []}
            for ct in note['tmpls']:
                noteTypeDict[note['name']]["cardTypes"].append(ct['name'])
            for f in note['flds']:
                noteTypeDict[note['name']]["fields"].append(f['name'])
            colA[pn] = noteTypeDict
        return colA

    def loadColors(self):
        languageColors = self.config["LanguageGendersMFN"]
        MFN = ["M","F","N"]
        for idx,c in enumerate(languageColors):
            name = 'language' + MFN[idx] + 'Color'
            widget = getattr(self, name)
            widget.setText(c)
            widget.setStyleSheet('color:' + c + ';')

    def getOptionsTab(self):
        self.profileCB = QComboBox()
        self.addRemProfile = QPushButton('Add')
        self.currentProfiles = QLabel('None')
        self.bopo2Number = QCheckBox()
        self.altCB = QComboBox()
        self.simpCB = QComboBox()
        self.tradCB = QComboBox()
        self.addRemAlt = QPushButton('Add')
        self.addRemSimp = QPushButton('Add')
        self.addRemTrad = QPushButton('Add')
        self.altLayout = QWidget()
        self.simpLayout = QWidget()
        self.tradLayout = QWidget()
        self.altOW = QRadioButton(self.altLayout)
        self.altIfE = QRadioButton(self.altLayout)
        self.altWithSep = QRadioButton(self.altLayout)
        self.altSep = QLineEdit()
        self.simpOW = QRadioButton(self.simpLayout)
        self.simpIfE = QRadioButton(self.simpLayout)
        self.simpWithSep = QRadioButton(self.simpLayout)
        self.simpSep = QLineEdit()
        self.tradOW = QRadioButton(self.tradLayout)
        self.tradIfE = QRadioButton(self.tradLayout)
        self.tradWithSep = QRadioButton(self.tradLayout)
        self.tradSep = QLineEdit()
        self.currentAlt = QLabel('None')
        self.currentSimp = QLabel('None')
        self.currentTrad = QLabel('None')

        self.languageMColor = QLineEdit()
        self.languageFColor = QLineEdit()
        self.languageNColor = QLineEdit()

        self.gMpb = QPushButton('Select Color')
        self.gFpb = QPushButton('Select Color')
        self.gNpb = QPushButton('Select Color')

        self.fontSize = QSpinBox()
        self.fontSize.setMinimum(1)
        self.fontSize.setMaximum(200)
        

        optionsTab = QWidget(self)
        optionsTab.setLayout(self.getOptionsLayout())
        return optionsTab

    def sizeOptionsWidgets(self):
        self.profileCB.setFixedWidth(120)
        self.addRemProfile.setFixedWidth(80)
        self.languageMColor.setFixedWidth(100)
        self.languageFColor.setFixedWidth(100)
        self.languageNColor.setFixedWidth(100)

        self.gMpb.setFixedWidth(100)
        self.gFpb.setFixedWidth(100)
        self.gNpb.setFixedWidth(100)

        self.fontSize.setFixedWidth(80)

    
    def getOptionsLayout(self):
        self.sizeOptionsWidgets()
        ol = QVBoxLayout() #options layout

        pgb = QGroupBox() #profile group box
        pgbv = QVBoxLayout()
        pgbt = QLabel('<b>Profiles</b>')
        pgbh = QHBoxLayout()
        pgbh.addWidget(self.profileCB)
        pgbh.addWidget(self.addRemProfile)
        pgbh.addStretch()
        pgbh2 = QHBoxLayout()
        l1 = QLabel('Current Profiles:')
        l1.setFixedWidth(100)
        pgbh2.addWidget(l1)
        pgbh2.addWidget(self.currentProfiles)
        pgbh2.addStretch()
        pgbv.addWidget(pgbt)
        pgbv.addLayout(pgbh)
        pgbv.addLayout(pgbh2)
        pgb.setLayout(pgbv)
        ol.addWidget(pgb)


        cgb = QGroupBox() #colors group box
        cgbv = QVBoxLayout()
        cgbv.addWidget(QLabel('<b>Colors</b>'))
    

        ccgb = QGroupBox('Noun genders')  #canto
        ccv = QVBoxLayout()
        cch1 = QHBoxLayout()
        cch2 = QHBoxLayout()
        colNeutral = QLabel('Neutral:')
        colFem = QLabel('Feminine:')
        ColMasc = QLabel('Masculine:')
        colNeutral.setFixedWidth(46)
        colFem.setFixedWidth(46)
        ColMasc.setFixedWidth(46)
        
        cch1.addWidget(colNeutral)
        cch1.addWidget(self.languageNColor)
        cch1.addWidget(self.gNpb)

        cch1.addWidget(colFem)
        cch1.addWidget(self.languageFColor)
        cch1.addWidget(self.gFpb)

        cch1.addWidget(ColMasc)
        cch1.addWidget(self.languageMColor)
        cch1.addWidget(self.gMpb)
        
        cch1.addStretch()
        cch2.addStretch()
        ccv.addLayout(cch1)
        ccv.addLayout(cch2)
        ccgb.setLayout(ccv)


        cgbv.addWidget(ccgb)
        cgb.setLayout(cgbv)
        ol.addWidget(cgb)
        ol.addStretch()

        return ol

    def getAFTable(self):
        afTable = QTableWidget(self)
        afTable.setSortingEnabled(True)
        afTable.setColumnCount(7)
        afTable.setSelectionBehavior(QTableView.SelectRows)
        afTable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tableHeader = afTable.horizontalHeader()
        afTable.setHorizontalHeaderLabels(['Profile', 'Note Type', 'Card Type', 'Field', 'Side', 'Display Type', ''])
        tableHeader.setSectionResizeMode(0, QHeaderView.Stretch)
        tableHeader.setSectionResizeMode(1, QHeaderView.Stretch)
        tableHeader.setSectionResizeMode(2, QHeaderView.Stretch)
        tableHeader.setSectionResizeMode(3, QHeaderView.Stretch)
        tableHeader.setSectionResizeMode(4, QHeaderView.Stretch)
        tableHeader.setSectionResizeMode(5, QHeaderView.Stretch)
        tableHeader.setSectionResizeMode(6, QHeaderView.Fixed)
        afTable.setColumnWidth(6, 40)
        afTable.setEditTriggers(QTableWidget.NoEditTriggers)
        return afTable

    def enableSep(self, sep):
        sep.setEnabled(True)

    def disableSep(self, sep):
        sep.setEnabled(False) 

    def sizeAFLayout(self):
        self.profileAF.setFixedWidth(120)
        self.noteTypeAF.setFixedWidth(120)
        self.cardTypeAF.setFixedWidth(120)
        self.fieldAF.setFixedWidth(120)
        self.sideAF.setFixedWidth(120)
        self.displayAF.setFixedWidth(120)


    def getAFLayout(self):
        self.sizeAFLayout()
        afl = QVBoxLayout() #active fields layout

        afh1 = QHBoxLayout()
        afh1.addWidget(QLabel('Auto CSS & JS Generation:'))
        afh1.addWidget(self.autoCSSJS)
        afh1.addStretch()
        afh1.addWidget(QLabel('Add Migaku Note Types:'))
        afh1.addWidget(self.addLanguage)
        afl.addLayout(afh1)

        afh2 = QHBoxLayout()
        afh2.addWidget(self.profileAF)
        afh2.addWidget(self.noteTypeAF)
        afh2.addWidget(self.cardTypeAF)
        afh2.addWidget(self.fieldAF)
        afh2.addWidget(self.sideAF)
        afh2.addWidget(self.displayAF)
        afl.addLayout(afh2)

        afh3 =QHBoxLayout()
        afh3.addStretch()
        afh3.addWidget(self.addEditAF)
        afl.addLayout(afh3)

        afl.addWidget(self.afTable)

        return afl

    def getAFTab(self):
        self.autoCSSJS = QCheckBox()
        self.addLanguage = QCheckBox('German')
        self.profileAF = QComboBox()
        self.noteTypeAF = QComboBox()
        self.cardTypeAF = QComboBox()
        self.fieldAF = QComboBox()
        self.sideAF = QComboBox()
        self.displayAF = QComboBox()
        #self.readingAF = QComboBox()
        self.addEditAF = QPushButton('Add')
        self.afTable = self.getAFTable()

        afTab = QWidget(self)
        afTab.setLayout(self.getAFLayout())
        return afTab

    def initTooltips(self):
        self.profileCB.setToolTip('These are the profiles that the add-on will be active on.\nWhen set to "All", the add-on will be active on all profiles.')
        self.addRemProfile.setToolTip('Add/Remove a profile.')

        self.gMpb.setToolTip('Select the color for masculine gender nouns.')
        self.gFpb.setToolTip('Select the color for feminine gender nouns.')
        self.gNpb.setToolTip('Select the color for neutral gender nouns.')

        self.autoCSSJS.setToolTip('Enable or disable automatic CSS and JavaScript handling.\n Disabling this option is not recommended if you are not familiar with these technologies.')
        self.addLanguage.setToolTip('Adds the Migaku German note types for use with gender highlighting,\nand dictionary templates for each note type for easy card exporting with\nthe Migaku Dictionary Add-on.')
        self.profileAF.setToolTip("Profile: Select the profile.")
        self.noteTypeAF.setToolTip("Note Type: Select the note type.")
        self.cardTypeAF.setToolTip("Card Type: Select the card type.")
        self.fieldAF.setToolTip("Field: Select the field.")
        self.sideAF.setToolTip("Side: Select the side of the card where the display type setting will apply.")
        self.displayAF.setToolTip("Display Type: Select the display type,\nhover over a display type for fuctionality details.")
        

    def initHandlers(self):
        self.gMpb.clicked.connect(lambda: self.openDialogColor(self.languageMColor))
        self.gFpb.clicked.connect(lambda: self.openDialogColor(self.languageFColor))
        self.gNpb.clicked.connect(lambda: self.openDialogColor(self.languageNColor))
        
        self.addRemProfile.clicked.connect(lambda: self.addRemoveFromList(self.profileCB.currentText(), self.addRemProfile, self.currentProfiles, self.selectedProfiles, True))
        self.profileCB.currentIndexChanged.connect(lambda: self.profAltSimpTradChange(self.profileCB.currentText(), self.addRemProfile, self.selectedProfiles))
        self.addRemAlt.clicked.connect(lambda: self.addRemoveFromList(self.altCB.currentText(), self.addRemAlt, self.currentAlt, self.selectedAltFields, True))
        self.altCB.currentIndexChanged.connect(lambda: self.profAltSimpTradChange(self.altCB.currentText(), self.addRemAlt, self.selectedAltFields))
        self.addRemSimp.clicked.connect(lambda: self.addRemoveFromList(self.simpCB.currentText(), self.addRemSimp, self.currentSimp, self.selectedSimpFields, True))
        self.simpCB.currentIndexChanged.connect(lambda: self.profAltSimpTradChange(self.simpCB.currentText(), self.addRemSimp, self.selectedSimpFields))
        self.addRemTrad.clicked.connect(lambda: self.addRemoveFromList(self.tradCB.currentText(), self.addRemTrad, self.currentTrad, self.selectedTradFields, True))
        self.tradCB.currentIndexChanged.connect(lambda: self.profAltSimpTradChange(self.tradCB.currentText(), self.addRemTrad, self.selectedTradFields))
        self.altWithSep.clicked.connect(lambda: self.enableSep(self.altSep))
        self.altOW.clicked.connect(lambda: self.disableSep(self.altSep))
        self.altIfE.clicked.connect(lambda: self.disableSep(self.altSep))
        self.simpWithSep.clicked.connect(lambda: self.enableSep(self.simpSep))
        self.simpOW.clicked.connect(lambda: self.disableSep(self.simpSep))
        self.simpIfE.clicked.connect(lambda: self.disableSep(self.simpSep))
        self.tradWithSep.clicked.connect(lambda: self.enableSep(self.tradSep))
        self.tradOW.clicked.connect(lambda: self.disableSep(self.tradSep))
        self.tradIfE.clicked.connect(lambda: self.disableSep(self.tradSep))

        self.profileAF.currentIndexChanged.connect(self.profileChange )
        self.noteTypeAF.currentIndexChanged.connect(self.noteTypeChange)
        self.cardTypeAF.currentIndexChanged.connect(self.selectionChange)
        self.fieldAF.currentIndexChanged.connect(self.selectionChange)
        self.sideAF.currentIndexChanged.connect(self.selectionChange)
        self.displayAF.currentIndexChanged.connect(self.selectionChange)


        self.afTable.cellClicked.connect(self.loadSelectedRow)

        self.addEditAF.clicked.connect(self.performAddEdit)
        self.applyButton.clicked.connect(self.saveConfig)
        self.resetButton.clicked.connect(self.resetDefaults)
        self.cancelButton.clicked.connect(self.close)
        self.autoCSSJS.toggled.connect(self.handleAutoCSSJS)


    def handleAutoCSSJS(self):
        if self.autoCSSJS.isChecked():
            self.profileAF.setEnabled(True)
            self.noteTypeAF.setEnabled(True)
            self.cardTypeAF.setEnabled(True)
            self.fieldAF.setEnabled(True)
            self.sideAF.setEnabled(True)
            self.displayAF.setEnabled(True)
            self.addEditAF.setEnabled(True)
            self.afTable.setEnabled(True)

        else:
            self.profileAF.setEnabled(False)
            self.noteTypeAF.setEnabled(False)
            self.cardTypeAF.setEnabled(False)
            self.fieldAF.setEnabled(False)
            self.sideAF.setEnabled(False)
            self.displayAF.setEnabled(False)
            self.addEditAF.setEnabled(False)
            self.afTable.setEnabled(False)

    def profileChange(self):
        if self.initializing:
            return
        self.changingProfile = True
        self.noteTypeAF.clear()
        self.cardTypeAF.clear()
        self.fieldAF.clear()
        if self.profileAF.currentIndex() == 0:
            self.loadAllNotes()
        else:
            prof = self.profileAF.currentText()
            for noteType in self.ciSort(self.cA[prof]):
                    self.noteTypeAF.addItem(noteType)
                    self.noteTypeAF.setItemData(self.noteTypeAF.count() - 1, noteType + ' (Prof:' + prof + ')',Qt.ToolTipRole)
                    self.noteTypeAF.setItemData(self.noteTypeAF.count() - 1, prof + ':pN:' + noteType)
        self.loadCardTypesFields()
        self.changingProfile = False
        self.selectionChange()

    def noteTypeChange(self):
        if self.initializing:
            return
        if not self.changingProfile:
            self.cardTypeAF.clear()
            self.fieldAF.clear()
            self.loadCardTypesFields()
        self.selectionChange()

    def resetWindow(self):
        self.initializing = True
        self.buttonStatus = 0
        self.addEditAF.setText('Add')
        self.selectedRow = False
        self.clearAllAF()
        self.initActiveFieldsCB()
        self.initializing = False

    def selectionChange(self):
        if self.buttonStatus == 1:
            self.buttonStatus = 2
            self.addEditAF.setText('Save Changes')

    def performAddEdit(self):
        if self.buttonStatus == 1:
            self.resetWindow()
        else:
            profile = self.profileAF.currentText()
            nt = self.noteTypeAF.itemData(self.noteTypeAF.currentIndex()).split(':pN:')[1]
            ct = self.cardTypeAF.currentText()
            field = self.fieldAF.currentText()
            side = self.sideAF.currentText()
            dt = self.displayAF.currentText()
            if profile != '' and nt != '' and ct != '' and field != '' and side != '' and dt != '':
                if self.buttonStatus == 0:
                    self.addToList(profile, nt, ct, field, side, dt)
                elif self.buttonStatus == 2:
                    self.editEntry(profile, nt, ct, field, side, dt)

    def dupeRow(self, afList, profile, nt, ct, field, side,  dt, selRow = False):
        for i in range(afList.rowCount()):
            if selRow is not False:
                if i == selRow[0].row():
                    continue
            if (afList.item(i, 0).text() == profile or afList.item(i, 0).text() == 'All' or profile == "All") and afList.item(i, 1).text() == nt and afList.item(i, 2).text() == ct and afList.item(i, 3).text() == field and (afList.item(i, 4).text() == side or afList.item(i, 4).text() == 'Both' or side == "Both"):
                return i + 1;
        return False

    def addToList(self, profile, nt, ct, field, side, dt):
        afList = self.afTable
        found = self.dupeRow(afList, profile, nt, ct, field, side, dt)
        if found:
            miInfo('This row cannot be added because row #' + str(found) + 
                ' in the Active Fields List already targets this given field and side combination. Please review that entry and try again.', level = 'err')
        else:
            afList.setSortingEnabled(False)
            rc = afList.rowCount()
            afList.setRowCount(rc + 1)
            afList.setItem(rc, 0, QTableWidgetItem(profile))
            afList.setItem(rc, 1, QTableWidgetItem(nt))
            afList.setItem(rc, 2, QTableWidgetItem(ct))
            afList.setItem(rc, 3, QTableWidgetItem(field))
            afList.setItem(rc, 4, QTableWidgetItem(side))
            afList.setItem(rc, 5, QTableWidgetItem(dt))
            deleteButton =  QPushButton("X");
            deleteButton.setFixedWidth(40)
            deleteButton.clicked.connect(self.removeRow)
            afList.setCellWidget(rc, 6, deleteButton);
            afList.setSortingEnabled(True)

    def initEditMode(self):
        self.buttonStatus = 1
        self.addEditAF.setText('Cancel')

    def editEntry(self, profile, nt, ct, field, side, dt):
        afList = self.afTable
        rc = self.selectedRow
        found = self.dupeRow(afList, profile, nt, ct, field, side, dt, rc)
        if found:
            miInfo('This row cannot be edited in this manner because row #' + str(found) + 
                ' in the Active Fields List already targets this given field and side combination. Please review that entry and try again.', level = 'err')
        else:
            afList.setSortingEnabled(False)
            rc[0].setText(profile)
            rc[1].setText(nt)
            rc[2].setText(ct)
            rc[3].setText(field)
            rc[4].setText(side)
            rc[5].setText(dt)
            afList.setSortingEnabled(True) 
        self.resetWindow()   

    def removeRow(self):
        if miAsk('Are you sure you would like to remove this entry from the active field list?'):
            self.afTable.removeRow(self.afTable.selectionModel().currentIndex().row())
            self.resetWindow()

    def loadSelectedRow(self, row, col):
        afList = self.afTable
        prof = afList.item(row, 0).text()
        nt = afList.item(row, 1).text()
        ct = afList.item(row, 2).text()
        field = afList.item(row, 3).text()
        side = afList.item(row, 4).text()
        dt = afList.item(row, 5).text()
        if prof.lower() == 'all':
            loaded = self.unspecifiedProfileLoad( nt, ct, field, side, dt)
        else:
            loaded = self.specifiedProfileLoad(prof, nt, ct, field, side, dt)
        if loaded:
            self.initEditMode()
            self.selectedRow = [afList.item(row, 0), afList.item(row, 1), afList.item(row, 2), afList.item(row, 3), afList.item(row, 4), afList.item(row, 5)]
            

    def unspecifiedProfileLoad(self, nt, ct, field, side, dt):
        self.profileAF.setCurrentIndex(0)
        if self.findFirstNoteCardFieldMatch(nt, ct, field):
            index = self.sideAF.findText(side, Qt.MatchFixedString)
            if index >= 0:
                self.sideAF.setCurrentIndex(index)
            index = self.displayAF.findText(dt, Qt.MatchFixedString)
            if index >= 0:
                self.displayAF.setCurrentIndex(index)
            return True
        else: 
            return False

    def findFirstNoteCardFieldMatch(self, nt, ct, field):
        for i in range(self.noteTypeAF.count()):
            if self.noteTypeAF.itemText(i).startswith(nt):
                self.noteTypeAF.setCurrentIndex(i)
                ci = self.cardTypeAF.findText(ct, Qt.MatchFixedString)
                if ci >= 0:
                    fi = self.fieldAF.findText(field, Qt.MatchFixedString)
                    if fi >= 0:
                        self.noteTypeAF.setCurrentIndex(i)
                        self.cardTypeAF.setCurrentIndex(ci)
                        self.fieldAF.setCurrentIndex(fi)
                        return True
        return False

    def specifiedProfileLoad(self, prof, nt, ct, field, side, dt):
        index = self.profileAF.findText(prof, Qt.MatchFixedString)
        if index >= 0:
            self.profileAF.setCurrentIndex(index)
        index = self.noteTypeAF.findText(nt, Qt.MatchFixedString)
        if index >= 0:
            self.noteTypeAF.setCurrentIndex(index)
        index = self.cardTypeAF.findText(ct, Qt.MatchFixedString)
        if index >= 0:
            self.cardTypeAF.setCurrentIndex(index)
        index = self.fieldAF.findText(field, Qt.MatchFixedString)
        if index >= 0:
            self.fieldAF.setCurrentIndex(index)
        index = self.sideAF.findText(side, Qt.MatchFixedString)
        if index >= 0:
            self.sideAF.setCurrentIndex(index)
        index = self.displayAF.findText(dt, Qt.MatchFixedString)
        if index >= 0:
            self.displayAF.setCurrentIndex(index)
        return True

    def loadAltSimpTradFieldsCB(self):
        self.altCB.addItem('Clipboard')
        self.altCB.addItem('──────────────────')
        self.altCB.model().item(self.altCB.count() - 1).setEnabled(False)
        self.altCB.model().item(self.altCB.count() - 1).setTextAlignment(Qt.AlignCenter)
        self.altCB.addItems(self.allFields)
        self.simpCB.addItem('Clipboard')
        self.simpCB.addItem('──────────────────')
        self.simpCB.model().item(self.simpCB.count() - 1).setEnabled(False)
        self.simpCB.model().item(self.simpCB.count() - 1).setTextAlignment(Qt.AlignCenter)
        self.simpCB.addItems(self.allFields)
        self.tradCB.addItem('Clipboard')
        self.tradCB.addItem('──────────────────')
        self.tradCB.model().item(self.tradCB.count() - 1).setEnabled(False)
        self.tradCB.model().item(self.tradCB.count() - 1).setTextAlignment(Qt.AlignCenter)
        self.tradCB.addItems(self.allFields)

    def loadFieldsList(self, which):
        if which == 1:
            fl = self.currentAlt
            currentSelection = self.altCB.currentText()
            fs = self.config['SimpTradField']
        elif which == 2:
            fl = self.currentSimp
            currentSelection = self.simpCB.currentText()
            fs = self.config['SimplifiedField']
        else:
            fl = self.currentTrad
            currentSelection = self.tradCB.currentText()
            fs = self.config['TraditionalField']

        fieldList = fs.split(';')
        separator = False
        if len(fieldList) > 2:
            fields, addMode, separator = fieldList
        else:    
            fields, addMode = fieldList
        fields = fields.split(',')
        for idx, field in enumerate(fields):
            if field == 'clipboard':
                fields[idx] = 'Clipboard'
        if len(fields) == 1 and (fields[0].lower() == 'none' or fields[0].lower() == ''):
            fl.setText('<i>None currently selected.</i>')
        else:
            fl.setText('<i>' + ', '.join(fields) +'</i>')
        if  which == 1:
            self.selectedAltFields = fields
            if currentSelection in self.selectedAltFields:
                self.addRemAlt.setText('Remove')
        elif  which == 2:
            self.selectedSimpFields = fields
            if currentSelection in self.selectedSimpFields:
                self.addRemSimp.setText('Remove')
        else:
            self.selectedTradFields = fields
            if currentSelection in self.selectedTradFields:
                self.addRemTrad.setText('Remove')
        self.loadAddModes(addMode.lower(), separator, which)
                
    def loadAddModes(self, addMode, separator, which):
        if which == 1:
            add = self.altWithSep
            overwrite = self.altOW
            ifEmpty = self.altIfE
            sepB = self.altSep
        elif which == 2:
            add = self.simpWithSep
            overwrite = self.simpOW
            ifEmpty = self.simpIfE
            sepB = self.simpSep
        else:
            add = self.tradWithSep
            overwrite = self.tradOW
            ifEmpty = self.tradIfE
            sepB = self.tradSep
        if addMode == 'overwrite':
            overwrite.setChecked(True)
        elif addMode == 'add':
            add.setChecked(True)
        elif addMode == 'no':
            ifEmpty.setChecked(True)
        if separator:
            sepB.setText(separator)
        else:
            sepB.setText('<br>')
        if not add.isChecked():
            sepB.setEnabled(False)


    def addRemoveFromList(self, value, button, lWidget, vList, profiles = False):
        if button.text() == 'Remove':
            if value in vList:
                vList.remove(value)
                lWidget.setText('<i>'+', '.join(vList)+ '</i>')
                button.setText('Add')
                if len(vList) == 0 or (len(vList) == 1 and vList[0].lower() == 'none'):
                    lWidget.setText('<i>None currently selected.</i>')
        else:
            if profiles and value == 'All':
                vList.clear()
                vList.append('All')
                lWidget.setText('<i>All</i>')
                button.setText('Remove')
            else:
                if profiles:
                    if 'All' in vList:
                        vList.remove('All')
                if len(vList) == 1 and (vList[0].lower() == 'none' or vList[0] == ''):
                    vList.remove(vList[0])
                vList.append(value)
                lWidget.setText('<i>'+ ', '.join(vList) + '</i>')
                button.setText('Remove')

    def profAltSimpTradChange(self, value, button, vList):
        if value in vList:
            button.setText('Remove')
        else:
            button.setText('Add')


    def loadProfileCB(self):
        pcb = self.profileCB
        pcb.addItem('All')
        pcb.addItem('──────')
        pcb.model().item(pcb.count() - 1).setEnabled(False)
        pcb.model().item(pcb.count() - 1).setTextAlignment(Qt.AlignCenter)
        for prof in self.cA:
            pcb.addItem(prof)
            pcb.setItemData(pcb.count() -1, prof, Qt.ToolTipRole)

    def loadProfilesList(self):
        pl = self.currentProfiles
        profs = self.config['Profiles']
        if len(profs) == 0:
            pl.setText('<i>None currently selected.</i>')
        else:
            profl = []
            currentSelection = self.profileCB.currentText()
            for prof in  profs:
                if prof.lower() == 'all':
                    profl.append('All')
                    self.selectedProfiles = ['All']
                    if currentSelection == 'All':
                        self.addRemProfile.setText('Remove')
                        self.selectedProfiles = profl            
                        pl.setText('<i>All</i>')
                        return
                profl.append(prof)
                if currentSelection == prof:
                    self.addRemProfile.setText('Remove')
            self.selectedProfiles = profl            
            pl.setText('<i>' + ', '.join(profl) + '</i>')

    def getConfig(self):
        return self.mw.addonManager.getConfig(__name__)
    

    def saveAltSimpTradConfig(self):
        if len(self.selectedAltFields) < 1:
            altConfig = ['none']
        else:
            altConfig = [ ','.join(self.selectedAltFields)]
        if len(self.selectedSimpFields) < 1:
            simpConfig = ['none']
        else:
            simpConfig = [ ','.join(self.selectedSimpFields)]
        if len(self.selectedTradFields) < 1:
            tradConfig = ['none']
        else:
            tradConfig = [ ','.join(self.selectedTradFields)]
        if self.altWithSep.isChecked():
            altConfig.append('add')
            altConfig.append(self.altSep.text())
        elif self.altOW.isChecked():
            altConfig.append('overwrite')
        elif self.altIfE.isChecked():
            altConfig.append('no')
        if self.simpWithSep.isChecked():
            simpConfig.append('add')
            simpConfig.append(self.simpSep.text())
        elif self.simpOW.isChecked():
            simpConfig.append('overwrite')
        elif self.simpIfE.isChecked():
            simpConfig.append('no')

        if self.tradWithSep.isChecked():
            tradConfig.append('add')
            tradConfig.append(self.tradSep.text())
        elif self.tradOW.isChecked():
            tradConfig.append('overwrite')
        elif self.tradIfE.isChecked():
            tradConfig.append('no')
        return ';'.join(altConfig), ';'.join(simpConfig), ';'.join(tradConfig);

    def getColors(self):
        colors = [self.languageMColor.text(), self.languageFColor.text(), self.languageNColor.text()]
        return colors

    def saveActiveFields(self):
        afList = self.afTable
        afs = []
        for i in range(afList.rowCount()):
            prof = afList.item(i, 0).text()
            if prof == 'All':
                prof = 'all'
            nt = afList.item(i, 1).text()
            ct = afList.item(i, 2).text()
            field = afList.item(i, 3).text()
            side = afList.item(i, 4).text().lower()
            target = afList.item(i,  5).text()
            for key, value in self.displayTranslation.items():
                if value == target:
                    dt = key
                    break
            afs.append(';'.join([dt,prof,nt,ct,field,side]))
        return afs
 

    def saveConfig(self):
        languageColors = self.getColors()
        autoCSSJS = self.autoCSSJS.isChecked()
        fontSize = self.fontSize.value()
        newConf = self.makeNewConfig(self.saveActiveFields(), self.selectedProfiles, languageColors, autoCSSJS, fontSize)
        self.mw.addonManager.writeConfig(__name__, newConf)
        if self.addLanguage.isChecked(): 
            self.modeler.addModels()
        self.cssJSHandler.injectWrapperElements()
        self.hide()
        self.mw.MigakuGerman.refreshConfig()
        self.mw.updateMigakuGermanConfig()

    def makeNewConfig(self, activeFields, selectedProfiles, languageColors, autoCSSJS, fontSize):
        newConf = {"ActiveFields" : activeFields
        , "Profiles" : selectedProfiles
        , "LanguageGendersMFN" : languageColors
        , "AutoCssJsGeneration" : autoCSSJS
        , "FontSize": fontSize
        }
        return newConf

    def openDialogColor(self, lineEd):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            lineEd.setText(color.name())
            lineEd.setStyleSheet('color:' + color.name() + ';')


    def miQLabel(self, text, width):
        label = QLabel(text)
        label.setFixedHeight(30)
        label.setFixedWidth(width)
        return label

    def setupMainLayout(self):
        self.ml = QVBoxLayout()
        self.ml.addWidget(self.tabs)
        bl = QHBoxLayout()
        bl.addWidget(self.resetButton)
        bl.addStretch()
        bl.addWidget(self.cancelButton)
        bl.addWidget(self.applyButton)
        self.ml.addLayout(bl)
        self.innerWidget.setLayout(self.ml)


    def getSVGWidget(self,  name):
        widget = MigakuSVG(join(self.addonPath, 'icons', name))
        widget.setFixedSize(27,27)
        return widget

    def getAboutTab(self):
        tab_4 = QWidget()
        tab_4.setObjectName("tab_4")
        tab4vl = QVBoxLayout()
        migakuAbout = QGroupBox()
        migakuAbout.setTitle('Migaku')
        migakuAboutVL = QVBoxLayout()

        migakuAbout.setStyleSheet("QGroupBox { font-weight: bold; } ")
        migakuAboutText = QLabel("This an original Migaku add-on. Migaku seeks to be a comprehensive platform for acquiring foreign languages. The official Migaku website will be published soon!")
        migakuAboutText.setWordWrap(True);
        migakuAboutText.setOpenExternalLinks(True);
        migakuAbout.setLayout(migakuAboutVL)
        migakuAboutLinksTitle = QLabel("<b>Links<b>")
 
        migakuAboutLinksHL3 = QHBoxLayout()


        migakuInfo = QLabel("Migaku:")
        migakuInfoYT = self.getSVGWidget('Youtube.svg')
        migakuInfoYT.setCursor(QCursor(Qt.PointingHandCursor))

        migakuInfoTW = self.getSVGWidget('Twitter.svg')
        migakuInfoTW.setCursor(QCursor(Qt.PointingHandCursor))


        migakuPatreonIcon = self.getSVGWidget('Patreon.svg')
        migakuPatreonIcon.setCursor(QCursor(Qt.PointingHandCursor))
        migakuAboutLinksHL3.addWidget(migakuInfo)
        migakuAboutLinksHL3.addWidget(migakuInfoYT)
        migakuAboutLinksHL3.addWidget(migakuInfoTW)
        migakuAboutLinksHL3.addWidget(migakuPatreonIcon)
        migakuAboutLinksHL3.addStretch()

        migakuAboutVL.addWidget(migakuAboutText)
        migakuAboutVL.addWidget(migakuAboutLinksTitle)
        migakuAboutVL.addLayout(migakuAboutLinksHL3)
        
        migakuContact = QGroupBox()
        migakuContact.setTitle('Contact Us')
        migakuContactVL = QVBoxLayout()
        migakuContact.setStyleSheet("QGroupBox { font-weight: bold; } ")
        migakuContactText = QLabel("If you would like to report a bug or contribute to the add-on, the best way to do so is by starting a ticket or pull request on GitHub. If you are looking for personal assistance using the add-on, check out the Migaku Patreon Discord Server.")
        migakuContactText.setWordWrap(True)

        gitHubIcon = self.getSVGWidget('Github.svg')
        gitHubIcon.setCursor(QCursor(Qt.PointingHandCursor))
        
        migakuThanks = QGroupBox()
        migakuThanks.setTitle('A Word of Thanks')
        migakuThanksVL = QVBoxLayout()
        migakuThanks.setStyleSheet("QGroupBox { font-weight: bold; } ")
        migakuThanksText = QLabel("Thanks so much to all Migaku supporters! I would not have been able to develop this add-on or any other Migaku project without your support!")
        migakuThanksText.setOpenExternalLinks(True);
        migakuThanksText.setWordWrap(True);
        migakuThanksVL.addWidget(migakuThanksText)

        migakuContactVL.addWidget(migakuContactText)
        migakuContactVL.addWidget(gitHubIcon)
        migakuContact.setLayout(migakuContactVL)
        migakuThanks.setLayout(migakuThanksVL)
        tab4vl.addWidget(migakuAbout)
        tab4vl.addWidget(migakuContact)
        tab4vl.addWidget(migakuThanks)
        tab4vl.addStretch()
        tab_4.setLayout(tab4vl)

        migakuPatreonIcon.clicked.connect(lambda: openLink('https://www.patreon.com/Migaku'))
        migakuInfoYT.clicked.connect(lambda: openLink('https://www.youtube.com/c/ImmerseWithYoga'))
        migakuInfoTW.clicked.connect(lambda: openLink('https://twitter.com/Migaku_Yoga'))
        gitHubIcon.clicked.connect(lambda: openLink('https://github.com/migaku-official'))
        return tab_4

    def clearAllAF(self):
        self.profileAF.clear()
        self.noteTypeAF.clear()
        self.cardTypeAF.clear()
        self.fieldAF.clear()
        self.sideAF.clear()
        self.displayAF.clear()


    def initActiveFieldsCB(self):
        aP = self.profileAF
        aP.addItem('All')
        aP.addItem('──────────────────')
        aP.model().item(aP.count() - 1).setEnabled(False)
        aP.model().item(aP.count() - 1).setTextAlignment(Qt.AlignCenter)
        self.loadAllProfiles()  
        self.loadCardTypesFields()
        for key, value in self.sides.items():
            self.sideAF.addItem(key)
            self.sideAF.setItemData(self.sideAF.count() - 1, value ,Qt.ToolTipRole)
        for key, value in self.displayTypes.items():
            self.displayAF.addItem(key)
            self.displayAF.setItemData(self.displayAF.count() - 1, value[1] ,Qt.ToolTipRole)
            self.displayAF.setItemData(self.displayAF.count() - 1, value[0])


    def loadAllProfiles(self):
        if not self.sortedProfiles and not self.sortedNoteTypes:
            profL = []
            noteL = []
            for prof in self.cA:
                profL.append(prof)
                for noteType in self.cA[prof]:
                    noteL.append([noteType + ' (Prof:' + prof + ')', prof + ':pN:' + noteType])
            self.sortedProfiles = self.ciSort(profL)
            self.sortedNoteTypes = sorted(noteL, key=itemgetter(0))
        aP = self.profileAF
        for prof in self.sortedProfiles:
            aP.addItem(prof)
            aP.setItemData(aP.count() -1, prof, Qt.ToolTipRole)
        self.loadAllNotes()

    def loadAllNotes(self):
        for noteType in self.sortedNoteTypes:
            self.noteTypeAF.addItem(noteType[0])
            self.noteTypeAF.setItemData(self.noteTypeAF.count() - 1, noteType[0],Qt.ToolTipRole)
            self.noteTypeAF.setItemData(self.noteTypeAF.count() - 1, noteType[1])

    def loadCardTypesFields(self):
        curProf, curNote = self.noteTypeAF.itemData(self.noteTypeAF.currentIndex()).split(':pN:')     
        for cardType in self.cA[curProf][curNote]['cardTypes']:
            self.cardTypeAF.addItem(cardType)
            self.cardTypeAF.setItemData(self.cardTypeAF.count() - 1, cardType,Qt.ToolTipRole)
        for field in self.cA[curProf][curNote]['fields']:
            self.fieldAF.addItem(field)
            self.fieldAF.setItemData(self.fieldAF.count() - 1, field,Qt.ToolTipRole)
        return

    def loadActiveFields(self):
        afs = self.config['ActiveFields']
        for af in afs:
            afl = af.split(';')
            dt = afl[0].lower()
            if dt in self.displayTranslation:
                prof = afl[1]
                if prof == 'all':
                    prof = 'All'
                self.addToList(prof, afl[2], afl[3], afl[4], afl[5][0].upper() + afl[5][1:].lower() , self.displayTranslation[dt])