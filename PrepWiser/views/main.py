from django.conf import settings
from .ai import *
from .converttotxt import *

def main():
    print("inside main")
    directory = 'prepwiser/media/texts'
    output_folder = "prepwiser/media/texts/"
    num_clusters = 5  # Example cluster number
    
    input_folder = os.path.join(settings.BASE_DIR, 'prepwiser/media/pdfs')
    #openai.api_key = api_key
    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            file_path = os.path.join(input_folder, filename)
            text = pdf_to_text(file_path)
            # Save the text to a text file in the output folder with the same name as the PDF file
            output_file_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".txt")
            with open(output_file_path, 'w') as f:
                f.write(text)
                print("here")

    print("before questions")
    questions = extract_questions_from_directory(directory)
    num_clusters = 5
    syllabus_file = 'prepwiser/media/texts/syllabus.txt'
    print("syllabus file")
    labels = cluster_questions(questions, num_clusters, syllabus_file)
    for i in range(num_clusters):
        cluster_question = np.array(questions)[np.where(labels == i)[0]]
        print(f"Module {i+1}:")
        for question in cluster_question:
            print(f" - {question}")
        print()

    important_topics,data_dict = extract_important_topics(questions)
    print("Most important topics are:")
    #print(important_topics)

    # Save cluster questions to file
    with open('prepwiser/media/cluster_question.txt', 'w') as f:
        for i in range(num_clusters):
            cluster_question= np.array(questions)[np.where(labels == i)[0]]
            f.write(f"Module {i+1}:\n")
            for question in cluster_question:
                f.write(f" - {question}\n")
            f.write("\n")

    # Save OpenAI reply to file
    with open('prepwiser/media/reply.txt', mode='w', encoding='utf-8') as f:
        f.write(important_topics)
    with open('prepwiser/media/reply_stats.txt', mode='w', encoding='utf-8') as f:
        f.write(data_dict)


