from GoogleNews import GoogleNews
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from datetime import datetime, date
import sys


news_search_string  = '2020 election'
pages               = 4

def gen_cal_dates(start_date, end_date):

    delta = end_date - start_date
    datetime_list  = pd.date_range(end = end_date, periods = delta.days+1).to_pydatetime().tolist()
    
    return datetime_list
    

def googlenews_extract(date_range, num_pages, search_text):

    ''' Use googlenews package to extract top X stories per day based on search string '''
    
    df_days = []
    
    #TODO: if we want to pull multiple years of data, perhaps add multi-threading...not necessary for < ~20 calls

    for date in date_range:
        
        result = []
        googlenews = GoogleNews(start=date, end=date)
        googlenews.search(search_text)
        print("Search Date = ", date)
        
        for i in range(0, num_pages):

            print('Executing GoogleNews call #', i+1)

            googlenews.getpage(i)
            result_next = googlenews.result()
            print("Total records returned: ", len(result_next))
            
            df = pd.DataFrame(result_next)   
            df['date_calendar'] = date
        
        df_days.append(df) 
        appended_data = pd.concat(df_days)

    # Drop duplicate titles
    appended_data = appended_data.drop_duplicates(subset=['title'])

    # Append to master news df
    df_news = appended_data.reset_index(drop=True).drop(['date'], axis=1)
      
    return df_news


def tokenize_headlines(df):
    
    headlines = df.title.tolist()

    all_bigrams = []

    for text in headlines:
        
        # remove punctuation
        tokenizer = nltk.RegexpTokenizer(r"\w+")
        tokens = tokenizer.tokenize(text)

        bigrm = nltk.bigrams(tokens)
        bigrams = list(bigrm)
        all_bigrams.append(bigrams)
        
    print(f"There are {len(all_bigrams)} bigrams in across all Headlines")

    return all_bigrams


def sentiment_scores(df, field):

    analyzer = SentimentIntensityAnalyzer()
    scores = df[field].apply(analyzer.polarity_scores).tolist()
    df_scores = pd.DataFrame(scores)
    df_scored = df.join(df_scores, rsuffix='_right')

    return df_scored


def main():

    datetime_list = gen_cal_dates(date(2020, 6, 1), date.today())

    stringdate_list = []
    for i in range(len(datetime_list)):
        format_date = datetime.strftime(datetime_list[i], "%m/%d/%Y")
        stringdate_list.append(format_date)
        
    min_date = stringdate_list[0] 
    max_date = stringdate_list[-1]
    min_date = min_date.replace("/", "-")
    max_date = max_date.replace("/", "-")

    print(f"There are {len(datetime_list)} days in the generated list from {min_date} to {max_date}")

    # Call API and specify number of pages to extract
    df_news = googlenews_extract(stringdate_list, pages, news_search_string)

    # Subset to having a description (valid news stories)
    df_news_subset = df_news[df_news.desc != ""].reset_index(drop=True)

    daily_cnts = df_news_subset.groupby('date_calendar')['title'].count().reset_index().rename(columns={'title':'cnt_stories'})

    daily_avg_cnt = daily_cnts['cnt_stories'].mean()

    print(f"There are {len(df_news_subset)} valid stories for search string '{news_search_string}' in the generated dataset (across {pages} pages each day)")
    print(f"There are {daily_avg_cnt} average stories per date")

    #TODO: bigram sentiment
    #all_bigrams = tokenize_headlines(df_news_subset)

    df_news_subset_scored = sentiment_scores(df_news_subset, 'title')
    df_news_subset_scored2 = sentiment_scores(df_news_subset_scored, 'desc')
    df_news_subset_scored2.rename(columns={'compound': 'compound_title', 'compound_right': 'compound_desc'}, inplace=True)
    df_news_subset_scored2.to_csv(f"'Election 2020' News for {min_date} through {max_date} with Sentiment Scores.csv", index=False)


if __name__== "__main__" :
    main()