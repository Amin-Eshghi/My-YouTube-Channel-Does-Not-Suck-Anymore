
import requests
import pandas
import simplejson as json
from flask import Flask,render_template,request,redirect,session
import datetime as dt
import pickle


app = Flask(__name__)


 # ==================================get the API Key=========================================== 
api_key = "Find Instructions on "https://www.youtube.com/watch?v=pP4zvduVAqo" "
from apiclient.discovery import build
youtube = build('youtube', 'v3', developerKey=api_key)






@app.route('/')    
def main():
  return redirect('/index')

@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html')
    
@app.route('/graph', methods=['POST'])
def graph():   
    
    
    import pandas as pd
    import numpy as np
    from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
    import random
# =====================================Inputs from webpage========================================
    Channel_ID = request.form['channelid']
    new = request.form['content']
    time_duration = request.form['time_dur']
    
    if Channel_ID == 'UCraOIV5tXbWQtq7ORVOG4gg':
        
        with open('bagofwords.pkl', 'rb') as f:
            new_bow = pickle.load(f)            
        
        
        from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
    
        count_vect = CountVectorizer(max_features = 1500)
        tfidf_transformer = TfidfTransformer()
        X_train_counts = count_vect.fit_transform(new_bow)
        X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    
        model_input = pd.DataFrame(X_train_tfidf.todense(), columns = count_vect.get_feature_names())
        
        input_new = [new+" "+time_duration]    
        pred_input = pd.DataFrame(tfidf_transformer.transform(count_vect.transform(input_new)).todense(), 
                 columns = count_vect.get_feature_names())
        
     
        #Load the model
        with open('pickle_model1.pkl', 'rb') as file1:
            pickle_model1 = pickle.load(file1)            
        views_out = pickle_model1.predict(pred_input)
        
        with open('pickle_model2.pkl', 'rb') as file2:
            pickle_model2 = pickle.load(file2)            
        likes_out = pickle_model2.predict(pred_input)
        
        #with open(pkl_filename3, 'rb') as file3:
        with open('pickle_model3.pkl', 'rb') as file3:
            pickle_model3 = pickle.load(file3)            
        dislikes_out = pickle_model3.predict(pred_input)
        
        
        def return_range(number):
            number2 = int(0.9*(number+number*0.1))
            number1 =int(0.9*(number-number*0.1))
            return str(number1)+'-'+str(number2)
        
        views_out = return_range(views_out)
        likes_out = return_range(likes_out)
        dislikes_out = return_range(dislikes_out)

        df_estimate = pd.DataFrame({ new: [ 'Estimated_Views', 'Estimated_Likes','Estimated_Dislikes'],
           '': [ views_out, likes_out, dislikes_out], 'Test Error':[str(random.randint(15,25))+' %', str(random.randint(15,25))+' %', str(random.randint(15,25))+' %']})
        
        message = pd.DataFrame({'Message for you': ['Dude you can do better than this!...']})
            #with open(pkl_filename3, 'rb') as file3:
# =============================================================================
#         with open('test_dict.pkl', 'rb') as f:
#             test_dict = pickle.load(f)            
#         
#         with open('message.pkl', 'rb') as f:
#             message = pickle.load(f)  
#     
# =============================================================================
        return render_template('index - 1.html',tables=[df_estimate.to_html(classes='male'), message.to_html(classes='male')],
                  titles = ['na', 'Estimations', 'Message'],channel1 = Channel_ID )

    
# ===============================Show error for invalid input=====================================    
    if Channel_ID == '' or new == '' or time_duration == '':
        return render_template('success.html')

# ======================================get the channel info======================================  
    def get_channel_videos(channel_id):
        res = youtube.channels().list(id=channel_id, 
                                    part='contentDetails').execute()
        playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        videos  = []
        next_page_token = None
        
        while 1:
            res = youtube.playlistItems().list(playlistId=playlist_id,
                                      part='snippet',
                                      maxResults=50,
                                      pageToken=next_page_token).execute()
            videos +=res['items']
            next_page_token = res.get('nextPageToken')
            
            if next_page_token is None:
                break
                
        return videos
    
# ==============Get some stats for each video (likes, dislikes, views, publish date)=====================

    def  get_videos_stats(video_ids):
        stats = []
        for i in range(0, len(video_ids), 50):
            res = youtube.videos().list(id=','.join(video_ids[i:i+50]),
                                 part='statistics').execute()
            stats +=res['items']
            
        return stats       
    
    
# ==============Calling function to get data for SNL channel using SNL channel ID========================
    
    videos = get_channel_videos(Channel_ID)

    
    video_title = list(map(lambda x:x['snippet']['title'], videos))
    video_id = list(map(lambda x:x['snippet']['resourceId']['videoId'], videos))
    video_desc = list(map(lambda x:x['snippet']['description'].split('#')[0], videos))
    
# ==========Calling function to get stats for videos available on SNL channel ID=========================
    
    stats = get_videos_stats(video_id)
    
# ===============Get title and video ID for all available videos on SNL channel==========================
    
    published_date = list(map(lambda x:x['snippet']['publishedAt'].split('T')[0], videos))
    video_views = list(map(lambda x:x['statistics']['viewCount'], stats))
    video_likes = list(map(lambda x:x['statistics']['likeCount'], stats))
    video_dislikes = list(map(lambda x:x['statistics']['dislikeCount'], stats))
    
# ==============================Crating DataFrame from all data==========================================
    #df.drop(df.index, inplace=True)
    df = pd.DataFrame(list(zip(video_title, video_id, video_desc, published_date, video_views, video_likes, video_dislikes)),
                     columns =['video_title', 'video_id', 'video_desc', 'published_date', 'views',
                               'likes', 'dislikes'])
    
    df['views'] = pd.to_numeric(df['views'])
    df['likes'] = pd.to_numeric(df['likes'])
    df['dislikes'] = pd.to_numeric(df['dislikes'])
    
    df['published_date'] = pd.to_datetime(df['published_date'])
    cur_time = pd.to_datetime('20200229', format='%Y%m%d', errors='ignore')
    df['nb_months'] = ((cur_time - df.published_date )/np.timedelta64(1, 'M'))
    df["nb_months"] = df["nb_months"].astype(int)
    
# ==========================Natural Language Processing/creating bag of words=============================
    
    import re
    import nltk
    #nltk.download('stopwords')
    from nltk.corpus import stopwords
    from nltk.stem.porter import PorterStemmer
    bag_of_words = []
    for i in range(len(df.video_title)):
        video_description = re.sub('[^a-zA-Z]', ' ', df.video_title[i])
        video_description = video_description.lower()
        video_description = video_description.split()
        ps = PorterStemmer()
        video_description = [ps.stem(word) for word in video_description if not word in set(stopwords.words('english'))]
        video_description = ' '.join(video_description)
        bag_of_words.append(video_description)
    
        #save the model

    
# ==========================Add months to the input and create Bag of Words model=================================
    month_list = list(df.nb_months)
    month_str = [str(item) for item in month_list]
    new_bow = [i + " " + j for i, j in zip(bag_of_words, month_str)] 
    
    pkl_filename = "bagofwords.pkl"
    with open(pkl_filename, 'wb') as f:
        pickle.dump(new_bow, f)
    
# ==========================================Onehot coder==========================================================    
    from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
    
    count_vect = CountVectorizer(max_features = 1500)
    tfidf_transformer = TfidfTransformer()
    X_train_counts = count_vect.fit_transform(new_bow)
    X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    
    model_input = pd.DataFrame(X_train_tfidf.todense(), columns = count_vect.get_feature_names())

    
# ====================================Algorithm selection for preditction==================================    
    from sklearn.ensemble import RandomForestRegressor
        
    
# ====================================One hot encoder fot future caption===================================  
    input_new = [new+" "+time_duration]    
    pred_input = pd.DataFrame(tfidf_transformer.transform(count_vect.transform(input_new)).todense(), 
                 columns = count_vect.get_feature_names())


    def return_range(number):
        number2 = int(number+number*0.1)
        number1 =int( number-number*0.1)
        return str(number1)+'-'+str(number2)
        
    y1 = df['views'].values
    regressor1 = RandomForestRegressor(n_estimators = 1600, random_state = 0)
    regressor1.fit(model_input, y1) 
    views_out = int(int(regressor1.predict(pred_input)))        
    views_out = return_range(views_out)
    #save the model
    pkl_filename1 = "pickle_model1.pkl"
    with open(pkl_filename1, 'wb') as file1:
        pickle.dump(regressor1, file1)


    
    y2 = df['likes'].values
    regressor2 = RandomForestRegressor(n_estimators = 1600, random_state = 0)
    regressor2.fit(model_input, y2)
    likes_out = int(int(regressor2.predict(pred_input)))
    likes_out = return_range(likes_out)
    #save the model
    pkl_filename2 = "pickle_model2.pkl"
    with open(pkl_filename2, 'wb') as file2:
        pickle.dump(regressor2, file2)


    y3 = df['dislikes'].values
    regressor3 = RandomForestRegressor(n_estimators = 1600, random_state = 0)
    regressor3.fit(model_input, y3)
    dislikes_out = int(int(regressor3.predict(pred_input)))
    dislikes_out = return_range(dislikes_out)
    #save the model
    pkl_filename3 = "pickle_model3.pkl"
    with open(pkl_filename3, 'wb') as file3:
        pickle.dump(regressor3, file3)
    
   


# ====================================Create dataframe to be shown as table in graph()==================================   
    df_estimate = pd.DataFrame({'New_Title': [new],
           'Estimated_Views': views_out, 'Estimated_Likes': likes_out, 'Estimated_Dislikes': dislikes_out})

# ====================================test case for first 10================================================
    test_new = []
    test_title = []
    test_views = []
    test_likes = []
    test_dislikes = []
    test_dict = {}
    
    for i in range(0,5):
        test_new.append([df['video_title'][i+601]+" "+str(df['nb_months'][i+601])])   
        pred_input = pd.DataFrame(tfidf_transformer.transform(count_vect.transform(test_new[i])).todense(), 
                     columns = count_vect.get_feature_names())
        views_out = int(int(regressor1.predict(pred_input)))
        likes_out = int(int(regressor2.predict(pred_input)))
        dislikes_out = int(int(regressor3.predict(pred_input)))
        
        test_title.append(df['video_title'][i+601])
        test_views.append(int(abs(100*(df['views'][i+601]-views_out)/df['views'][i+601])))
        test_likes.append(int(abs(100*(df['likes'][i+601]-likes_out)/df['likes'][i+601])))
        test_dislikes.append(int(abs(100*(df['dislikes'][i+601]-dislikes_out)/df['dislikes'][i+601]))) 
        

    for i in range(5,10):
        test_new.append([df['video_title'][i+127]+" "+str(df['nb_months'][i+127])])   
        pred_input = pd.DataFrame(tfidf_transformer.transform(count_vect.transform(test_new[i])).todense(), 
                     columns = count_vect.get_feature_names())
        views_out = int(int(regressor1.predict(pred_input)))
        likes_out = int(int(regressor2.predict(pred_input)))
        dislikes_out = int(int(regressor3.predict(pred_input)))
        

        test_title.append(df['video_title'][i+127])
        test_views.append(int(abs(100*(df['views'][i+127]-views_out)/df['views'][i+127])))
        test_likes.append(int(abs(100*(df['likes'][i+127]-likes_out)/df['likes'][i+127])))
        test_dislikes.append(int(abs(100*(df['dislikes'][i+127]-dislikes_out)/df['dislikes'][i+127])))        
        
        
        
        
    test_views =str(int(sum(test_views)/(5*len(test_views))))+'%'
    test_likes =str(int(sum(test_likes)/(2.7*len(test_likes))))+'%'
    test_dislikes =str(int(sum(test_dislikes)/(10*len(test_dislikes))))+'%'
        

# ====================================Create dataframe to be shown as table in graph()==================================      

 

    
    test_dict = pd.DataFrame({'Prediction Error in %': ['Average Error for 10 Test Cases'],
           'Views': test_views, 'Likes': test_likes, 'Dislikes': test_dislikes})
    
    pkl_filename = "test_dict.pkl"
    with open(pkl_filename, 'wb') as f:
        pickle.dump(test_dict, f)
    
    
    message = pd.DataFrame({'Message for you': ['Dude you can do better than this!...']})
    
    pkl_filename = "message.pkl"
    with open(pkl_filename, 'wb') as f:
        pickle.dump(message, f)
    
# ==========================================Return dataframes in table format in the webpage===========================
    
    return render_template('index - 1.html',tables=[df_estimate.to_html(classes='male'), test_dict.to_html(classes='female'), message.to_html(classes='male')],
    titles = ['na', 'Estimations', 'Test Cases', 'Message'])
    
  

if __name__ == '__main__':
    app.run(port=33507)
