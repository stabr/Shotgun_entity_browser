'''
author: Dmitry Stabrov
mailto: syrbor@gmail.com
------------------------------
description: Collects a list of Shotgun entities and their parameters
    and displays selected parameters in a way convenient to
    compose a Shotgun request. For instance - a "find" command.
------------------------------
Usage:
    You can use a keyboard or mouse in a common way to navigate through.
'''

import sys
from os.path import realpath, dirname

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from pprint import pprint

scripts_path = dirname(realpath(__file__))
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

import shotgun_api3
from settings import URL, USER, KEY, CACERTS

# Your Shotgun project id
shotgun_project_id = 0

class ShotgunEntityBrowser(QListWidget):
    '''
     Displays a list of Shotgun entities
     or parameters of the selected entity
    '''
    def __init__(self, duplex):
        super(ShotgunEntityBrowser, self).__init__()
        self.setWindowTitle('Entities')
        self.resize(300, 700)
        # var
        self.dlx = duplex
        self.prj = {'type': 'Project', 'id': shotgun_project_id}
        self.sg = self.connect_to_shotgun()
        self.find_text = ''
        self.context = 'entity'
        self.obj = ''
        # fill this with list of entities
        self.entities()
        # Actions
        self.itemDoubleClicked.connect(lambda: self.get_params())

    def connect_to_shotgun(self):
        '''
         URL - your studio Shotgun url
         USER can be a human login or a script name
         KEY - a password in a human case
        '''
        from shotgun_api3 import Shotgun
        sg = Shotgun(URL, USER, KEY, ca_certs=CACERTS)
        return sg

    def fill(self, lst, flag):
        '''
         Fills the List Widget with a given list (lst)
        '''
        self.clear()
        for i in lst:
            itm = QListWidgetItem(i)
            itm.setData(Qt.UserRole, flag)
            self.addItem(itm)

    def entities(self):
        '''
         Returns a list of Shotgun entities
        '''
        self.context = 'entity'
        self.find_text = ''
        self.obj = ''
        entity_lst = sorted(self.sg.schema_entity_read(self.prj).keys())
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.fill(entity_lst, 'entity')

    def get_params(self):
        '''
         Returns a list of parameters of the selected entity
        '''
        self.context = 'fields'
        self.find_text = ''
        if self.obj:
            entity = self.obj
        else:
            itm = self.currentItem()
            if not itm:
                print('No items selected')
                return
            if not itm.data(Qt.UserRole) == 'entity':
                return
            entity = itm.text()
            self.obj = entity
        entity_fields = sorted(self.sg.schema_field_read(entity, '', self.prj).keys())
        self.dlx.setWindowTitle(entity)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.fill(entity_fields, 'field')

    def keyPressEvent(self, event):
        # Return to the previous context
        if event.key() == Qt.Key_Escape:
            if self.obj and self.find_text:
                self.get_params()
            else:
                self.entities()
        # Filter an appropriate entity or
        # parameter with printed characters
        elif event.key() in range(128):
            self.find_text += event.text()
            for j in range(self.count()):
                if self.find_text.lower() not in self.item(j).text().lower():
                    self.item(j).setHidden(True)
        # Return to the previous context or a filtered result
        elif event.key() == Qt.Key_Backspace:
            self.find_text = self.find_text[:-1]
            back = True
            for itm in self.findItems(self.find_text, Qt.MatchContains):
                if itm.isHidden():
                    back = False
                itm.setHidden(False)
            if back:
                self.entities()
        # Display selected parameters as a data dictionary
        elif QApplication.keyboardModifiers() == Qt.AltModifier:
            if event.key() == Qt.Key_Return:
                # print(f'"{self.obj}"\ndata = ')
                text = 'data = ' + {
                    str(i.text()):None for i in self.selectedItems()}.__str__()
                self.dlx.display.setText(text)
        # Display selected parameters as a fields
        elif QApplication.keyboardModifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Return:
                text = 'fields = ' + [
                    str(i.text()) for i in self.selectedItems()].__str__()
                self.dlx.display.setText(text)
        # Display selected parameters as a filters list
        elif event.key() == Qt.Key_Return:
            if self.obj:
                text = 'filters = ' + [
                    [str(i.text()), 'is', 'value']
                    for i in self.selectedItems()].__str__()
                self.dlx.display.setText(text)
            else:
                self.get_params()
        super(ShotgunEntityBrowser, self).keyPressEvent(event)


class DuplexWidget(QWidget):
    text = '''
        Display selected parameters as
        a filters list - "Return"
        a fields list - "Ctrl" + "Return"
        a data dictionary - "Alt" + "Return"
    '''
    def __init__(self):
        super(DuplexWidget, self).__init__()
        main_lay = QHBoxLayout(self)
        self.browser = ShotgunEntityBrowser(self)
        self.display = QTextEdit()
        main_lay.addWidget(self.browser)
        main_lay.addWidget(self.display)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        self.setLayout(main_lay)
        self.display.setText(self.text)
        self.resize(500, 600)

    def keyPressEvent(self, event):
        return self.browser.event(event)


if __name__ == '__main__':
    a = QApplication([])
    browser = DuplexWidget()
    browser.show()
    a.exec_()
