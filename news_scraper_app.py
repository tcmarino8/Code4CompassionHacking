from flask import Flask, request, jsonify,  render_template
import requests
from bs4 import BeautifulSoup
import pandas as pd
import folium
from bs4 import BeautifulSoup
import regex as re
import spacy


app = Flask(__name__)


# Load the spaCy model for NER
nlp = spacy.load("en_core_web_sm")

def extract_location_from_article(url):
    try:
        # Fetch the article content
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the main content of the article
        # This may vary depending on the website structure
        paragraphs = soup.find_all('p')
        article_text = ' '.join([para.get_text() for para in paragraphs])

        # Process the text with spaCy
        doc = nlp(article_text)

        # Extract locations
        locations = set()
        for ent in doc.ents:
            if ent.label_ == "GPE":  # GPE stands for Geopolitical Entity
                locations.add(ent.text)

        return list(locations)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching article: {e}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    


animal_advocacy_words = [
    "adoption", "advocacy", "animal rights", "animal welfare", "anti-cruelty", 
    "awareness", "compassion", "conservation", "cruelty-free", "ecosystem", 
    "endangered", "ethical", "extinction", "foster", "habitat", "humane", 
    "legislation", "liberation", "meatless", "neglect", "nonprofit", "paws", 
    "petition", "preservation", "protection", "rehabilitation", "rescue", 
    "sanctuary", "sentience", "shelter", "speciesism", "sponsorship", "sustainability", 
    "symbiosis", "TNR (Trap-Neuter-Return)", "vegan", "vegetarian", "volunteer", 
    "wildlife", "zoonotic", "abolition", "advocate", "biodiversity", "captivity", 
    "care", "coexistence", "domestication", "ecology", "education", "empowerment", 
    "equity", "ethics", "foraging", "humane education", "legal protection", "marine life", 
    "migratory", "no-kill", "outreach", "policy", "rehoming", "reintroduction", "rights", 
    "spay/neuter", "stewardship", "suffering", "therapy animals", "treatment", "underprivileged animals", 
    "wildlife corridors", "zoos", "enrichment", "fair treatment", "farmed animals", "habitat restoration", 
    "law enforcement", "legislation reform", "livestock welfare", "marine conservation", "medical care", 
    "microchipping", "overpopulation", "pest control", "pro-animal", "reform", "rehab", "research alternatives", 
    "responsible ownership", "sentient beings", "species protection", "sterilization", "stray animals", 
    "sustainable practices", "veterinary care", "wildlife protection", "dog", "Cat", "abuse", "Damage", "Dead", "Welfare", "Death"
]


def find_animal_advocacy_words(text):


    # Find and return the advocacy words present in the text
    found_words = set()
    text = str.lower(text)
    for word in animal_advocacy_words:
        if word in text:
            found_words.add(word)

    return list(found_words)



def scrape_links_and_sources_based_on_interests(interests, location):
    articles = []
    for interest in interests:
        search_query = f"{interest} {location}".replace(" ", "+")
        url = f"https://news.google.com/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find articles and extract links and sources
            for item in soup.find_all('article'):

                item_str = str(item)
                match = re.search(r'aria-label="More - (.*?)"', item_str)
                title = match.group(1) if match else 'No title found'
                match = re.search(r'data-n-tid="9">(.*?)</div>', item_str)
                source = match.group(1) if match else 'No source found'
                key_words = find_animal_advocacy_words(item_str)
                
        

                link_tag = item.find('a')
                if link_tag and 'href' in link_tag.attrs:
    
                    link = link_tag['href']
                    
                    if link.startswith('.'):
                        link = 'https://news.google.com' + link[1:]

                    locations_found = "Nothing"
                    
                    articles.append({'link': link, 'title': title, 'source': source, "KeyWords": key_words, "Locations": locations_found})

            # Limit to 10 articles per interest
            if len(articles) >= 10:
                break

        except requests.exceptions.RequestException as e:
            print(f"Error fetching articles for {interest}: {e}")

    return articles[:10]  # Return the first 10 articles
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    data = request.json  # Get the JSON data from the request
    email = data.get('email')  # Extract the email
    interests = data.get('interests')  # Extract the interests
    location = data.get('location')

    # Log the received data to the console
    print(f"Received email: {email}")
    print(f"Received interests: {interests}")

    # Scrape links based on interests
    Information = scrape_links_and_sources_based_on_interests(interests, location)

    # Create a response message
    response_message = f"Thank you: {email}, Based on your Interests: {', '.join(interests)}, here are the most relevant Articles:"

    return jsonify({
        "message": response_message,
        "ArticleInformation": Information 
    })

if __name__ == '__main__':
    app.run(debug=True)