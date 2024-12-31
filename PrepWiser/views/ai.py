import os
import re
import chardet
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import dendrogram, linkage
from nltk.tokenize import word_tokenize
from collections import Counter
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.cluster.hierarchy import linkage
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage
from sklearn.feature_extraction.text import CountVectorizer
from collections import Counter
from sklearn.decomposition import LatentDirichletAllocation
import json



def extract_questions_from_file(filepath):
    print("extract questions")
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    with open(filepath, encoding=encoding) as f:
        content = f.read()
        pattern = r'((?:[IVX]+|\([a-z]\))\. .*(?:\n\s+\(\w\)\. .*)*)'
        matches = re.findall(pattern, content)
        questions = [re.sub(r'\n\s+\(\w\)\. ', ' ', match.strip()) for match in matches]
        print("questions")
    return questions

def extract_questions_from_directory(directory):
    questions = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            questions += extract_questions_from_file(filepath)
    return questions

def clean_topics(syllabus_file):
    with open(syllabus_file, 'r') as file:
        syllabus_topics = file.read().splitlines()
    syllabus_topics = list(set(topic.strip() for topic in syllabus_topics if topic.strip()))
    return syllabus_topics

def extract_key_topics(questions, syllabus_topics):
    vectorizer = TfidfVectorizer(vocabulary=syllabus_topics)
    X = vectorizer.fit_transform(questions)
    
    topic_counts = np.sum(X.toarray(), axis=0)
    topics_freq = dict(zip(vectorizer.get_feature_names_out(), topic_counts))
    
    return topics_freq

def get_cluster_topic_distribution(questions, labels, syllabus_topics):
   
    
    vectorizer = TfidfVectorizer(vocabulary=syllabus_topics)
    cluster_topic_freq = {}
    for cluster in np.unique(labels):
        cluster_indices = np.where(labels == cluster)[0]
        cluster_questions = [questions[i] for i in cluster_indices]
        cluster_X = vectorizer.fit_transform(cluster_questions)
        
        topic_counts = np.sum(cluster_X.toarray(), axis=0)
        topics_freq = dict(zip(vectorizer.get_feature_names_out(), topic_counts))
        cluster_topic_freq[cluster] = topics_freq
        
    return 

def assign_topic_names_to_clusters(questions, labels, num_clusters):
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(questions)
    
    lda = LatentDirichletAllocation(n_components=num_clusters, random_state=42)
    lda.fit(X)
    
    feature_names = vectorizer.get_feature_names_out()
    topic_names = []
    for topic_idx, topic in enumerate(lda.components_):
        top_features_indices = topic.argsort()[:-6:-1]
        top_features = [feature_names[i] for i in top_features_indices]
        topic_names.append(" ".join(top_features))
    
    cluster_topic_names = {}
    for cluster in range(num_clusters):
        cluster_indices = np.where(labels == cluster)[0]
        cluster_questions = [questions[i] for i in cluster_indices]
        topic_distribution = lda.transform(vectorizer.transform(cluster_questions))
        dominant_topic = np.argmax(topic_distribution, axis=1)
        most_common_topic = Counter(dominant_topic).most_common(1)[0][0]
        cluster_topic_names[cluster] = topic_names[most_common_topic]
    
    return cluster_topic_names
    


def cluster_questions(questions, num_clusters, syllabus_file):
    # module_url = "https://www.kaggle.com/models/google/universal-sentence-encoder/TensorFlow2/large/2"
    # module_url = "https://www.kaggle.com/models/google/universal-sentence-encoder/TensorFlow1/large/3"
    module_url = "https://www.kaggle.com/models/google/universal-sentence-encoder/TensorFlow2/universal-sentence-encoder/2"
    embed = hub.load(module_url)
    embeddings = embed(questions)
    embeddings = embeddings.numpy()
   
    kmeans = KMeans(n_clusters=num_clusters)
    kmeans.fit(embeddings)
    y_kmeans = kmeans.predict(embeddings)
    # syllabus_topics=clean_topics(syllabus_file)
    # overall_topics_freq = extract_key_topics(questions, syllabus_topics)
    # cluster_topic_freq = get_cluster_topic_distribution(questions, y_kmeans, syllabus_topics)
    # cluster_topic_names = assign_topic_names_to_clusters(questions, y_kmeans, num_clusters)
    # print('cluster topic frequenxy')
    # print(cluster_topic_freq)
    # print('cluster_topic_names')
    # print(cluster_topic_names)
    # print('overall_topics_freq')
    # print(overall_topics_freq)
    return y_kmeans
  
        # pca = PCA(n_components=2)
    # principalComponents = pca.fit_transform(embeddings)
    # linkage_matrix = linkage(embeddings, method='ward', metric='euclidean')
    # plt.figure(figsize=(15, 10))
    # plt.title("Dendrogram")
    # dendrogram(linkage_matrix, truncate_mode='level', p=15, leaf_font_size=10)
    # plt.xlabel("Number of points in node (or index of point if no parenthesis).")
    # plt.ylabel("Distance between centroids")
    # plt.show()
    # plt.figure(figsize=(10, 10))
    # plt.scatter(principalComponents[:, 0], principalComponents[:, 1], c=y_kmeans, s=50, cmap='viridis')
    # centers = kmeans.cluster_centers_
    # plt.scatter(centers[:, 0], centers[:, 1], c='black', s=200, alpha=0.5)
    # plt.axis('off')
    # plt.show()
   


def extract_important_topics(questions):
    text = '\n'.join(questions)
    # print(text)
    
# {text} should be replaced or appended with actual topic names you want to focus on.
    prompt=f'''Given this set of questions:{text}, cluster them into exactly 5 clusters based on their semantic topic similarity. The clusters should be formed based on the overall semantic meaning of the questions rather than just matching topic names. Each question should be a part of some cluster. For each cluster, provide the following detailed information:

        Topic Name: A meaningful name for each cluster derived from the most representative and specific technical keywords.
        Number of Questions: The total number of questions within this cluster.
        Keyword Frequency Map: A map of the atmost 4 most important technical subtopics (keywords) relevant to the subject matter, along with their respective frequencies within the cluster. Exclude general and non-technical words from this map.
        Give it in minified json format.
        Format of output:
        Example:{{"topics":[{{"Topic_Name":"Calculus","Number_of_Questions":25,"Keyword_Frequency":{{"derivatives":15,"integrals":10,"limits":5,"functions":8,"series":3}}}},{{"Topic_Name":"Algebra","Number_of_Questions":30,"Keyword_Frequency":{{"equations":12,"inequalities":8,"polynomials":5,"exponents":10,"functions":5}}}}]}}

        Ensure that the keyword frequency map focuses on significant technical subtopics pertinent to the subject matter, excluding generic or non-technical terms. Make sure the number of clusters formed is excatly 5.'''
    client=OpenAI(api_key="")
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        # prompt=f"create a table (extract atleast 6 important topic names and give all utube link to study those important topic) and give extra similar 3 questions from each topic with their answer in the format topic,youtube link,3 question and answer for each topic :\n\n{text}\n\n",
        prompt=prompt,
        temperature=0.5,
        max_tokens=2048,
    )
    data = response.choices[0].text
    data_dict = json.loads(data)

    # Extract topic names and store them in a comma-separated string
    topic_names = ', '.join(topic['Topic_Name'] for topic in data_dict['topics'])
    #topic_names = ', '.join(topic["Topic_Name"] for topic in data["topics"])
    print("important topics")
    print(data)
    print(topic_names)
    prompt2=f"""
    Create a structured table containing information about six important topics. For each topic, provide three additional questions related to the topic with their respective answers. Use the following format for each entry:

    Topic Name: [Name of the Topic]
    Question 1: [First question]
    Answer 1: [Answer to first question]
    Question 2: [Second question]
    Answer 2: [Answer to second question]
    Question 3: [Third question]
    Answer 3: [Answer to third question]

    Example:

    Topic Name: Digital Logic Design
    Question 1: What is the difference between combinational and sequential circuits?
    Answer 1: Combinational circuits use logic gates to perform a specific function, while sequential circuits use memory elements to store information and perform a sequence of operations.
    Question 2: How do you convert a Boolean expression into a logic circuit?
    Answer 2: By using logic gates such as AND, OR, and NOT gates to represent the Boolean expression and connecting them together according to the logic.
    Question 3: How do you implement a full adder using only half adders?
    Answer 3: A full adder can be implemented using two half adders and an OR gate to handle the carry bit.

    Please create similar entries for the following topics: {topic_names}.
    """
    client=OpenAI(api_key="")
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        # prompt=f"create a table (extract atleast 6 important topic names and give all utube link to study those important topic) and give extra similar 3 questions from each topic with their answer in the format topic,youtube link,3 question and answer for each topic :\n\n{text}\n\n",
        prompt=prompt2,
        temperature=0.5,
        max_tokens=2048,
    )
    important_topics= response.choices[0].text
    # print(important_topics)
    print(important_topics)
    return important_topics,data


