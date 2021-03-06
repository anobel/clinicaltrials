#!../clinicaltrials/env/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ctapp import app
import flask, time, re, random, uuid, json, warnings
from flask import request, url_for
from hashlib import md5
from collections import defaultdict, Counter
from string import punctuation 
from datetime import datetime

# active learning
import word2vec
from nltk import RegexpParser

# document similarity
from gensim import corpora, models, similarities, utils
import gensim, simserver

# SQLAlchemy setup
from sqlalchemy import create_engine
from sqlalchemy.sql import text, func, select, and_, or_, not_, desc, bindparam
from connect import mysqlusername, mysqlpassword, mysqlserver, mysqldbname
from db_tables import metadata, InstitutionDescription, InstitutionLookup, ConditionDescription, \
    ConditionLookup, InstitutionSponsors, InstitutionFacilities, InstitutionRatings, TrialSummary, \
    Interventions, Conditions, ConditionSynonym, ClinicalStudy, Investigators, TrialRatings, \
    Users, MeshAssignStaging, UserHistoryMesh, CriteriaConceptStaging, UserHistoryCriteria, \
    Sponsors, Facilities, TrialPublications, CriteriaText, CriteriaTagged, CriteriaConceptLookup, \
    ConceptTerms, CriteriaConcept, ConceptPredictors, ConceptPredictorsReject, ConceptTerms, \
    ConceptTermsReject, ConditionBrowse, MeshThesaurus, ZipLatlong, ZipFacilities




# initialize database
def initializeDB(user,pwd,server,dbname):
    engine = create_engine('mysql://%s:%s@%s/%s?charset=utf8' % (user,pwd,server,dbname),
                           pool_recycle=3600)
    conn = engine.connect()
    metadata.create_all(engine)
    return engine, conn

mysqlserver = 'localhost'
engine, conn = initializeDB(mysqlusername, mysqlpassword, mysqlserver, mysqldbname)

# initialize global variables
app.secret_key = str(uuid.uuid4())

skip_term_list = {'month', 'months', 'patient', 'patients', 'history', 'day', 'days',
                  'year', 'years', 'week', 'weeks', 'subject', 'subjects', 'study', 'inclusion criteria', 'exclusion criteria',
                  'history of', 'patients with', 'age', 'investigator', 'use', 'evidence', 'women', 'men', 'woman', 'man',
                  'female', 'male', 'enrollment', 'time', 'informed consent', 'treatment', 'mg/dl', 'mm'}
skip_predictor_list = {'inclusion criteria', 'exclusion criteria'}


# load active learning model
#model = word2vec.load('/groups/clinicaltrials/clinicaltrials/data/criteria.bin')
model = word2vec.load('data/criteria.bin')

# load similarity server
similarity_server = simserver.SessionServer('data/docsim_server')






# HELPER FUNCTIONS

# construct an address in HTML from city, state, zip, and country
def construct_address(city,state,zipcode,country,break_country=True):
    if city:
        if country == 'United States':
            return '%s, %s %s%s' % (city, state, zipcode, '<br>' + country if break_country else '')
        else:
            return '%s, %s' % (city, country)
    else:
        return 'No location information provided' 

# construct star rating from number
def gen_stars(s):
    ''' s is a number between 1 and 5 '''
    if s > 5:
        s = 5
    elif s < 1:
        s = 1

    rating_str = "<span class='rating'><i class='fa fa-star'></i>"
    ok = [1] * (int(s * 2) - 2)
    ok.extend([0] * (8 - len(ok)))
    for i in range(0,7,2):
        if sum(ok[i:i+2]) == 2:
            rating_str += "<i class='fa fa-star'></i>"
        elif sum(ok[i:i+2]) == 1:
            rating_str += "<i class='fa fa-star-half-o'></i>"
        else:
            rating_str += "<i class='fa fa-star-o'></i>"

    return rating_str + "</span>"

# calculate overall rating
def calc_overall(r_array):
    ''' r_array is a list or tuple of category ratings, in the order:
            date, mesh, sites, description, criteria
    '''
    r_wgt_avg = (r_array[0] * 0.10) + \
                (r_array[1] * 0.25) + \
                (r_array[2] * 0.25) + \
                (r_array[3] * 0.25) + \
                (r_array[4] * 0.15)
    return 1 + (round((r_wgt_avg) * 2 - 2) / 2.0)

# turn a query result with multiple rows per key into a lookup dictionary
def dictify(qresult,pos):
    ''' qresult is a list of n-tuples, pos is the position in the tuple to make the value (key is assumed to be 0) '''
    output = defaultdict(set)
    for r in qresult:
        output[r[0]].add(r[pos])
    return output

# create a comma-separated list of words
def add_commas(strlist, conj='and', sep=', '):
    ''' strlist is a list of strings to be concatenated with comma
        conj is the final conjunction, defaults to 'and'
    '''
    if 'Other' in strlist:
        strlist.remove('Other') 
        strlist.append('Other')
    if len(strlist) <= 1:
        return ''.join(strlist)
    elif len(strlist) == 2:
        return '%s %s %s' % (strlist[0], conj, strlist[1])
    else:
        return '%s%s%s %s' % (sep.join(strlist[:-1]), sep, conj, strlist[-1])

# create a layman's terms string that describes the trial
def layman_desc(phase, status, inv_dict, stype):
    missing_data = []

    if phase != 'N/A':
        lay_str = "This <span style='font-weight: bold'>%s</span> trial" % phase
    else:
        lay_str = "This trial"
        missing_data.append('phase')
    lay_str += " is <span style='font-weight: bold%s'>%s</span>." % ("; color: #228B22;" if status in ['recruiting',
                                                                                                       'not yet recruiting',
                                                                                                       'enrolling by invitation'] else "",
                                                                     status)

    inv_str = add_commas(inv_dict, 'and/or')
    if inv_str:
        if stype.lower() != 'n/a':
            stype = " <span style='font-weight: bold'>%s</span>" % stype
        else:
            stype = ''
            missing_data.append('study type')
        lay_str += " It is an%s assessment of a%s <span style='font-weight: bold'>%s</span> intervention." % (stype, 
                                                                                                            'n' if inv_str.lower()[0] in 'aeiou' else '',
                                                                                                            inv_str.lower())
    else:
        missing_data.append('intervention(s)')

    if missing_data:
        lay_str += " (No information was provided about the %s of the trial.)" % add_commas(missing_data, 'or')

    return lay_str

# procedure to bold search term
def bold_term(qtype, qid, name, term, num_trials):
    '''
        qtype is a string indicating the type of result, eg "inst" or "cond"
        qid is the object id for this result, usually an integer
        name is a string representing the full result text
        term is the search term
        num_trials is an integer indicating how many trials are associated with this result
    '''
    if qtype == 'cond':
        qpath = url_for('condition')
    elif qtype == 'inst':
        qpath = url_for('institution')
    background = 'rgba(255, 223, 51, 0.7)'
    term_pos = name.lower().find(term)
    term_end = term_pos + len(term)
    bold_name = '%s<span style="background-color: %s; font-weight: bold;">%s</span>%s'  % (name[:term_pos],
                                                                                           background,
                                                                                           name[term_pos:term_end],
                                                                                           name[term_end:])
    return '<p><a href="%s?%s=%s">%s</a> (%d trials)</p>' % (qpath, qtype, qid, bold_name, num_trials)

# procedure to return chunks of noun phrase terms
def chunker(sent):

    chunk_reg = r"""
                      CHUNK: {(<NN.*><POS>)?<RB>?<JJ.*>*<NN.*>+}
                 """
    results = []
    cp = RegexpParser(chunk_reg)

    tree = cp.parse(sent)
    for subtree in tree.subtrees():
        if subtree.label() == 'CHUNK':
            results.append(subtree[:])

    return results

#get chunks for predictors
def chunker_preds(sent):

    chunk_reg1 = r"""
                      CHUNK: {<NN.*><IN>}
                 """
    chunk_reg2 = r"""
                      CHUNK: {<VB.*><DT>}
                 """
    chunk_reg3 = r"""
                      CHUNK: {<NN.*><VB.*>}
                 """
    results = []

    for chunk_reg in [chunk_reg1, chunk_reg2, chunk_reg3]:
        cp = RegexpParser(chunk_reg)

        try:
            tree = cp.parse(sent)
        except Exception as e:
            print 'Chunker problem: %s' % e
            print sent
        
        for subtree in tree.subtrees():
            if subtree.label() == 'CHUNK':
                results.append(subtree[:])
    return results

# get random selection of tagged text to process
def get_random_text():

    if 'criteria_tracking' not in flask.session:
        flask.session['criteria_tracking'] = []

    criteria_tracking = flask.session['criteria_tracking']

    while True:
        rand_select = random.choice(range(250))
        if rand_select not in criteria_tracking:
            flask.session['criteria_tracking'].append(rand_select)
            break

    result = conn.execute(select([CriteriaTagged.c.tagged_text]).where(CriteriaTagged.c.random_select == rand_select))

    #convert into list of lists
    data = [eval(r.tagged_text)[0] for r in result]

    #mark punctuation with XX tag and convert inner list to tuples for processing
    data = [[(w[0], w[1]) if w[0] not in punctuation else (w[0], 'XX') for w in s] for s in data]

    return data

def get_past_predictors():
    '''pulls all the past predictors from other concepts into a list of lists'''
    result = conn.execute(select([ConceptPredictors.c.concept_id,
                                   ConceptPredictors.c.predictor])).fetchall()
    return result

# weight predictor terms for active learning algorithm
def weight_preds(past_predictors, pred_list):
    pred_weight_list = []

    #create a combined list of all preds, create Counter dict
    count_pred = Counter([p[1] for p in past_predictors])

    #add weights to pred terms and create new pred weight lists
    for idx in range(len(pred_list)):
        weight  = len(past_predictors) - (count_pred[pred_list[idx]]-1)
        pred_weight_list.append((pred_list[idx], weight))
        
    return pred_weight_list

# write list of terms to database
def write_list(termlist, termtype):
    if termlist:
        ins = conn.execute(CriteriaConceptStaging.insert(), [{'user_id': flask.session['userid'],
                                                              'update_time': datetime.now(),
                                                              'concept_id': flask.session['concept_id'],
                                                              'new_concept': flask.session['new_concept'],
                                                              'update_type': termtype,
                                                              'value': t}
                                                              for t in termlist])

# get list of strings based on typelist (eg 'term','term-reject', etc.)
def get_list(typelist):
    r = conn.execute(select([CriteriaConceptStaging.c.value]).\
                     where(and_(CriteriaConceptStaging.c.concept_id == flask.session['concept_id'],
                                CriteriaConceptStaging.c.update_type.in_(typelist)))).fetchall()
    outlist = [t[0] for t in r]
    for ttype in typelist:
        parts = ttype.split('-')
        thisvar = parts[0]
        thistab = 'Concept%ss%s' % (thisvar.title(), 'Reject' if len(parts) == 2 else '')
        r = conn.execute(select([eval('%s.c.%s' % (thistab, thisvar))]).\
                         where(eval('%s.c.concept_id' % thistab) == flask.session['concept_id'])).fetchall()
        outlist += [t[0] for t in r]
    return outlist

# get all staged data for a particular concept
def pull_staged_data(concept_id):
    current_data = conn.execute(select([CriteriaConceptStaging.c.update_time,
                                        CriteriaConceptStaging.c.update_type,
                                        CriteriaConceptStaging.c.value]).\
                                where(CriteriaConceptStaging.c.concept_id == concept_id)).\
                        fetchall()

    existing = defaultdict(dict)
    for update_time, update_type, value in current_data:
        existing[update_type][value] = update_time

    return existing








# homepage
@app.route('/')
def home():
    return flask.render_template('index.html',
                                 is_home=True)






# search results
@app.route('/search_results')
def search_results():

    params = request.args

    if 'q' in params:
        s_term = params['q'].lower()

        for i in range(5):
            try:
                cond = conn.execute(select([ConditionDescription.c.condition_id,
                                                ConditionDescription.c.mesh_term,
                                                func.count(ConditionLookup.c.nct_id).label('cnt')]).
                                            select_from(ConditionDescription.join(ConditionLookup,
                                                    and_(ConditionDescription.c.condition_id == ConditionLookup.c.condition_id,
                                                         ConditionLookup.c.source == 'CTGOV'))).\
                                            where(func.lower(ConditionDescription.c.mesh_term).contains(s_term)).\
                                            group_by(ConditionDescription.c.condition_id,
                                                ConditionDescription.c.mesh_term).\
                                            order_by(desc('cnt'))).\
                                        fetchall()
                inst = conn.execute(InstitutionDescription.\
                                            select().\
                                            where(func.lower(InstitutionDescription.c.name).contains(s_term)).\
                                            order_by(desc(InstitutionDescription.c.trial_count))).\
                                        fetchall()
                
                cond_list = [bold_term('cond', t[0], t[1], s_term, t[2]) for t in cond]
                inst_list = [bold_term('inst', t[0], t[1], s_term, t[8]) for t in inst if t[2] == 'GOLD']
                spon_list = [bold_term('inst', t[0], t[1], s_term, t[8]) for t in inst if t[2] == 'SPONSOR']
                fac_list = [bold_term('inst', t[0], t[1], s_term, t[8]) for t in inst if t[2] == 'FACILITY']

                return flask.render_template('search_results.html',
                                             search_term=params['q'],
                                             conditions=cond_list[:20],
                                             num_cond=len(cond_list),
                                             institutions=inst_list[:20],
                                             num_inst=len(inst_list),
                                             sponsors=spon_list[:20],
                                             num_spon=len(spon_list),
                                             facs=fac_list[:20],
                                             num_fac=len(fac_list))
            except Exception, e:
                print 'Database connection error getting search result info: %s' % e
                initializeDB(mysqlusername, mysqlpassword, mysqlserver, mysqldbname)

    return flask.redirect(url_for('home'))








# institution page
@app.route('/institution')
def institution():

    params = request.args

    if 'inst' in params:
        inst_id = int(params['inst'])
        for i in range(5):
            try:
                inst_data = conn.execute(InstitutionDescription.\
                                            select().\
                                            where(InstitutionDescription.c.institution_id == inst_id)).\
                                        fetchone()

                sponsors = conn.execute(InstitutionSponsors.\
                                            select().\
                                            where(InstitutionSponsors.c.institution_id == inst_id).\
                                            order_by(desc('trial_count'))).\
                                        fetchall()
                facilities = conn.execute(InstitutionFacilities.\
                                            select().\
                                            where(InstitutionFacilities.c.institution_id == inst_id).\
                                            order_by(desc('trial_count'))).\
                                        fetchall()

                inst_concept_desc = 'This institution is associated with %d trial sponsor%s and %d research facilit%s' % (len(sponsors),
                                                                                                                          '' if len(sponsors) == 1 else 's',
                                                                                                                          len(facilities),
                                                                                                                          'y' if len(facilities) == 1 else 'ies')

                rating_info = conn.execute(InstitutionRatings.select().where(InstitutionRatings.c.institution_id == inst_id)).fetchone()
                rating_obj = {'dates': gen_stars(float(rating_info[1])),
                              'mesh': gen_stars(float(rating_info[2])),
                              'sites': gen_stars(float(rating_info[3])),
                              'desc': gen_stars(float(rating_info[4])),
                              'crit': gen_stars(float(rating_info[5])),
                              'overall': gen_stars(calc_overall([float(f) for f in rating_info[1:6]]))}
                if inst_data:
                    return flask.render_template('institution.html',
                                                inst_id=inst_id,
                                                inst_name=inst_data[1],
                                                trial_cnt=inst_data[8],
                                                inst_loc=inst_data[3],
                                                inst_img=inst_data[4],
                                                inst_summary=inst_data[5],
                                                inst_concept_desc=inst_concept_desc,
                                                ratings=rating_obj
                                                )
            except Exception, e:
                print 'Database connection error getting institution info : %s' % str(e)
                initializeDB(mysqlusername, mysqlpassword, mysqlserver, mysqldbname)

    return flask.redirect(url_for('home'))

# top conditions JSON
@app.route('/_top_condition')
def top_condition():
    params = request.args
    if 'inst' in params:

        for i in range(5):
            try:
                cond_cnt = conn.execute(select([ConditionDescription.c.condition_id, 
                                            ConditionDescription.c.mesh_term, 
                                            func.count(InstitutionLookup.c.nct_id).label('cond_count')]).\
                                                select_from(InstitutionLookup.join(ConditionLookup,
                                                                                   and_(InstitutionLookup.c.institution_id == int(params['inst']),
                                                                                        InstitutionLookup.c.nct_id == ConditionLookup.c.nct_id,
                                                                                        ConditionLookup.c.syn_flag == 0,
                                                                                        or_(ConditionLookup.c.source == 'CTGOV',
                                                                                            ConditionLookup.c.source == 'ASSIGNED'))).\
                                                                              join(ConditionDescription)).\
                                                group_by(ConditionDescription.c.condition_id, ConditionDescription.c.mesh_term).\
                                                order_by(desc('cond_count')).\
                                                limit(20)).\
                                        fetchall()
                if cond_cnt:
                    return flask.jsonify(result=[{'cond_name': t[1],
                                                  'cond_id': t[0],
                                                  'trial_count': t[2]} for t in cond_cnt])
            except Exception, e:
                print 'Database connection error getting top conditions for institution info: %s' % e
                initializeDB(mysqlusername, mysqlpassword, mysqlserver, mysqldbname)

    return flask.jsonify(None)

# institution sponsors and facilities page
@app.route('/inst_sites')
def inst_sites():
    params = request.args
    if 'inst' in params:
        inst_id = int(params['inst'])
        for i in range(5):
            try:
                inst_data = conn.execute(InstitutionDescription.\
                                            select().\
                                            where(InstitutionDescription.c.institution_id == inst_id)).\
                                        fetchone()

                sponsors = conn.execute(InstitutionSponsors.\
                                            select().\
                                            where(InstitutionSponsors.c.institution_id == inst_id).\
                                            order_by(desc('trial_count'))).\
                                        fetchall()
                facilities = conn.execute(InstitutionFacilities.\
                                            select().\
                                            where(InstitutionFacilities.c.institution_id == inst_id).\
                                            order_by(desc('trial_count'))).\
                                        fetchall()

                sponsor_list = [{'name': t[1], 'cnt': t[2]} for t in sponsors]
                facility_list = [{'name': t[1],
                                  'cnt': t[6],
                                  'address': construct_address(t[2],t[3],t[4],t[5])}
                                  for t in facilities]

                if inst_data:
                    return flask.render_template('inst_sites.html',
                                                inst_id=inst_id,
                                                inst_name=inst_data[1],
                                                sponsor_list=sponsor_list,
                                                facility_list=facility_list
                                                )
            except Exception, e:
                print 'Database connection error getting institution info : %s' % str(e)
                initializeDB(mysqlusername, mysqlpassword, mysqlserver, mysqldbname)

    return flask.redirect(url_for('home'))







# condition page
@app.route('/condition')
def condition():
    params = request.args
    if 'cond' in params:
        cond_id = int(params['cond'])
        for i in range(5):
            try:

                cond_data = conn.execute(ConditionDescription.\
                                            select().\
                                            where(ConditionDescription.c.condition_id == cond_id)).\
                                        fetchone()

                cond_syn = conn.execute(select([ConditionDescription.c.mesh_term]).\
                                            select_from(ConditionSynonym.join(ConditionDescription,
                                                and_(ConditionDescription.c.condition_id == ConditionSynonym.c.synonym_id,
                                                     ConditionSynonym.c.condition_id == cond_id)))).\
                                        fetchall()

                top_inst = conn.execute(select([InstitutionDescription.c.institution_id,
                                                InstitutionDescription.c.name,
                                                InstitutionDescription.c.image_url,
                                                InstitutionDescription.c.location,
                                                func.count(ConditionLookup.c.nct_id).label('cnt')]).\
                                            select_from(InstitutionDescription.join(InstitutionLookup.join(ConditionLookup,
                                                    and_(ConditionLookup.c.condition_id == cond_id,
                                                         ConditionLookup.c.source == 'CTGOV',
                                                         ConditionLookup.c.nct_id == InstitutionLookup.c.nct_id)),
                                                    InstitutionLookup.c.institution_id == InstitutionDescription.c.institution_id)).\
                                            group_by(InstitutionDescription.c.institution_id,
                                                     InstitutionDescription.c.name,
                                                     InstitutionDescription.c.image_url,
                                                     InstitutionDescription.c.location).\
                                            order_by(desc('cnt')).\
                                            limit(5)).\
                                        fetchall()

                summary_text = cond_data[2].replace('<a ','<a target="blank" ') if cond_data[2] else ''

                inst_obj = [{'inst_id': t[0],
                             'inst_name': t[1],
                             'inst_img': t[2],
                             'inst_loc': t[3],
                             'inst_cnt': t[4]}
                             for t in top_inst]
                if cond_data:
                    return flask.render_template('condition.html', 
                                                cond_id=cond_id,
                                                cond_name=cond_data[1],
                                                cond_summary=summary_text or 'This condition has no description available.',
                                                cond_synonyms=[t[0] for t in cond_syn],
                                                institution_list=inst_obj
                                                )
            except Exception, e:
                print 'Database connection error getting condition info: %s' % e
    
    return flask.redirect(url_for('home'))








# trial summary page
@app.route('/trial')
def trial():
    params = request.args
    if 'nct_id' in params:
        nct_id = params['nct_id']
        for i in range(5):
            try:

                summary_data = conn.execute(select([ClinicalStudy.c.brief_title,
                                                    ClinicalStudy.c.brief_summary,
                                                    ClinicalStudy.c.detailed_description,
                                                    ClinicalStudy.c.overall_status,
                                                    ClinicalStudy.c.phase,
                                                    ClinicalStudy.c.study_type,
                                                    ClinicalStudy.c.gender,
                                                    ClinicalStudy.c.minimum_age,
                                                    ClinicalStudy.c.maximum_age,
                                                    ClinicalStudy.c.healthy_volunteers,
                                                    ClinicalStudy.c.lastchanged_date]).
                                            select_from(ClinicalStudy).\
                                            where(ClinicalStudy.c.nct_id == nct_id)).\
                                        fetchone()

                brief_desc = summary_data[1].replace('<br />','</p><p>') or 'No brief summary was provided.'
                detailed_desc = summary_data[2].replace('<br />','</p><p>') or 'No detailed description was provided.'

                inv = conn.execute(select([Interventions.c.nct_id, Interventions.c.intervention_type]).\
                                        select_from(Interventions).\
                                        where(Interventions.c.nct_id == nct_id)).\
                                    fetchall()

                inv_dict = dictify(inv,1)

                cond = conn.execute(select([ConditionDescription.c.condition_id,
                                            ConditionDescription.c.mesh_term]).\
                                            select_from(ConditionDescription.join(ConditionLookup,
                                                and_(ConditionLookup.c.nct_id == nct_id,
                                                    ConditionLookup.c.source == 'CTGOV',
                                                    ConditionLookup.c.syn_flag == 0,
                                                    ConditionLookup.c.condition_id == ConditionDescription.c.condition_id)))).\
                                    fetchall()

                ctext = conn.execute(select([CriteriaText.c.criteria_text,
                                             CriteriaText.c.display_type]).\
                                        select_from(CriteriaText).\
                                        where(CriteriaText.c.nct_id == nct_id).\
                                        order_by(CriteriaText.c.display_order)).\
                                    fetchall()
                criteria = [{'disptext': t[0],
                             'disptype': t[1]}
                             for t in ctext]

                cond_suggest = conn.execute(select([ConditionDescription.c.condition_id,
                                                    ConditionDescription.c.mesh_term]).\
                                            select_from(ConditionDescription.join(ConditionLookup,
                                                and_(ConditionLookup.c.nct_id == nct_id,
                                                    ConditionLookup.c.source.in_(['KNN','MAXENT','MTI']),
                                                    ConditionLookup.c.syn_flag == 0,
                                                    ConditionLookup.c.condition_id == ConditionDescription.c.condition_id)))).\
                                    fetchall()

                rating_info = conn.execute(TrialRatings.select().where(TrialRatings.c.nct_id == nct_id)).fetchone()
                rating_obj = {'dates': gen_stars(float(rating_info[1])),
                              'mesh': gen_stars(float(rating_info[2])),
                              'sites': gen_stars(float(rating_info[3])),
                              'desc': gen_stars(float(rating_info[4])),
                              'crit': gen_stars(float(rating_info[5])),
                              'overall': gen_stars(calc_overall([float(f) for f in rating_info[1:6]]))}

                sponsors = conn.execute(Sponsors.select().where(Sponsors.c.nct_id == nct_id)).fetchall()
                prim_spon = [t[3] for t in sponsors if t[2] == 'Lead Sponsor'][0]
                other_collab = [t[3] for t in sponsors if t[2] == 'Collaborator']
                collab_dict = {'cnt': len(other_collab),
                               'list_string': add_commas(other_collab, sep='; ')}

                facilities = conn.execute(Facilities.select().where(Facilities.c.nct_id == nct_id)).fetchall()
                valid_fac = [{'name': t[3] or '[No facility name provided]',
                              'address': construct_address(t[4],t[5],t[6],t[7])}
                             for t in facilities]

                pubs = conn.execute(TrialPublications.select().\
                                    where(TrialPublications.c.nct_id == nct_id).\
                                    order_by(TrialPublications.c.authors)).\
                            fetchall()
                pub_dict = {'linked': [{'pmid': t[1],
                                        'authors': t[2],
                                        'title': t[3],
                                        'cite': t[4]} for t in pubs if t[5] == 1],
                            'other_likely': [{'pmid': t[1],
                                       'authors': t[2],
                                       'title': t[3],
                                       'cite': t[4]} for t in pubs if t[5] == 0.9],
                            'other_probably': [{'pmid': t[1],
                                       'authors': t[2],
                                       'title': t[3],
                                       'cite': t[4]} for t in pubs if t[5] == 0.6],
                            'other_possibly': [{'pmid': t[1],
                                       'authors': t[2],
                                       'title': t[3],
                                       'cite': t[4]} for t in pubs if t[5] == 0.3],
                            }

                if summary_data:
                    return flask.render_template('trial.html', 
                                                nct_id=nct_id,
                                                trial_title=summary_data[0],
                                                lay_str=layman_desc(summary_data[4],
                                                                    summary_data[3].lower(),
                                                                    list(inv_dict[nct_id]) if nct_id in inv_dict else '',
                                                                    summary_data[5].lower()),
                                                cond_list=[{'id': c[0],
                                                            'name': c[1]}
                                                            for c in cond],
                                                cond_list_s=[{'id': c[0],
                                                              'name': c[1]}
                                                              for c in set(tuple(t) for t in cond_suggest)],
                                                brief_desc=brief_desc,
                                                detailed_desc=detailed_desc,
                                                criteria=criteria,
                                                ratings=rating_obj,
                                                prim_spon=prim_spon,
                                                other_collab=collab_dict,
                                                facility_list=valid_fac,
                                                pubs=pub_dict
                                                )
            except Exception, e:
                print 'Database connection error getting trial summary info: %s' % e

    return flask.redirect(url_for('home'))

@app.route('/trial_sites')
def trial_sites():
    params = request.args
    if 'nct_id' in params:
        nct_id = params['nct_id']
        for i in range(5):
            try:

                summary_data = conn.execute(select([ClinicalStudy.c.brief_title]).
                                            select_from(ClinicalStudy).\
                                            where(ClinicalStudy.c.nct_id == nct_id)).\
                                        fetchone()

                facilities = conn.execute(Facilities.select().where(Facilities.c.nct_id == nct_id)).fetchall()
                valid_fac = [{'name': t[3] or '[No facility name provided]',
                              'address': construct_address(t[4],t[5],t[6],t[7])}
                             for t in facilities]

                if summary_data:
                    return flask.render_template('trial_sites.html', 
                                                nct_id=nct_id,
                                                trial_title=summary_data[0],
                                                facility_list=valid_fac
                                                )
            except Exception, e:
                print 'Database connection error getting trial site list info: %s' % e
    

    return flask.redirect(url_for('home'))









# trials JSON
@app.route('/_trial_list')
def trial_list():
    params = request.args

    main_table = TrialSummary
    wheres = []
    filter_cond_list = []

    # fill in condition list if part of user's query
    if 'condition_filter' in params and json.loads(params['condition_filter']):
        filter_cond_list = json.loads(params['condition_filter'])

    if 'page' in params:
        # for institution pages, filter trials by institution_id
        if params['page'] == 'inst':
            tbl = InstitutionLookup
            tbl_key = InstitutionLookup.c.institution_id
            main_table = main_table.join(tbl, 
                                and_(tbl.c.nct_id == TrialSummary.c.nct_id,
                                     tbl_key == int(params['id'])))

        # for condition pages, filter trials by condition_id
        elif params['page'] == 'cond':
            tbl = ConditionLookup
            tbl_key = ConditionLookup.c.condition_id
            filter_cond_list.append(params['id'])

    # add in condition table if there are condition filters
    if len(filter_cond_list) > 0:
        cond_table = select([ConditionLookup.c.nct_id]).\
                        where(and_(ConditionLookup.c.source == 'CTGOV',
                                   ConditionLookup.c.condition_id.in_(int(d) for d in filter_cond_list))).\
                        distinct().alias()
        main_table = main_table.join(cond_table, cond_table.c.nct_id == TrialSummary.c.nct_id)

    # get limit count
    if 'limit' in params:
        this_limit = int(params['limit'])
    else:
        this_limit = 10000000

    # add other where clauses based on user query
    if 'age' in params and params['age']:
        wheres.append(text('trial_summary.minimum_age <= %s' % params['age']))
        wheres.append(text('trial_summary.maximum_age >= %s' % params['age']))

    if 'gender' in params and params['gender'] != 'false':
        if params['gender'] == 'female':
            wheres.append(text("trial_summary.gender != 'Male'"))
        elif params['gender'] == 'male':
            wheres.append(text("trial_summary.gender != 'Female'"))

    if 'healthy' in params and params['healthy'] != 'false':
        wheres.append(text("trial_summary.healthy_volunteers = 'Accepts Healthy Volunteers'"))

    okzip = True
    if 'zip_dist' in params and params['zip_dist'] in ['5 miles ','25 miles ','100 miles ']:
        if 'zip_val' in params and len(params['zip_val']) == 5:
            zip_loc = conn.execute(select([ZipLatlong.c.latitude, ZipLatlong.c.longitude]).\
                                   where(ZipLatlong.c.zip == params['zip_val'])).\
                           fetchone()
            if len(zip_loc) > 0:
                zip_lat, zip_lng = zip_loc
                zip_miles = params['zip_dist'].split()[0]
                zip_table = select([ZipFacilities.c.nct_id]).\
                                where(text("(3959*acos(cos(radians(%g))*cos(radians(zip_facilities.latitude))*" % zip_lat + \
                                           "cos(radians(zip_facilities.longitude)-radians(%g))+sin(radians(%g))*" % (zip_lng, zip_lat)+ \
                                           "sin(radians(zip_facilities.latitude))))<%s" % zip_miles)).\
                                distinct().alias()
                main_table = main_table.join(zip_table, zip_table.c.nct_id == TrialSummary.c.nct_id) 

            else:
                okzip = False
        else:
            okzip = False

    if 'status' in params and json.loads(params['status']):
        if 'All (default)' not in json.loads(params['status']):
            wheres.append(text("trial_summary.overall_status in ('%s')" % "','".join(json.loads(params['status']))))

    if 'has_res' in params and params['has_res'] != 'false':
        wheres.append(text("trial_summary.has_results = 'Y'"))

    if 'interventions' in params and json.loads(params['interventions']):
        if 'All (default)' not in json.loads(params['interventions']):
            wheres.append(text("(%s)" % ' or '.join("trial_summary.interventions like '%%%s%%'" % i for i in json.loads(params['interventions']))))

    if 'criteria_filters' in params and json.loads(params['criteria_filters']):
        critf = json.loads(params['criteria_filters'])
        crit_table = select([CriteriaConceptLookup.c.nct_id]).\
                     group_by(CriteriaConceptLookup.c.nct_id).\
                     having(or_(text("sum(case when concept_id = '%s' and inverse = %d then 1 else 0 end) > 0" % (k, 1 if v == 'Y' else 0))
                            for k, v in critf.items())).alias('crit_table')
        main_table = main_table.outerjoin(crit_table, TrialSummary.c.nct_id == crit_table.c.nct_id)
        wheres.append(text("crit_table.nct_id is null"))

    # get trials
    trials = conn.execute(select([TrialSummary]).\
                            select_from(main_table).\
                            where(and_(cl for cl in wheres)).\
                            order_by(desc(TrialSummary.c.sort_date), TrialSummary.c.nct_id)).\
                        fetchall()

    nct_ids = [t[0] for t in trials][:this_limit]

    # if any trials match query, get condition, institutions, and facilities for those trials
    if len(nct_ids) > 0:
        inv = conn.execute(select([Interventions.c.nct_id, 
                                   Interventions.c.intervention_type,
                                   Interventions.c.intervention_name]).\
                                where(Interventions.c.nct_id.in_(nct_ids))).\
                            fetchall()

        inv_dict = dictify(inv,1)
        inv_list = dictify(inv,2)

        conds = conn.execute(select([ConditionLookup.c.nct_id,
                                     ConditionDescription.c.mesh_term]).
                                select_from(ConditionLookup.join(ConditionDescription,
                                    and_(ConditionLookup.c.nct_id.in_(nct_ids),
                                         ConditionLookup.c.source == 'CTGOV',
                                         ConditionLookup.c.syn_flag == 0,
                                         ConditionLookup.c.condition_id == ConditionDescription.c.condition_id)))).\
                            fetchall()

        cond_list = dictify(conds,1)

        facilities = conn.execute(Facilities.select().where(Facilities.c.nct_id.in_(nct_ids))).fetchall()
        facs_list = {}
        for t in facilities:
            if t[1] not in facs_list:
                fac_entry = '%s, %s' % (t[3] or '[No facility name provided]',
                                          construct_address(t[4],t[5],t[6],t[7],break_country=False))
                facs_list[t[1]] = {'lead': fac_entry, 'cnt': 0}
            else:
                facs_list[t[1]]['cnt'] += 1

    # compile JSON object
    out_obj = []
    for nct_id, title, status, phase, stype, gender, min_age, max_age, hv, has_res, sort_date, intrv in trials[:this_limit]:
        if nct_id in facs_list:
            fac_name = '%s%s' % (facs_list[nct_id]['lead'], ', and %d other facilities' % facs_list[nct_id]['cnt'] if facs_list[nct_id]['cnt'] > 0 else '')
        else:
            fac_name = 'No trial sites listed'
        out_obj.append({'nct_id': nct_id,
                        'trial_title': title,
                        'lay_str': layman_desc(phase, status, list(inv_dict[nct_id]) if nct_id in inv_dict else '', stype),
                        'interventions': add_commas(list(inv_list[nct_id]),sep='; ') or 'None listed',
                        'conditions': add_commas(list(cond_list[nct_id]),sep='; ') or 'None listed',
                        'facility': fac_name
                        })

    return flask.jsonify(result=out_obj,
                         total_results=len(trials),
                         num_results=len(nct_ids),
                         okzip=okzip)


@app.route('/_patient_filters')
def patient_filters():
    concepts = conn.execute(select([CriteriaConcept])).fetchall()
    con_list = [{'concept_id': t[0],
                 'concept_name': t[1]}
                for t in concepts]
    return flask.jsonify(concepts=con_list)

@app.route('/_get_condition_name')
def get_condition_name():
    cond_id = request.args['cond_id']
    cname = conn.execute(select([ConditionDescription.c.mesh_term]).where(ConditionDescription.c.condition_id == int(cond_id))).fetchone()[0]
    return flask.jsonify(condition_name=cname)








@app.route('/structure_trial_criteria')
def structure_trial_criteria():
    params = request.args
    if 'nct_id' in params:
        nct_id = params['nct_id']
        for i in range(5):
            try:
                ctext = conn.execute(select([CriteriaText.c.criteria_text_id,
                                             CriteriaText.c.display_order,
                                             CriteriaText.c.criteria_text,
                                             CriteriaTagged.c.tagged_text,
                                             CriteriaText.c.display_type,
                                             ConceptTerms.c.term,
                                             CriteriaConceptLookup.c.inverse,
                                             CriteriaConcept.c.concept_id,
                                             CriteriaConcept.c.concept_name]).\
                                        select_from(CriteriaText.join(CriteriaTagged,
                                            and_(CriteriaText.c.nct_id == nct_id,
                                                CriteriaText.c.criteria_text_id == CriteriaTagged.c.criteria_text_id)).\
                                            outerjoin(CriteriaConceptLookup,
                                                CriteriaText.c.criteria_text_id == CriteriaConceptLookup.c.criteria_text_id).\
                                            outerjoin(ConceptTerms,
                                                CriteriaConceptLookup.c.term_id == ConceptTerms.c.term_id).\
                                            outerjoin(CriteriaConcept,
                                                CriteriaConceptLookup.c.concept_id == CriteriaConcept.c.concept_id)).\
                                        order_by(CriteriaText.c.display_order)).\
                                    fetchall()

                trial_title = conn.execute(select([TrialSummary.c.brief_title]).where(TrialSummary.c.nct_id == nct_id)).fetchone()[0]

                under_review = conn.execute(select([CriteriaConceptStaging.c.value]).\
                                                where(CriteriaConceptStaging.c.update_type == 'concept-name')).fetchall()
                cur_concepts = [t[0].lower() for t in under_review]

                criteria_dict = {}
                for cid, corder, ct, tt, dtype, cterm, cinv, conid, conname in ctext:
                    if corder not in criteria_dict:
                        chunks = []
                        last_pos = 0

                        for s in eval(tt):
                            new_s = [(w[0],w[1]) for w in s]
                            s_tags = chunker(new_s)

                            for c in s_tags:
                                this_str = c[0][0] 
                                if len(c) > 1:
                                    this_str += ''.join('%s%s' % (' ' if c[i][1] != 'POS' and not (c[i-1][1] == 'JJR' and len(c[i-1][0]) == 1) else '',
                                                                  c[i][0]) for i in range(1,len(c)))
                                if len(this_str) > 1 and this_str.lower() not in skip_term_list:
                                    this_pos = ct.find(this_str, last_pos)
                                    if this_pos == -1:
                                        print ct
                                        print this_str
                                        print
                                    chunks.append((this_str, this_pos))
                                    last_pos += len(this_str)
                        criteria_dict[corder] = {'id': cid,
                                                 'disptype': dtype,
                                                 'ctext': ct,
                                                 'chunks': chunks,
                                                 'terms': defaultdict(dict)}
                    if conname:
                        criteria_dict[corder]['terms'][cterm.lower()][conname] = conid

                write_obj = []
                for c in sorted(criteria_dict.keys()):
                    ct = criteria_dict[c]['ctext']
                    poss_chunks = []
                    if criteria_dict[c]['disptype'] == 'H':
                        out_text = '<h4>%s</h4>' % ct
                    elif criteria_dict[c]['chunks']:
                        chunks = criteria_dict[c]['chunks']
                        out_text = '<p class="criteria-text">%s' % ct[:chunks[0][1]]
                        for i, chunk in enumerate(chunks):

                            phrase, start = chunk

                            concept_class = 'criteria-highlight'
                            concept_list = [{'id': criteria_dict[c]['terms'][phrase.lower()][m],
                                             'name': phrase.lower()}
                                             for m in sorted(criteria_dict[c]['terms'][phrase.lower()].keys())
                                             if phrase.lower() in criteria_dict[c]['terms']]
                            concept_list += [{'id': '', 'name': 'Start a new concept'}]

                            if i == len(chunks) - 1:
                                end = len(ct)
                            else:
                                end = chunks[i+1][1]

                            out_text += '<mark>%s</mark>%s' % (phrase, ct[start+len(phrase):end])

                            in_db = []
                            where_from = True
                            chunk_links = []
                            if phrase.lower() in cur_concepts:
                                chunk_links.append('<span class="disabled-text">Concept is under review</span>')
                                where_from = False
                            else:
                                for concept in concept_list:
                                    if concept['id']:
                                        in_db.append(concept['name'])
                                        if concept['name'] == phrase.lower():
                                            link_text = 'Continue developing <b>%s</b>' % concept['name']
                                        else:
                                            link_text = None
                                    else:
                                        link_text = concept['name']
                                    if link_text:
                                        chunk_link = '<a href="%s?term=%s&cid=%s&id=%d" target="_blank">%s</a>' % (url_for('active_learning'),
                                                                                                                   phrase.lower(),
                                                                                                                   concept['id'],
                                                                                                                   criteria_dict[c]['id'],
                                                                                                                   link_text)
                                        chunk_links.append('<p>%s</p>' % chunk_link)

                            if in_db:
                                in_db_text = "Part of %s" % add_commas(in_db)
                            elif where_from:
                                in_db_text = "Not part of any concept"
                            else:
                                in_db_text = ""

                            poss_chunks.append({'term': '<p>%s</p>' % phrase, 'in_db': in_db_text, 'links': chunk_links})

                        out_text += '</p>'
                    else:
                        out_text = '<p class="criteria-text">%s</p>' % ct
                    write_obj.append({'text': out_text, 'chunks': poss_chunks})

                if nct_id:
                    return flask.render_template('structure_trial_criteria.html', 
                                                nct_id=nct_id,
                                                trial_title=trial_title,
                                                crit_list=write_obj
                                                )
            except Exception, e:
                print 'Database connection error getting structure trial criteria info: %s' % e

    return flask.redirect(url_for('home'))

# run active learning for a term
@app.route('/active_learning')
def active_learning():
    params = request.args
    initial_term = params['term']

    under_review = conn.execute(select([CriteriaConceptStaging.c.concept_id]).\
                                where(and_(CriteriaConceptStaging.c.update_type == 'concept-name',
                                           CriteriaConceptStaging.c.value == initial_term.lower()))).fetchall()

    return flask.render_template('active_learning.html',
                                 initial_term=initial_term,
                                 under_review=len(under_review) > 0)

@app.route('/_learning_startup')
def learning_startup():
    params = request.args

    concept_id = params['concept_id']
    initial_term = params['initial_term']
    criteria_text_id = params['criteria_text_id']

    ctypes = ['term','term-reject','predictor','predictor-reject']
    if concept_id:
        new_concept = 0
        flask.session['concept_id'] = concept_id
        for c in ctypes:
            exec('%s = get_list(["%s"])' % (c.replace('-','_'),c))
    else:
        new_concept = 1
        concept_id = str(uuid.uuid4())
        flask.session['concept_id'] = concept_id
        for c in ctypes:
            exec('%s = []' % c.replace('-','_'))

    #add skip terms to term_exc and pred_exc
    #term_exc += list(skip_term_list)
    #pred_exc += list(skip_predictor_list)

    # getting existing predictors
    #all_preds = list(get_past_predictors())

    # setting session variables
    flask.session['new_concept'] = new_concept
    #flask.session['concept_id'] = concept_id
    #flask.session['all_preds'] = all_preds

    # write concept info to the database
    ins = conn.execute(CriteriaConceptStaging.insert(), [{'user_id': flask.session['userid'],
                                                          'update_time': datetime.now(),
                                                          'concept_id': flask.session['concept_id'],
                                                          'new_concept': flask.session['new_concept'],
                                                          'update_type': 'concept-name',
                                                          'value':initial_term}])
    if new_concept == 1:
        write_list([initial_term.lower()], 'term')

    return flask.jsonify(new_concept=new_concept,
                         term=term,
                         term_exc=term_reject,
                         predictor=predictor,
                         predictor_exc=predictor_reject,
                         )

@app.route('/_learning_terms_w2v')
def learning_terms_w2v():

    num_terms = int(request.args['num'])
    word = request.args['initial_term']
    word = '_'.join(word.lower().split(' '))

    exc_list = get_list(['term','term-reject'])

    try:
        indexes, metrics = model.cosine(word, n=num_terms)
        return flask.jsonify(vals='terms',
                             new_vals=[{'name': ' '.join(w.split('_')), 'score': round(p*100)}
                                       for w, p in model.generate_response(indexes, metrics).tolist()
                                       if w not in exc_list
                                       and w not in skip_term_list])
    except Exception as e:
        print 'word2vec problem with %s: %s' % (word,e)
        return flask.jsonify(vals='terms',
                             new_vals=[word])

@app.route('/_learning_terms_basic')
def learning_terms_basic():

    text = get_random_text()

    pred_list = get_list(['predictor'])
    all_preds = get_past_predictors()

    pred_weight_list = weight_preds(all_preds, pred_list)

    term_options_dict = Counter()
    for sent in text:
        #skip sentence if it contains less than one word
        if len(sent) <= 1:
                continue
        #crate a sentence rank for judging weight of terms found
        sent_rank = 1
        for pred in pred_weight_list:
            if pred[0].lower() in ' '.join(zip(*sent)[0]).lower():
                sent_rank += pred[1]
        result = chunker(sent)
        terms = [' '.join(x) for x in [[x[0] for x in term] for term in result]]
        terms.append(' '.join([sent[0][0], sent[1][0]]))
        #lower case all terms
        terms = [x.lower() for x in terms]
        #add weights to terms by multiplying by sent_rank
        terms = terms * sent_rank
        term_options_dict.update(terms)

    #get top 20 predictors that have not been seen before
    exc_list = get_list(['term','term-reject'])
    exc_list += list(skip_term_list)
    sorted_terms = sorted(term_options_dict.items(), key=lambda x: x[1], reverse=True)
    counter = 0
    top_terms = []
    for term in sorted_terms:
        if term[0] not in exc_list and len(term[0]) > 1:
            top_terms.append(term)
            counter += 1
            if counter == 20 or counter == len(sorted_terms):
                break

    return flask.jsonify(vals='terms',
                         new_vals=[{'name': t[0], 'score': round(t[1])}
                                    for t in top_terms])

@app.route('/_learning_preds')
def learning_preds():

    text = get_random_text()

    term_list = get_list(['term'])
    pred_options_dict = Counter()
    for sent in text:
        #if the sentance has less than 2 words skip it
        if len(sent) <= 1:
            continue
        #create a sentence rank for judging weight of terms found
        sent_rank = 0
        for term in term_list:
            if term.lower() in ' '.join(zip(*sent)[0]).lower():
                sent_rank += 1
        result = chunker_preds(sent)
        preds = [' '.join(x) for x in [[x[0] for x in term] for term in result]]
        preds.append(' '.join([sent[0][0], sent[1][0]]))
        #lower case all preds
        preds = [x.lower() for x in preds]
        preds = preds * sent_rank
        pred_options_dict.update(preds)

    #get top 20 predictors that have not been seen before
    exc_list = get_list(['predictor','predictor-reject'])
    exc_list += list(skip_predictor_list)
    sorted_preds = sorted(pred_options_dict.items(), key=lambda x: x[1], reverse=True)
    counter = 0
    top_preds = []
    for pred in sorted_preds:
        if pred[0] not in exc_list and len(pred[0]) > 1:
            top_preds.append(pred)
            counter += 1
            if counter == 20 or counter == len(sorted_preds):
                break

    return flask.jsonify(vals='predictors',
                         new_vals=[{'name': p[0], 'score': round(p[1])}
                                    for p in top_preds])

@app.route('/_write_data')
def write_data():
    params = request.args
    new_accepts = json.loads(params['acc'])
    new_rejects = json.loads(params['rej'])
    wordtype = params['wt']

    if wordtype == 'term':
        write_list(new_accepts,'term')
        write_list(new_rejects,'term-reject')
    else:
        write_list(new_accepts,'predictor')
        write_list(new_rejects,'predictor-reject')

    return flask.jsonify(done=True)

@app.route('/_concept_terms')
def concept_terms():
    params = request.args
    all_terms = json.loads(params['acc']) + get_list(['term'])
    return flask.jsonify(all_terms=all_terms)


@app.route('/_rename_concept')
def rename_concept():
    params = request.args
    new_name = params['new_name']

    try:
        r = conn.execute(CriteriaConceptStaging.update().\
                            where(and_(CriteriaConceptStaging.c.concept_id == flask.session['concept_id'],
                                       CriteriaConceptStaging.c.update_type == 'concept-name')).\
                            values(value=new_name))
        return flask.jsonify(done=True)
    except:
        return flask.jsonify(done=False)















# tools page
@app.route('/tools')
def tools():
    return flask.render_template('tools.html')

# MeSH suggestion page
@app.route('/mesh_suggest')
def mesh_suggest():
    return flask.render_template('mesh_suggest.html')

@app.route('/_get_suggestions')
def get_suggestions():
    sim_docs = {sim_id: dist
                 for sim_id, dist, _ in 
                    similarity_server.find_similar({'tokens': utils.simple_preprocess(request.args['doc'])}, min_score=0.4, max_results=10)}
    doc_terms = conn.execute(select([ConditionBrowse.c.nct_id, ConditionBrowse.c.mesh_term]).\
                                where(ConditionBrowse.c.nct_id.in_(sim_docs.keys()))).fetchall()
    if doc_terms:
        ranking = defaultdict(float)
        for nct_id, term in doc_terms:
            ranking[term] += sim_docs[nct_id]
        ordered_terms = [t[0] for t in sorted(ranking.items(), key=lambda x: x[1], reverse=True)]
        return flask.jsonify(results=ordered_terms)
    else:
        return flask.jsonify(results=False)

# inserting suggested MeSH terms
@app.route('/_mesh_stage')
def stage_mesh():
    params = request.args
    nct_id = params['nct_id']
    conds = json.loads(params['cond_ids'])

    try:
        r = conn.execute(MeshAssignStaging.insert(), [{'user_id': flask.session['userid'],
                                                       'nct_id': nct_id,
                                                       'update_time': datetime.now(),
                                                       'condition_id': cid}
                                                       for cid in conds
                                                       if len(str(cid)) > 0])
        return flask.jsonify(done=True)
    except:
        return flask.jsonify(done=False)






# get counts for admin modal
@app.route('/_get_admin_counts')
def get_admin_counts():
    num_concepts = len(conn.execute(CriteriaConceptStaging.select().where(CriteriaConceptStaging.c.update_type == 'concept-name')).fetchall())
    num_mesh = len(conn.execute(MeshAssignStaging.select()).fetchall())
    return flask.jsonify(num_concepts=num_concepts,
                         num_mesh=num_mesh)







# admin concept approval page
@app.route('/approve_concepts')
def approve_concepts():
    return flask.render_template('approve_concepts.html')

@app.route('/_approve_concepts_load')
def approve_concepts_load():
    concept_data = conn.execute(select([CriteriaConceptStaging.c.concept_id, 
                                        CriteriaConceptStaging.c.user_id,
                                        CriteriaConceptStaging.c.new_concept,
                                        CriteriaConceptStaging.c.value]).\
                                where(CriteriaConceptStaging.c.update_type == 'concept-name')).\
                            fetchall()

    concept_terms = conn.execute(select([CriteriaConceptStaging.c.concept_id,
                                         CriteriaConceptStaging.c.update_type,
                                         CriteriaConceptStaging.c.value]).\
                                 where(CriteriaConceptStaging.c.update_type.in_(['term','term-reject']))).\
                            fetchall()

    uniq_user = list(set(t[1] for t in concept_data))
    if len(uniq_user) > 0:
        uinfo = conn.execute(select([Users.c.user_id, 
                                     Users.c.full_name,
                                     Users.c.institution]).where(Users.c.user_id.in_(uniq_user))).fetchall()

        user_info = {t[0]: {'name': t[1], 'institution': t[2]} for t in uinfo}

    concepts = {}
    for cid, user_id, newconc, cname in concept_data:
        if newconc == 0:
            old_terms     = [r[0] for r in conn.execute(select([ConceptTerms.c.term]).where(ConceptTerms.c.concept_id == cid))]
            old_terms_rej = [r[0] for r in conn.execute(select([ConceptTermsReject.c.term]).where(ConceptTermsReject.c.concept_id == cid))]
        else:
            old_terms = []
            old_terms_rej = []

        new_terms = [t[2] for t in concept_terms if t[0] == cid and t[1] == 'term' and t[2] != cname]
        new_terms_rej = [t[2] for t in concept_terms if t[0] == cid and t[1] == 'term-reject']

        concepts[cid] = {'name': cname,
                         'new_concept': newconc,
                         'userid': user_id,
                         'username': user_info[user_id]['name'],
                         'userinst': user_info[user_id]['institution'],
                         'new_terms': new_terms,
                         'new_terms_rej': new_terms_rej,
                         'old_terms': old_terms,
                         'old_terms_rej': old_terms_rej}

    return flask.jsonify(concepts=concepts)

@app.route('/_write_criteria_approval')
def write_criteria_approval():
    params = request.args
    concept_id = params['concept_id']
    new_concept = params['new_concept']
    user_id = params['userid']
    ok_terms = json.loads(params['ok_terms'])

    existing = pull_staged_data(concept_id)

    concept_name = existing['concept-name'].keys()[0]
    ok_terms.append(concept_name)

    # write data to main criteria concept tables
    try:
        if new_concept:
            r = conn.execute(CriteriaConcept.insert(), [{'concept_id': concept_id,
                                                         'concept_name': concept_name
                                                        }])
        else:
            r = conn.update(CriteriaConcept.update().\
                                            where(CriteriaConcept.c.concept_id == concept_id).\
                                            values(concept_name=concept_name))
    except Exception, e:
        print 'Problem inserting or updating concept name: %s' % e

    try:
        r = conn.execute(ConceptTerms.insert(), [{'concept_id': concept_id,
                                                  'term': k}
                                                 for k, v in existing['term'].items()
                                                 if k in ok_terms])

        other_tabs = [(ConceptTermsReject,'term-reject'),
                      (ConceptPredictors, 'predictor'),
                      (ConceptPredictorsReject, 'predictor-reject')]
        for tab, ttype in other_tabs:
            if len(existing[ttype].keys()) > 0:
                r = conn.execute(tab.insert(), [{'concept_id': concept_id,
                                                 ttype.split('-')[0]: k}
                                                for k in existing[ttype].keys()])
    except Exception, e:
        print 'Problem inserting concept terms and predictors: %s' % e

    # write data to user log table
    try:
        r = conn.execute(UserHistoryCriteria.insert(), [{'user_id': user_id,
                                                         'update_time': v,
                                                         'concept_id': concept_id,
                                                         'new_concept': new_concept,
                                                         'update_type': t,
                                                         'value': k,
                                                         'accepted': 1}
                                                        for t in existing.keys()
                                                        if len(existing[t].keys()) > 0
                                                        for k, v in existing[t].items()])

        bad_terms = list(set(existing['term'].keys()) - set(ok_terms))
        if len(bad_terms) > 0:
            r = conn.execute(UserHistoryCriteria.update().\
                                                 where(and_(UserHistoryCriteria.c.concept_id == concept_id,
                                                            UserHistoryCriteria.c.update_type == 'term',
                                                            UserHistoryCriteria.c.value.in_(bad_terms))).\
                                                 values(accepted=0))
    except Exception, e:
        print 'Problem inserting user log data: %s' % e

    try:
        r = conn.execute(CriteriaConceptStaging.delete().where(CriteriaConceptStaging.c.concept_id == concept_id))
    except Exception, e:
        print 'Problem deleting concept %s: %s' % (concept_name, e)

    return flask.jsonify(concept_id=concept_id)

@app.route('/_write_criteria_rejection')
def write_criteria_rejection():
    params = request.args
    concept_id = params['concept_id']

    concept_data = conn.execute(select([CriteriaConceptStaging]).where(CriteriaConceptStaging.c.concept_id == concept_id)).fetchall()

    try:
        r = conn.execute(UserHistoryCriteria.insert(), [{'user_id': t[1],
                                                         'update_time': t[2],
                                                         'concept_id': t[3],
                                                         'new_concept': t[4],
                                                         'update_type': t[5],
                                                         'value': t[6],
                                                         'accepted': 0}
                                                        for t in concept_data])
    except Exception, e:
        print 'Problem writing rejection data: %s' % e

    try:
        r = conn.execute(CriteriaConceptStaging.delete().where(CriteriaConceptStaging.c.concept_id == concept_id))
        return flask.jsonify(done=True)
    except Exception, e:
        print 'Problem deleting concept %s: %s' % (concept_id, e)

    return flask.jsonify(done=False)

@app.route('/_associate_trials')
def associate_trials():
    params = request.args
    concept_id = params['concept_id']
    rnd = int(params['rnd'])
    num_trials = int(params['num_trials'])

    #pull the terms and all criteria sentences that match
    term_list = conn.execute(select([ConceptTerms.c.term, ConceptTerms.c.term_id]).\
                             where(ConceptTerms.c.concept_id == concept_id)).\
                     fetchall()
    
    criteria_text = conn.execute(select([CriteriaText.c.criteria_text,
                                         CriteriaText.c.criteria_text_id,
                                         CriteriaText.c.display_type,
                                         CriteriaText.c.nct_id]).\
                                 where(and_(CriteriaText.c.display_type != 'H',
                                            CriteriaText.c.random_select == rnd,
                                            or_(CriteriaText.c.criteria_text.op('rlike')('[[:<:]]' + t[0] + '[[:>:]]')
                                           for t in term_list))))
    
    #find all the sentences where a concept term occurs
    tagged_sentences = []
    for sent, sent_id, disp_type, nct_id in criteria_text:
        for term, term_id in term_list:
            if term in sent.lower():
                #check if there is a negative in the sentence related to the term.
                #the negative term has to be within 3 words of the concept term
                #or at the beginning of the sentece
                string = sent.lower()
                negative_pattern_start = r"^(not|no|isn't|didn't)"
                negative_beginning = re.search(negative_pattern_start, string)
                negative_in_sentence = re.search("(not|didn't|isn't|no)\W+(?:\w+\W+){0,3}%s" % (term), string)
                if negative_beginning or negative_in_sentence:
                    inverse = 1
                else:
                    inverse = 0
                if disp_type == 'E':
                    if inverse == 1:
                        inverse = 0
                    else:
                        inverse = 1
                tagged_sentences.append((sent_id, nct_id, term_id, inverse))
                
    #write tagged sentences to db
    for i in range(5):
        try:
            r = conn.execute(CriteriaConceptLookup.insert(), [{'criteria_text_id': v[0],
                                                        'nct_id': v[1],
                                                        'term_id': v[2],
                                                        'concept_id': concept_id,
                                                        'inverse': v[3]}
                                                       for v in tagged_sentences])

            num_trials += len(set([t[1] for t in tagged_sentences]))

            return flask.jsonify(num_trials=num_trials)

        except Exception, e:
            print 'Problem writing concept data: %s' % e
            global engine, conn
            engine, conn = initializeDB(mysqlusername, mysqlpassword, mysqlserver, mysqldbname)

    return flask.jsonify(num_trials=num_trials)









# admin mesh assignment page
@app.route('/approve_mesh')
def approve_mesh():
    return flask.render_template('approve_mesh.html')

@app.route('/_approve_assignments_load')
def approve_assignments_load():
    assignments = conn.execute(select([MeshAssignStaging.c.nct_id, 
                                       MeshAssignStaging.c.user_id,
                                       MeshAssignStaging.c.update_id,
                                       ConditionDescription.c.mesh_term]).\
                                select_from(MeshAssignStaging.join(ConditionDescription,
                                        MeshAssignStaging.c.condition_id == ConditionDescription.c.condition_id))).\
                            fetchall()

    if len(assignments) > 0:

        assign_dict = {}
        for nct_id, user_id, update_id, cond_name in assignments:
            if nct_id not in assign_dict:
                assign_dict[nct_id] = {'userid': user_id,
                                       'cond_name': {}}
            assign_dict[nct_id]['cond_name'][cond_name] = update_id

        nct_ids = list(set(t[0] for t in assignments))

        trial_desc = conn.execute(select([TrialSummary.c.nct_id,
                                          TrialSummary.c.brief_title]).\
                                  where(TrialSummary.c.nct_id.in_(nct_ids))).\
                          fetchall()

        trial_info = {t[0]: t[1] for t in trial_desc}
        for nct_id in assign_dict:
            assign_dict[nct_id]['title'] = trial_info[nct_id]

        uniq_user = list(set(t[1] for t in assignments))
        uinfo = conn.execute(select([Users.c.user_id, 
                                     Users.c.full_name,
                                     Users.c.institution]).where(Users.c.user_id.in_(uniq_user))).fetchall()

        user_info = {t[0]: {'name': t[1], 'institution': t[2]} for t in uinfo}
        for nct_id in assign_dict:
            assign_dict[nct_id]['username'] = user_info[assign_dict[nct_id]['userid']]['name']
            assign_dict[nct_id]['userinst'] = user_info[assign_dict[nct_id]['userid']]['institution']

        return flask.jsonify(assignments=assign_dict)

    return flask.jsonify(assignments={})

@app.route('/_write_assignment_approval')
def write_assignment_approval():
    params = request.args
    ok_assign = json.loads(params['ok_assign'])
    bad_assign = json.loads(params['bad_assign'])

    cond_info = conn.execute(select([MeshAssignStaging]).where(MeshAssignStaging.c.update_id.in_(ok_assign + bad_assign))).fetchall()

    good_updates = []
    bad_updates = []
    for update_id, user_id, update_time, nct_id, condition_id in cond_info:
        if str(update_id) in ok_assign:
            good_updates.append({'n': nct_id, 'cid': condition_id})
        else:
            bad_updates.append({'n': nct_id, 'cid': condition_id})

    print good_updates
    print bad_updates

    # write new rows for good updates
    r = conn.execute(ConditionLookup.insert(), [{'condition_id': t['cid'],
                                                 'nct_id': t['n'],
                                                 'source': 'ASSIGN',
                                                 'syn_flag': 0}
                                                for t in good_updates])

    # update rows so they don't show up in suggestions any more
    r = conn.execute(ConditionLookup.update().\
                        where(and_(ConditionLookup.c.nct_id == bindparam('n'),
                                   ConditionLookup.c.condition_id == bindparam('cid'),
                                   ConditionLookup.c.source.in_(['KNN','MAXENT','MTI']))).\
                        values(syn_flag=2), good_updates + bad_updates)
    
    # write user history
    r = conn.execute(UserHistoryMesh.insert(), [{'user_id': t[1],
                                                 'update_time': t[2],
                                                 'nct_id': t[3],
                                                 'condition_id': t[4],
                                                 'accepted': 1 if str(t[0]) in ok_assign else 0}
                                                for t in cond_info])

    # clear staging
    r = conn.execute(MeshAssignStaging.delete().where(MeshAssignStaging.c.update_id.in_(ok_assign + bad_assign)))

    return flask.jsonify(done=True)







# user creation and login
@app.route('/_create_user')
def create_user():
    name = request.args['name']
    inst_user = request.args['inst_user']
    email = request.args['email']
    username = request.args['username']
    pwd = md5(request.args['pwd']).hexdigest()

    already_taken = conn.execute(Users.select().where(Users.c.user_name == username)).fetchone()

    if already_taken:
        return flask.jsonify(result='Username is already taken. Please try another one.')
    else:
        res = conn.execute(Users.insert().values(user_name=username,
                                                 full_name=name,
                                                 institution=inst_user,
                                                 email_address=email,
                                                 password=pwd,
                                                 access_level='user'))
        if res.inserted_primary_key:
            flask.session['userid'] = res.inserted_primary_key[0]
            return flask.jsonify(result='ok',
                                 username=username)
        else:
            return flask.jsonify(result="Sorry, we couldn't create a new account for some reason. Please try again.")

@app.route('/_login')
def login():
    #flask.session.clear()
    username = request.args['username']
    pwd = md5(request.args['pwd']).hexdigest()

    in_db = conn.execute(Users.select().\
                            where(and_(Users.c.user_name == username,
                                       Users.c.password == pwd))).fetchone()

    if in_db:
        flask.session['userid'] = in_db[0]
        return flask.jsonify(result='ok',
                             username=username)
    else:
        return flask.jsonify(result='bad')

@app.route('/_logout')
def logout():
    #flask.session.clear()
    flask.session.pop('userid',None)
    return flask.jsonify(result='ok')

@app.route('/_check_login')
def check_login():
    userid = flask.session['userid'] if 'userid' in flask.session else None
    if 'userid' in flask.session:
        username, usertype = conn.execute(select([Users.c.user_name, Users.c.access_level]).\
                                            where(Users.c.user_id == flask.session['userid'])).fetchone()
    else:
        username = None
        usertype = None
    return flask.jsonify(logged_in='userid' in flask.session,
                         username=username,
                         admin=1 if usertype =='admin' else 0)

@app.route('/_clear_session')
def clear_session():
    thisuser = None
    if 'userid' in flask.session:
        thisuser = flask.session['userid']
    flask.session.clear()
    if thisuser:
        flask.session['userid'] = thisuser

    return flask.jsonify(done=True)










# about page
@app.route('/about')
def about():
    return flask.render_template('about.html')

# data page
@app.route('/data')
def data():
    return flask.render_template('data.html')

# contact page
@app.route('/contact')
def contact():
    print request.url_root
    return flask.render_template('contact.html',url=request.url_root)

# ratings description page
@app.route('/ratings_description')
def ratings_description():
    return flask.render_template('ratings_description.html')


# old ClinicalTrials Browser infoviz project
@app.route('/browser')
def browser():
    return flask.render_template('browser.html')
