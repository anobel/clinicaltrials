#!../clinicaltrials/env/bin/python
from ctapp import app
import flask
from flask import request
import pymongo
from connect import mongoip

# initializing global variables
#mongoip = 'localhost'
inst_rating_info = 'These currently do not have any meaning.'
inst_trials_active_info="Trials with status recruiting or active."
cond_name_mesh_info = 'MeSH is a hierarchy of medical subject headings.'

def mongo_connect(ip):
    conn = pymongo.MongoClient(host=ip)
    db = conn.ctdb
    return db

# homepage
@app.route('/')
def home():
    return flask.render_template('index.html')

# institution page
@app.route('/institution')
def institution():
    params = request.args
    if 'inst' in params:
        db = mongo_connect(mongoip)
        inst_data = db.institutions.find_one({'inst_id': str(params['inst'])})
        return flask.render_template('institution.html',
                                inst_name=inst_data['inst_name'],
                                inst_loc=inst_data['inst_loc'],
                                inst_img=inst_data['inst_img'],
                                inst_summary=inst_data['inst_summary'],
                                trials_active=inst_data['inst_trials_active'],
                                inst_trials_active_info=inst_trials_active_info,
                                inst_researchers=inst_data['inst_researchers'],
                                inst_pubs=inst_data['inst_pubs'],
                                inst_cond_top=inst_data['inst_cond_top'],
                                inst_rating=inst_data['inst_rating'],
                                inst_rating_info=inst_rating_info
                                )
    else:
        return flask.render_template('index.html')

# top conditions JSON
@app.route('/_top_condition')
def top_condition():
    params = request.args
    if 'inst' in params:
        db = mongo_connect(mongoip)
        inst_data = db.institutions.find_one({'inst_id': str(params['inst'])})
        return flask.jsonify(result=inst_data['inst_cond_top'])

# condition page
@app.route('/condition')
def condition():
    params = request.args
    if 'cond' in params:
        db = mongo_connect(mongoip)
        cond_data = db.conditions.find_one({'cond_id': int(params['cond'])})
        return flask.render_template('condition.html', 
                                    cond_name=cond_data['cond_name'],
                                    cond_name_mesh=cond_data['cond_name_mesh'],
                                    cond_summary=cond_data['cond_summary'],
                                    cond_synonyms=cond_data['cond_synonyms'],
                                    trials_active=cond_data['cond_trials_active'],
                                    institution_list=cond_data['cond_inst_top'],
                                    cond_name_mesh_info=cond_name_mesh_info
                                    )
    else:
        return flask.render_template('index.html')


# old ClinicalTrials Browser infoviz project
@app.route('/browser')
def browser():
    return flask.render_template('browser.html')