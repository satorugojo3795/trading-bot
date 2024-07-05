from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Tuple
device = "cuda:0" if torch.cuda.is_available() else "cpu:0"

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert").to(device)
labels = ["positive", "negative", "neutral"]

def estimate_sentiment(news):
    if news:
        tokens = tokenizer(news, return_tensors="pt", padding=True).to(device)
        result = model(tokens["input_ids"], attention_mask = tokens["attention_mask"])
        result = result["logits"]
        
        #now do batchwise aggreagation
        result = torch.sum(result, dim=0)
        
        #now apply softmax activation function
        #taking dim as -1 beacuse we want to take the softmax along the last dimension that are our labels even if we pass dim=0 we  will get the same result
        result = torch.nn.functional.softmax(result, dim=-1)
        
        #get the corresponging probabalilty
        probability =  result[torch.argmax(result)]
        
        #get the corresponding sentiment
        sentiment = labels[torch.argmax(result)]
        
        return probability, sentiment
    
if __name__ == "__main__":
    tensor, sentiment = estimate_sentiment(['markets responded negatively to the news!','traders were displeased!'])
    print(tensor, sentiment)
    print(torch.cuda.is_available())
        
        
        