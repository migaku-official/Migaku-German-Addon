# -*- coding: utf-8 -*-
# 

import aqt
from aqt.qt import *
from os.path import dirname, join

addon_path = dirname(__file__)

def miInfo(text, parent=False, level = 'msg', day = True):
    if level == 'wrn':
        title = "Migaku German Warning"
    elif level == 'not':
        title = "Migaku German Notice"
    elif level == 'err':
        title = "Migaku German Error"
    else:
        title = "Migaku German"
    if parent is False:
        parent = aqt.mw.app.activeWindow() or aqt.mw
    icon = QIcon(join(addon_path, 'icons', 'migaku.png'))
    mb = QMessageBox(parent)
    if not day:
        mb.setStyleSheet(" QMessageBox {background-color: #272828;}")
    mb.setText(text)
    mb.setWindowIcon(icon)
    mb.setWindowTitle(title)
    b = mb.addButton(QMessageBox.Ok)
    b.setFixedSize(100, 30)
    b.setDefault(True)

    return mb.exec_()


def miAsk(text, parent=None, day=True):

    msg = QMessageBox(parent)
    msg.setWindowTitle("Migaku German")
    msg.setText(text)
    icon = QIcon(join(addon_path, 'icons', 'migaku.png'))
    b = msg.addButton(QMessageBox.Yes)
    b.setFixedSize(100, 30)
    b.setDefault(True)
    c = msg.addButton(QMessageBox.No)
    c.setFixedSize(100, 30)
    if not day:
        msg.setStyleSheet(" QMessageBox {background-color: #272828;}")
    msg.setWindowIcon(icon)
    msg.exec_()
    if msg.clickedButton() == b:
        return True
    else:
        return False

