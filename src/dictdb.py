# -*- coding: utf-8 -*-
#


import sqlite3
import os.path
import re



class DictDB:
    conn = None
    c = None
    addon_path = os.path.dirname(__file__)

    def __init__(self):
        # try:
        #     from aqt import mw

        db_file = os.path.join(self.addon_path, "db", "language_dict.sqlite")
        # except:
        #     db_file = "db/language_dict.sqlite"

        self.conn=sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        # self.insertIntoDb()
    

    def removeParentheses(self, text):
        return re.sub(r'\(.+?\)', '', text)

    def insertIntoDb(self):
        import json
        poses = {    
            "v":"v",
            "adj":"adj",
            "adv":"adv",
            "art":"art",
            "card":"cnum",
            "circp":"circ",
            "conj":"conj",
            "demo":"demo",
            "indef":"ind",
            "intj":"int",
            "ord":"onum",
            "nn":"n",
            "nnp":"pn",
            "poss":"pos",
            "postp":"poss",
            "prp":"per",
            "prep":"prep",
            "prepart":"prepart",
            "proadv":"proadv",
            "prtkl":"part",
            "rel":"rel",
            "trunc":"trunc",
            "vpart":"vpart",
            "wpadv":"advpro",
            "wpro":"pro",
            "zu":"zu"
        }
        path = os.path.join(self.addon_path, "db", "wordData.json")
        with open(path, encoding='utf-8') as fh:
            data = fh.read()
            jsonFile = json.loads(data)
        count = 1
        for word, entry in jsonFile.items():
            # if count > 10:
            #     return
            count += 1
            word = self.removeParentheses(word)
            root = self.removeParentheses(entry['lemma'])
            pos = poses[entry["type"].lower()]
            gender = 0
            if 'gender' in entry:
                genderText = entry['gender'][0]
                if genderText == 'neut' or genderText == "noGender":
                    gender = 1
                elif genderText == "fem":
                    gender = 2
                elif genderText == "masc":
                    gender = 3
            self.pushDeclension(word, root, pos, gender)
        # print(data)
        self.commitChanges()
        print("FINISHED ADDING DB")

    def closeConnection(self):
        self.c.close()
        self.conn.close()
        self = False


    def pushDeclension(self, declension, root, pos, gender):
        self.c.execute('INSERT INTO declensions (declension, root, pos, gender) VALUES (?, ?, ?, ?);', (declension, root, pos, gender))
        

    def commitChanges(self):
        self.conn.commit()


    def getDeclensionMatch(self, word):
        print("LOOKING FOR")
        print(word)
        self.c.execute("select root, pos, gender from declensions where declension=?;", (word,) )
        try:
            result = self.c.fetchone()
            return result
        except:
            return None

 