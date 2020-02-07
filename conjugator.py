""" Uses scraped data to conjugate and declenate German verbs, nouns 
and adjectives """

import dataset

DB = dataset.connect('sqlite:///.local/share/Anki2/addons21/german_anki/german.db')
VERBS = DB.get_table('verb')
NOUNS = DB.get_table('noun')
ADJVS = DB.get_table('adjective')

def conjugate_verb(verb, reflexive):
    data = VERBS.find_one(word=verb)

    if data is None:
        return {}

    conj = {
        'Infinitive': data['word'],
        'aux': data['auxillary_verb'],
        'prefix': data['seperable_prefix'],
        }

    conj['Past Participle'] = conj['prefix'] + data['past_participle']

    if data['type'] == 'de-conj-weak-eln':
        conj['Present 1'] = data['present_stem'] + 'le'
        conj['Present 2 Sing'] = data['present_second_third_stem'] + 'elst'
        conj['Present 2 Plural'] = data['present_stem'] + 'elt'
        conj['Present 3'] = data['present_second_third_stem'] + 'elt'
        conj['Present 1 3 Plural 2 Formal'] = data['present_stem'] + 'eln'
        conj['Conjunctive II 1'] = data['conjunctive_ii_stem'] + 'le'
        conj['Imperfect 1'] = data['past_stem'] + 'elte'
        conj['Imperative Singular'] = [data['present_stem'] + 'le']

    elif data['type'] == 'de-conj-weak-ern':
        conj['Present 1'] = data['present_stem'] + 'ere'
        conj['Present 2 Sing'] = data['present_second_third_stem'] + 'erst'
        conj['Present 2 Plural'] = data['present_stem'] + 'ert'
        conj['Present 3'] = data['present_second_third_stem'] + 'ert'
        conj['Present 1 3 Plural 2 Formal'] = data['present_stem'] + 'ern'
        conj['Conjunctive II 1'] = data['conjunctive_ii_stem'] + 'ere'
        conj['Imperfect 1'] = data['past_stem'] + 'erte'
        conj['Imperative Singular'] = [data['present_stem'] + 're']
    else:
        conj['Present 1'] = data['present_stem'] + 'e'

        conj['Present 2 Sing'] = data['present_second_third_stem']
        conj['Present 2 Plural'] = data['present_stem']
        conj['Present 3'] = data['present_second_third_stem']
        if data['e_on_present_second_third']:
            conj['Present 2 Sing'] += 'e'
            conj['Present 2 Plural'] += 'e'
            conj['Present 3'] += 'e'
        if data['present_second_ends_t'] or data['esset_stem_ending']:
            conj['Present 2 Sing'] += 't'
        else:
            conj['Present 2 Sing'] += 'st'
        conj['Present 2 Plural'] += 't'
        conj['Present 3'] += 't'
        conj['Present 1 3 Plural 2 Formal'] = data['present_stem'] + 'en'

        conj['Conjunctive II 1'] = data['conjunctive_ii_stem'] + 'e'

        conj['Imperfect 1'] = data['past_stem']
        if data['e_on_present_second_third']:
            conj['Imperfect 1'] += 'e'
        if not data['no_te_past_stem']:
            conj['Imperfect 1'] += 'te'

        if data['imperative_uses_infinite_vowel']:
            imp_stem = data['present_stem']
        else:
            imp_stem = data['present_second_third_stem']

        if data['no_e_imperative']:
            conj['Imperative Singular'] = [imp_stem]
        elif data['e_on_present_second_third'] or imp_stem[-2:] == 'ig':
            conj['Imperative Singular'] = [imp_stem + 'e']
        else:
            conj['Imperative Singular'] = [imp_stem, imp_stem + 'e']

    if reflexive:
        conj['Infinitive'] = 'sich ' + conj['Infinitive']
        conj['Present 1'] += ' mich'
        conj['Present 2 Sing'] += ' dich'
        conj['Present 3'] += ' sich'
        conj['Present 2 Plural'] += ' euch'
        conj['Present 1 3 Plural 2 Formal'] += ' uns'
        conj['Imperfect 1'] += ' mich'
        conj['Conjunctive II 1'] += ' mich'

        conj['Past Participle'] = 'sich ' + conj['Past Participle']

        conj['Imperative Singular'] = [form + ' dich' for form in conj['Imperative Singular']]
    
    if conj['prefix']:
        for field in [
                'Present 1', 'Present 2 Sing', 'Present 2 Plural', 'Present 1 3 Plural 2 Formal',
                'Present 3', 'Imperfect 1', 'Conjunctive II 1'
                ]:
                conj[field] += ' ' + conj['prefix']

        conj['Imperative Singular'] = [form + ' ' + conj['prefix'] for form in conj['Imperative Singular']]

    return conj

def declenations_noun(noun):
    data = NOUNS.find_one(word=noun)
    decl = {}

    if data is None:
        return {}

    if data['type'] == 'de-decl-noun-m':
        gender = 'm'
    if data['type'] == 'de-decl-noun-f':
        gender = 'f'
    if data['type'] == 'de-decl-noun-n':
        gender = 'n'
    if data['type'] == 'de-decl-noun-pl':
        gender = 'pl'

    decl['Gender'] = gender

    if gender == 'pl':
        decl['Nominative Plural'] = noun
    if gender == 'm':
        decl['Nominative Singular'] = noun
    if gender == 'f':
        decl['Nominative Singular'] = noun
    if gender == 'n':
        decl['Nominative Singular'] = noun

    if gender == 'm' or gender == 'n':
        ending = data['genitive_singular_ending']

        if ending == '(e)s':
            decl['Genitive Singular Forms'] = [noun + 'es', noun + 's']
        else:
            decl['Genitive Singular Forms'] = [noun + ending]

    if gender == 'f':
        decl['Genitive Singular Forms'] = [noun]

    if gender in ['m', 'f', 'n']:
        if data['plural'] is not None:
            if data['plural'] != '-':
                decl['Nominative Plural'] = data['plural']
        elif data['plural_ending'] is not None:
            decl['Nominative Plural'] = noun + data['plural_ending']

    return decl

def declenations_adj(adj):
    data = ADJVS.find_one(word=adj)

    if data is None:
        return {}

    decl = {'lemma': adj}
    if data['stem']:
        stem = data['stem']
        if stem != adj:
            decl['stem'] = stem
    if data['pred']:
        pred = data['pred']
        if pred != adj:
            decl['pred'] = pred
    if data['comparative']:
        decl['comparative'] = data['comparative']
    if data['superlative']:
        decl['superlative'] = data['superlative']

    return decl

