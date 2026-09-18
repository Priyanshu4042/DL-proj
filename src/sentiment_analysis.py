import pandas as pd 

def FinBERT_sentiment_score(heading):
    """
    compute sentiment score using pretrained FinBERT on -1 to 1 scale. -1 being negative and 1 being positive
    """
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from transformers import pipeline
    tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')
    finbert = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')
    nlp = pipeline("sentiment-analysis", model=finbert, tokenizer=tokenizer)
    result = nlp(heading)
    if result[0]['label'] == "positive":
        return result[0]['score']
    elif result[0]['label'] == "neutral":
        return 0
    import argparse
    import pandas as pd


    def compute_vader_scores(texts):
        import nltk
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        nltk.download('vader_lexicon', quiet=True)
        analyzer = SentimentIntensityAnalyzer()
        scores = []
        for t in texts:
            if not t:
                scores.append(0.0)
                continue
            r = analyzer.polarity_scores(t)
            # use compound which is in [-1,1]
            scores.append(r.get('compound', 0.0))
        return scores


    def compute_finbert_scores(texts):
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')
        finbert = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')
        nlp = pipeline('sentiment-analysis', model=finbert, tokenizer=tokenizer)
        scores = []
        for t in texts:
            if not t:
                scores.append(0.0)
                continue
            r = nlp(t)
            lab = r[0]['label']
            val = r[0]['score']
            if lab == 'positive':
                scores.append(float(val))
            elif lab == 'neutral':
                scores.append(0.0)
            else:
                scores.append(-float(val))
        return scores


    def main():
        parser = argparse.ArgumentParser(description='Compute sentiment per-date from news_data.csv')
        parser.add_argument('--method', choices=['vader', 'finbert'], default='vader', help='Which sentiment engine to use (default: vader)')
        parser.add_argument('--infile', default='news_data.csv', help='Input cleaned news CSV (default: news_data.csv)')
        parser.add_argument('--outfile', default='sentiment.csv', help='Output sentiment CSV (default: sentiment.csv)')
        args = parser.parse_args()

        news_df = pd.read_csv(args.infile)

        texts = []
        for i in range(len(news_df)):
            # combine non-empty News columns into a single string per date
            news_list = news_df.iloc[i, 1:].astype(str).tolist()
            news_list = [s for s in news_list if s and s != '0' and s != 'nan']
            texts.append(' '.join(news_list))

        if args.method == 'finbert':
            scores = compute_finbert_scores(texts)
        else:
            scores = compute_vader_scores(texts)

        news_df['FinBERT score'] = scores
        news_df.to_csv(args.outfile, index=False)


    if __name__ == '__main__':
        main()