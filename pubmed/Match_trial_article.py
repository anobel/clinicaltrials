#imports
import cPickle as pickle
import pandas as pd
import os


def match_trial_article(data, trial_mesh_dict, investigator_dict):
    invest_trial_article_dict = {}
    trial_associated_articles_dict = {}

    for invest in data:
        #skip investigators that have no articles
        if len(data[invest]) == 0:
            continue
        for trial in investigator_dict[invest]['Trials']:
            #if the trial does not have associated mesh terms skip it.
            if trial not in trial_mesh_dict.keys():
                continue
            for article in data[invest]:
                #check dates of trial and article, skip articles that were published
                #before the trial started
                trial_date = int(trial_mesh_dict[trial]['Date'].year)
                article_date = int(data[invest][article]['year'])
                if trial_date > article_date:
                    continue

                #score variable
                score = 0

                #get the intersection of mesh terms between the article and trial
                article_mesh = data[invest][article]['mesh']
                intersection = set([term[0].lower() for term in article_mesh]).intersection(map(lambda x: x.lower(),
                                                                                                trial_mesh_dict[trial]['Mesh']))
                #create score for article

                #add a point for the article being within 10 years of the trial
                #an addtional point for being within 5 years
                #if the year difference is greater than 10 a point is subtracted
                if (article_date - trial_date) <= 5:
                    score += 2
                elif (article_date - trial_date) <= 10:
                    score += 1
                else:
                    score += -1

                #add 1 point for every matching mesh term, add an aditional point if a primary
                #mesh term matched
                for mesh in set(article_mesh):
                    if mesh[0].lower() in intersection:
                        if mesh[1] == 'Y':
                            score += 2
                        else:
                            score += 1

                #if the score is greater that 3 it is assumed that the article and
                #trial are related
                if score > 3:
                    if invest not in invest_trial_article_dict:
                        invest_trial_article_dict[invest] = {}
                    if trial not in invest_trial_article_dict[invest]:
                        invest_trial_article_dict[invest][trial] = []
                    invest_trial_article_dict[invest][trial].append(article)
                    trial_associated_articles_dict[article] = data[invest][article]
    return invest_trial_article_dict, trial_associated_articles_dict

#load trial mesh dict
trial_mesh_dict = pickle.load(open('data/trial_mesh_dict.pkl', 'rb'))
#load investigator dict
investigator_dict = pickle.load(open('data/investigator_dict.pkl', 'rb'))

#load in data files to run
data_list = []
data_files = os.listdir('data/investigator_process/')
for f in data_files:
    if 'processed_' in f:
        data_list.append(f)

#list to keep track of which files have been run
run_files_list = []

#load pervious run files list
try:
    run_files_list = pickle.load(open('data/matching_run_file_list.pkl', 'wb'))
except:
    pass


for f in data_list:
    print f
    if f not in run_files_list:
        #load data to process
        data = pickle.load(open( f, 'rb'))

        #process data
        invest_trial_article_dict, trial_associated_articles_dict = match_trial_article(data, trial_mesh_dict, investigator_dict)

    if len(invest_trial_article_dict) > 0:
            #trial_match_ has all the investigators and trials with article ids matched to trials
            #trails_ has a dictionary of all the trials what were matched for lookup
            pickle.dump(invest_trial_article_dict, open('data/matched_trial_article/trial_match_' + f,'wb'))
            pickle.dump(trial_associated_articles_dict, open('data/matched_trial_article/trials_' + f,'wb'))

    pickle.dump(run_files_list, open('data/matching_run_file_list.pkl', 'wb'))

    del invest_trial_article_dict
    del trial_associated_articles_dict
    del data
    run_files_list.append(f)

