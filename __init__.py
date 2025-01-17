""" Anki autofiller """

import sys
import subprocess

code = """
import sys
print(";".join(sys.path))
"""

newpath = subprocess.check_output(["python", "-c", code]).decode('utf-8').split(';')

for item in newpath:
    sys.path.append(item)
    
from anki.hooks import addHook
import hashlib
from german_anki.conjugator import conjugate_verb, declenations_adj, declenations_noun
from bs4 import BeautifulSoup
from aqt import mw
from aqt.editor import Editor
from aqt.utils import showInfo
import os
    
def tts(text, prefix = None):
    text = BeautifulSoup(text, "lxml").text # parsing out all html tags
    if prefix is not None:
        text = prefix + ' ' + text
    filename = "german-gtts-{0}.mp3".format(hashlib.md5(text.encode('utf-8')).hexdigest())

    command = """python ~/.local/share/Anki2/addons21/german_anki/google_tts.py "{0}" {1}""".format(text, filename)
    os.system(command)

    return "[sound:{0}]".format(filename)

def add_sound_to_field(note, field, prefix=None):
    if note[field]:
        note[field + ' Sound'] = tts(note[field], prefix = prefix)

def comma_join(lst):
    return ", ".join(lst)

GERMAN_NOUN_NAME = "German Nouns"
GERMAN_ADJV_NAME = "German Adjectives"
GERMAN_VERB_NAME = "German Verbs"
OTHER_GERMAN_NOTES = ["German General", "German Phrases"]

REFLEXIVE_PRONOUN = {
        'ich': 'mich',
        'du': 'dich',
        'er;sie;es': 'sich',
        'ihr': 'euch',
        'wir': 'uns'
        }

def format_noun(noun, gender, case):
    article = {
            ('nom', 'm'): 'der',
            ('nom', 'f'): 'die',
            ('nom', 'n'): 'das',
            ('gen', 'm'): 'des',
            ('gen', 'n'): 'des'
            }

    if gender == 'pl' or gender == 'adj':
        return """<span class="{1}">{0}</span>""".format(noun, gender)

    return """<span class="{1}">{2} {0}</span>""".format(noun, gender, article[(case, gender)])

def onFocusLost(flag, note, fidx):
    note_type = note.model()['name']
    field_indices = {card: i for i, card in enumerate(mw.col.models.fieldNames(note.model()))}

    if note_type == GERMAN_ADJV_NAME:
        if field_indices['Auto'] == fidx and not note['Manual Override']:
            adj_list = note['Auto'].split(',')
            adj_decl_list = []
            for adj in adj_list:
                adj = adj.strip()
                decl = declenations_adj(adj)
                if decl:
                    adj_decl_list.append(decl)

            entries = []
            for decl in adj_decl_list:
                if decl['word']:
                    entries.append(decl['word'])

            note['Predicative'] = comma_join(entries)

            entries = []
            for decl in adj_decl_list:
                if decl['comparative']:
                    entries.append(decl['comparative'])

            note['Comparative'] = comma_join(entries)

            entries = []
            for decl in adj_decl_list:
                if decl['superlative']:
                    entries.append("am " + decl['superlative'] + "en")

            note['Superlative'] = comma_join(entries)

            add_sound(note)
            
            return True

    if note_type == GERMAN_NOUN_NAME:
        if field_indices['Auto'] == fidx and not note['Manual Override']:
            noun_list = note['Auto'].split(',')
            noun_decl_list = []
            for noun in noun_list:
                noun = noun.strip()
                decl = declenations_noun(noun)
                if decl:
                    noun_decl_list.append(decl)

            entries = []
            for decl in noun_decl_list:
                if decl['gender'] != 'pl':
                    entries.append(format_noun(decl['word'], decl['gender'], 'nom'))
            note['Nominative Singular'] = comma_join(entries)

            entries = []
            for decl in noun_decl_list:
                plural = None
                if decl['plural'] != None:
                    plural = decl['plural']
                elif decl['plural_ending'] != None:
                    plural = decl['word'] + decl['plural_ending']

                if plural:
                    entries.append(format_noun(plural, 'pl', 'nom'))

            note['Nominative Plural'] = comma_join(entries)

            entries = []
            for decl in noun_decl_list:
                plural = None
                if decl['gender'] == 'm' or decl['gender'] == 'n':
                    gen = decl['word'] + decl['genitive_ending']
                    entries.append(format_noun(gen, decl['gender'], 'gen'))

            note['Genitive Singular'] = comma_join(entries)

            add_sound(note)

            return True

    if note_type == GERMAN_VERB_NAME:
        if field_indices['Auto'] == fidx and not note['Manual Override']:
            try:
                verb_list = note['Auto'].split(',')
                verb_conj_list = []
                for verb in verb_list:
                    verb = verb.strip()
                    parts = verb.split(' ')
                    verb_conj = conjugate_verb(parts[-1])
                    if verb_conj:
                        if len(parts) > 1 and parts[0] == "sich":
                            verb_conj['reflexive'] = True
                        else:
                            verb_conj['reflexive'] = False

                        verb_conj_list.append(verb_conj)

                print(verb_conj_list)

                """ Processing infinitives """
                
                entries = []
                for verb_conj in verb_conj_list:
                    entry = ""
                    if verb_conj['reflexive']:
                        entry += "sich "

                    if 'prefix' in verb_conj:
                        entry += verb_conj['prefix'] + '|'

                    entry += verb_conj['infinitive_no_prefix']

                    entries.append(entry)

                note['Infinitive'] = comma_join(entries)

                """ Processing present tense """

                for pronoun in ['ich', 'du', 'er;sie;es', 'wir', 'ihr']:
                    entries = []
                    for verb_conj in verb_conj_list:
                        entry = verb_conj[pronoun]

                        if verb_conj['reflexive']:
                            entry += " " + REFLEXIVE_PRONOUN[pronoun]

                        if 'prefix' in verb_conj:
                            entry += " " + verb_conj['prefix']
                        entries.append(entry)

                    note[pronoun] = comma_join(entries)

                """ Processing perfect tense """

                entries = []
                for verb_conj in verb_conj_list:
                    entry = verb_conj['aux_verb']

                    if verb_conj['reflexive']:
                        entry += " sich"

                    entry += " " + verb_conj['past_participle']

                    entries.append(entry)

                note['Perfect'] = comma_join(entries)

                """ Processing imperfect tense """

                entries = []
                for verb_conj in verb_conj_list:
                    entry = verb_conj['imperfect']

                    if verb_conj['reflexive']:
                        entry += " mich"

                    if 'prefix' in verb_conj:
                        entry += " " + verb_conj['prefix']

                    entries.append(entry)

                note['Imperfect'] = comma_join(entries)

                """ Processing konjunctiv tense """

                entries = []
                for verb_conj in verb_conj_list:
                    entry = verb_conj['konjunctiv']
                    if verb_conj['reflexive']:
                        entry += " mich"

                    if 'prefix' in verb_conj:
                        entry += " " + verb_conj['prefix']

                    entries.append(entry)

                note['Konjunctiv'] = comma_join(entries)

                """ Processing imperative tense """

                entries = []
                for verb_conj in verb_conj_list:
                    for entry in verb_conj['imperative_forms']:
                        if verb_conj['reflexive']:
                            entry += " dich"

                        if 'prefix' in verb_conj:
                            entry += " " + verb_conj['prefix']

                        entries.append(entry)

                note['Imperative'] = comma_join(entries)
            except AttributeError:
                showInfo("scraping error")
            
            add_sound(note)

            return True

    if note_type in [GERMAN_VERB_NAME, GERMAN_ADJV_NAME, GERMAN_NOUN_NAME] + OTHER_GERMAN_NOTES:
        if (fidx == field_indices['Manual Override'] and note['Manual Override'] == 'a') \
                or note_type in OTHER_GERMAN_NOTES:

            add_sound(note)
        
            return True

    return flag

def strip_parentheses(text):
    new_text = ""
    include = True
    for char in text:
        if char == '(':
            include = False

        if include:
            new_text += char

        if char == ')':
            include = True

    return new_text

def add_sound(note):
    note_type = note.model()['name']
    field_indices = {card: i for i, card in enumerate(mw.col.models.fieldNames(note.model()))}

    if note_type == GERMAN_ADJV_NAME:
        for field in ["Predicative", "Comparative", "Superlative"]:
            add_sound_to_field(note, field)

    if note_type == GERMAN_NOUN_NAME:
        for field in ["Nominative Singular", "Nominative Plural"]:
            add_sound_to_field(note, field)

        stripped_gen = strip_parentheses(note['Genitive Singular'])
        note['Genitive Singular Sound'] = tts(stripped_gen)

    if note_type == GERMAN_VERB_NAME:
        field_and_prefixes = [
                ("ich", "ich"),
                ("du", "du"),
                ("er;sie;es", "es"),
                ("wir", "wir"),
                ("ihr", "ihr"),
                ("Perfect", None),
                ("Imperfect", "ich"),
                ("Imperative", None),
                ("Konjunctiv", "ich")
                ]
        for field, prefix in field_and_prefixes:
            if prefix:
                entries = []
                for entry in note[field].split(", "):
                    entry = prefix + " " + entry
                    entries.append(entry)

                note[field + " Sound"] = tts(comma_join(entries))
            else:
                add_sound_to_field(note, field)

        """ Replacing | for generating the infinitive """
        note['Infinitive Sound'] = tts(note['Infinitive'].replace("|", ""))

    if note_type in OTHER_GERMAN_NOTES:
        add_sound_to_field(note, "German")

addHook("editFocusLost", onFocusLost)

def clearFields(self):
    for field in mw.col.models.fieldNames(self.note.model()):
        self.note[field] = ''
    self.note.flush()
    mw.reset()

def noteStyle(self):
    self.web.eval("""wrap('<span class="inlinenote">', '</span>');""")

def onSetupShortcuts(cuts, self):
    cuts += [("Ctrl+Y", self.clearFields),
             ("Ctrl+Shift+W", self.noteStyle)]
    
Editor.noteStyle = noteStyle
Editor.clearFields = clearFields
addHook("setupEditorShortcuts", onSetupShortcuts)
