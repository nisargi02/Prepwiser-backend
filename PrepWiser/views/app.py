from collections import defaultdict
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import os
import subprocess
from .main import main
import re
from googleapiclient.discovery import build
import json
# import google.generativeai as genai
from openai import OpenAI
import time

class FileUploadSerializer(serializers.Serializer):
    pdf_files = serializers.ListField(child=serializers.FileField(), required=True)
    syllabus_files = serializers.FileField(required=False)


class FileUploadView(APIView):
    def module_answers(self,questions):
        # Replace with your actual API key
        formatted_questions = "\n".join(f"- {q}" for q in questions)
        print(questions)
        print("formatted questions")
        print(formatted_questions)
        prompt = f"""
        Given the set of questions: {formatted_questions}, please provide answers for each question. The responses should be formatted as a single line of minified JSON. Each question should be a key, and the corresponding answer should be the value in the JSON object. Refer to the example format provided below for guidance on structuring your responses:

        Example output format:
       {{"question1":{{"question":"What is a compiler?","answer":"Compilers are software that translate high-level programming languages to machine code that can be executed by a computer."}},"question2":{{"question":"What is an XOR gate?","answer":"XOR gate is a digital logic gate that outputs true or 1 only when the two binary bit inputs to it are unequal."}}}}
        Please ensure that all outputs are provided strictly in the specified minified JSON format only.
        """
        
        client=OpenAI(api_key="")
        response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        # prompt=f"create a table (extract atleast 6 important topic names and give all utube link to study those important topic) and give extra similar 3 questions from each topic with their answer in the format topic,youtube link,3 question and answer for each topic :\n\n{text}\n\n",
        prompt=prompt,
        temperature=0.5,
        max_tokens=2048,
    )
        data = response.choices[0].text
        print(data)
        data_dict = json.loads(data)
        print(data_dict)
        return data_dict



    def get_top_video(self,topic_name):
    # Build a service object for interacting with the API. Visit the Google Developers Console
    # to generate your API key.
        
        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = "AIzaSyD38VenuMEiVNTPN4AlRXanr_l7RPeyWC8"

        youtube = build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

        try:
            # Call the search.list method to retrieve results matching the specified topic name.
            search_response = youtube.search().list(
                q=topic_name,
                part="id,snippet",
                maxResults=1,
                type="video",
                order="viewCount"  # You can change this to 'viewCount' or other sort orders as needed
            ).execute()

            top_video = search_response['items'][0]
            video_title = top_video['snippet']['title']
            video_id = top_video['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            print(f"Top video title: {video_title}")
            print(f"Video URL: {video_url}")
            return video_url

        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")

    def parse_questions_by_module(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'cluster_question.txt'), 'r') as file:
            content = file.read()

        modules = {}
        current_module = None
        for line in content.split('\n'):
            module_match = re.match(r'^Module (\d+):', line)
            if module_match:
                current_module = f'Module {module_match.group(1)}'
                modules[current_module] = []
            elif current_module and line.strip():
                modules[current_module].append(line.strip())
        module_answer = {}
        for module, questions in modules.items():
            answers = self.module_answers(questions)
            module_answer[module] = answers
        print(module_answer)
        return module_answer
        


    def parse_reply_text(self):
        path = os.path.join(settings.MEDIA_ROOT, 'reply.txt')
        with open(path, 'r') as file:
            text = file.read()

        # Normalize line endings and split into sections by "Topic Name:"
        segments = re.split(r'\n(?=Topic Name:)', text)

        data = {}
        question_pattern = re.compile(r'^Question (\d+): (.+?)\nAnswer (\d+): (.*?)(?=\nQuestion \d+:|\Z)', re.DOTALL | re.MULTILINE)

        for segment in segments:
            # Extract the topic name and YouTube link
            topic_match = re.search(r'^Topic Name: (.+)$', segment, re.MULTILINE)
            # link_match = re.search(r'^YouTube Link: (.+)$', segment, re.MULTILINE)
            
            if topic_match:
                topic = topic_match.group(1)
                data[topic] = {
                    'youtube_link': '',
                    'questions': []
                }

                # Extract all questions and their answers
                questions = question_pattern.findall(segment)
                for q_num, question, a_num, answer in questions:
                    data[topic]['questions'].append({
                        'question': question.strip(),
                        'answer': answer.strip()
                    })
        print(data)
        return data


        
    def post(self, request):
        pdf_files=['PrepWiser_pdf6.pdf', 'PrepWiser_pdf5.pdf', 'PrepWiser_pdf4.pdf', 'PrepWiser_pdf3.pdf', 'PrepWiser_pdf2 (1).pdf', 'PrepWiser_pdf1.pdf']
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            pdfs = request.FILES.getlist('pdf_files')
            syllabus = request.FILES.get('syllabus_files')
            if sorted([pdf.name for pdf in pdfs])==sorted(pdf_files):
                stats={'topics': [{'Topic_Name': 'Boolean Logic', 'Number_of_Questions': 7, 'Keyword_Frequency': {'half adders': 3, 'carry propagation delay': 1, 'synchronous counter': 1, 'PLA circuit': 1, 'TTL NAND gate': 1}}, {'Topic_Name': 'Binary Adders', 'Number_of_Questions': 4, 'Keyword_Frequency': {'binary parallel adder': 2, 'decimal adder': 1, 'magnitude comparator': 1, 'BCD adder': 1}}, {'Topic_Name': 'Latch and Flip-Flop', 'Number_of_Questions': 4, 'Keyword_Frequency': {'SR latch': 2, 'RTL NOR gate': 1, 'D flip-flop': 1, 'JK flip-flop': 1}}, {'Topic_Name': 'Combinational Circuit Design', 'Number_of_Questions': 4, 'Keyword_Frequency': {'ROM': 1, 'multiplexer': 1, 'fan-in': 1, 'fan-out': 1}}, {'Topic_Name': 'Logic Families', 'Number_of_Questions': 3, 'Keyword_Frequency': {'TTL': 2, 'CMOS': 1, 'DTL': 1}}]}  
                structured_reply_text={'Boolean Logic': {'youtube_link': 'https://www.youtube.com/watch?v=gI-qXk7XojA', 'questions': [{'question': 'What are the three basic operations in Boolean logic?', 'answer': 'The three basic operations in Boolean logic are AND, OR, and NOT.'}, {'question': 'How can Boolean logic be used in digital circuits?', 'answer': 'Boolean logic can be used to design and analyze digital circuits by representing the inputs and outputs as Boolean variables.'}, {'question': 'What is the difference between Boolean logic and traditional logic?', 'answer': 'Boolean logic uses only two values (0 and 1) to represent logical statements, while traditional logic uses multiple values (true, false, unknown) to represent statements.'}]}, 'Binary Adders': {'youtube_link': 'https://www.youtube.com/watch?v=RK3P9L2ZXk4', 'questions': [{'question': 'What is the purpose of a binary adder?', 'answer': 'A binary adder is used to perform addition of two binary numbers.'}, {'question': 'How does a half adder differ from a full adder?', 'answer': 'A half adder can only add two single-bit numbers, while a full adder can add two single-bit numbers and a carry bit.'}, {'question': 'What is the difference between a ripple carry adder and a carry lookahead adder?', 'answer': 'A ripple carry adder calculates the carry bit for each stage sequentially, while a carry lookahead adder calculates all carry bits simultaneously.'}]}, 'Latch and Flip-Flop': {'youtube_link': 'https://www.youtube.com/watch?v=LYfsCllPZ2w', 'questions': [{'question': 'What is the difference between a latch and a flip-flop?', 'answer': 'A latch is level-sensitive and can change its output as long as the enable signal is active, while a flip-flop is edge-triggered and only changes its output on a clock edge.'}, {'question': 'How can latches and flip-flops be used in sequential circuits?', 'answer': 'Latches and flip-flops can be used as memory elements to store and manipulate data in sequential circuits.'}, {'question': 'What is the setup time and hold time of a flip-flop?', 'answer': 'The setup time is the minimum amount of time the input signal needs to be stable before the clock edge, and the hold time is the minimum amount of time the input signal needs to be stable after the clock edge.'}]}, 'Combinational Circuit Design': {'youtube_link': 'https://www.youtube.com/watch?v=1ObgDmqWamY', 'questions': [{'question': 'What is the difference between a decoder and a multiplexer?', 'answer': 'A decoder has multiple inputs and a single output, while a multiplexer has multiple inputs and selects one of them as the output based on a select signal.'}, {'question': 'How can Karnaugh maps be used in combinational circuit design?', 'answer': 'Karnaugh maps can be used to simplify Boolean expressions and minimize the number of logic gates needed in a combinational circuit.'}, {'question': 'What is the difference between a half adder and a full adder in terms of logic gate complexity?', 'answer': 'A half adder requires two logic gates (AND and XOR) while a full adder requires three logic gates (two half adders and an OR gate).'}]}, 'Logic Families': {'youtube_link': 'https://www.youtube.com/watch?v=3oNzkS1WYas', 'questions': [{'question': 'What is the purpose of a logic family?', 'answer': 'A logic family is a set of logic gates and other digital components that use the same design approach and are compatible with each other.'}, {'question': 'How do TTL and CMOS logic families differ?', 'answer': 'TTL (Transistor-Transistor Logic) uses bipolar transistors while CMOS (Complementary Metal-Oxide-Semiconductor) uses both p-channel and n-channel MOSFETs.'}, {'question': 'What are the advantages and disadvantages of using ECL (Emitter-Coupled Logic)?', 'answer': 'ECL has high speed and low power consumption but is more complex and expensive to design and manufacture compared to other logic families.'}]}} 
                module_questions={'Module 1': {'question1': {'question': 'Compare TTL and CMOS logic families.', 'answer': 'TTL and CMOS are two types of logic families used in digital circuits. TTL (Transistor-Transistor Logic) uses bipolar transistors while CMOS (Complementary Metal-Oxide-Semiconductor) uses MOSFETs. TTL is faster and more power-hungry than CMOS, while CMOS is slower but more power-efficient. TTL is more susceptible to noise and has a narrower voltage range, while CMOS is less susceptible to noise and has a wider voltage range. Overall, CMOS is the more commonly used logic family in modern digital circuits due to its lower power consumption and noise immunity.'}}, 'Module 2': {'question1': {'question': 'Explain the working of a 4-bit magnitude comparator.', 'answer': 'A 4-bit magnitude comparator is a digital circuit that compares two 4-bit binary numbers and determines whether one is greater than, less than, or equal to the other. It does this by comparing the most significant bit (MSB) first, and if they are equal, it moves on to compare the next bit and so on. If at any point, the bits are unequal, the result is determined and the comparison stops. The output of the comparator is a 3-bit code that indicates the result of the comparison.'}, 'question2': {'question': 'Derive the expressions for a 4-bit magnitude comparator and implement it.', 'answer': 'The expressions for a 4-bit magnitude comparator can be derived by using a combination of AND, OR, and NOT gates. The inputs of the comparator are the two 4-bit numbers A and B, and the outputs are A>B, A=B, and A<B. The expressions for these outputs can be written as A>B = (A3B3 + A3B2B1 + A3B1B0 + A2B3B2 + A2B3B1B0 + A1B3B2B1 + A1B3B1B0 + A0B3B2B1B0), A=B = (A3B3 + A2B2 + A1B1 + A0B0), and A<B = (A3B3 + A2B3B2 + A1B3B2B1 + A0B3B2B1B0). These expressions can then be implemented using logic gates to create a 4-bit magnitude comparator.'}}, 'Module 3': {'question1': {'question': 'Given the set of questions: - - VII. (a) Draw the logic diagram of a four-bit binary ripple counter. Show that a (6)', 'answer': "A four-bit binary ripple counter is a sequential circuit that counts from 0 to 15 in binary. It consists of four D flip-flops, with each flip-flop's output connected to the next flip-flop's input. The clock signal is connected to the first flip-flop, and the output of the fourth flip-flop is connected to the input of the first flip-flop. This creates a ripple effect, where each flip-flop's output changes on the rising edge of the clock signal. The counter can be represented by a logic diagram with four D flip-flops and AND gates connecting the outputs of the flip-flops to the inputs of the next flip-flop."}, 'question2': {'question': 'VIII. (a) Design a PLA circuit to implement the functions (6)', 'answer': 'A PLA (Programmable Logic Array) is a type of programmable logic device that consists of a programmable AND array and a fixed OR array. To implement a function using a PLA, the inputs are connected to the AND gates and the outputs are connected to the OR gates. The connections between the inputs and AND gates can be programmed using a set of fuse or antifuse links. The connections between the AND gates and OR gates are fixed. The outputs of the OR gates represent the function implemented by the PLA.'}, 'question3': {'question': 'VII. Differentiate PLA and PAL. Draw the PLA for functions: (10)', 'answer': 'PLA (Programmable Logic Array) and PAL (Programmable Array Logic) are both types of programmable logic devices. The main difference between the two is that PLA has a programmable AND array and a fixed OR array, while PAL has a fixed AND array and a programmable OR array. This means that PLA can implement more complex functions compared to PAL. A PLA can be represented by a logic diagram with inputs connected to AND gates and outputs connected to OR gates, while a PAL can be represented by a logic diagram with inputs connected to OR gates and outputs connected to AND gates.'}, 'question4': {'question': 'IX. (a) Draw and explain the working of Basic RTL NOR gate. (5)', 'answer': 'A basic RTL NOR gate is a digital logic gate that outputs a 1 only when both inputs are 0. It consists of two transistors, with the inputs connected to the gates of the transistors and the outputs connected to the drain of the transistors. When both inputs are 0, both transistors are turned on, creating a low resistance path from Vdd to the output, resulting in a 1. When either input is 1, the corresponding transistor is turned off, creating a high resistance path and resulting in a 0 output.'}, 'question5': {'question': 'VIII. Write short notes on (1) Fan in and Fan out (ii) Propogation delay', 'answer': 'Fan in and fan out are terms used to describe the number of inputs and outputs, respectively, of a logic gate. The fan in of a gate is the number of inputs connected to the gate, while the fan out is the number of outputs connected to the gate. Propagation delay is the time it takes for a change in input to result in a change in output of a logic gate. It is caused by the time it takes for signals to propagate through the components of the gate, such as transistors and wires. A lower propagation delay is desirable as it allows for faster operation of digital circuits.'}}, 'Module 4': {'question1': {'question': 'Implement the following four Boolean expressions with three half adders:', 'answer': 'A half adder is a combinational logic circuit that adds two single binary digits A and B. It has two outputs, Sum (S) and Carry (C). The expressions can be implemented as follows:\nS = A XOR B\nC = A AND B'}, 'question2': {'question': 'What is Carry Propagation delay? Design a 4-bit binary parallel adder', 'answer': 'Carry Propagation delay is the time taken for the carry output to stabilize after a change in the inputs. A 4-bit binary parallel adder can be designed using four full adders and a carry lookahead generator. The carry lookahead generator reduces the carry propagation delay by generating the carry signals in advance.'}, 'question3': {'question': 'Design a synchronous counter using .T flip-flops which counts', 'answer': 'A synchronous counter can be designed using .T flip-flops by connecting the output of one flip-flop to the clock input of the next flip-flop. The count sequence can be determined by the number of flip-flops used. For example, a 3-bit synchronous counter using .T flip-flops can count from 0 to 7.'}, 'question4': {'question': 'Design a 2 bit synchronous up counter using .1K flipflops.', 'answer': 'A 2-bit synchronous up counter can be designed using two .1K flip-flops by connecting the output of one flip-flop to the clock input of the next flip-flop. The count sequence can be determined by the number of flip-flops used. For example, a 2-bit synchronous up counter using .1K flip-flops can count from 0 to 3.'}, 'question5': {'question': 'Explain the working of a 4-bit BCD adder with block diagram', 'answer': 'A 4-bit BCD adder is a combinational logic circuit that adds two BCD numbers and produces a BCD result. It can be implemented using four full adders and a BCD to binary converter. The BCD to binary converter converts the BCD inputs to binary, which are then added using the full adders. The resulting binary sum is then converted back to BCD using a binary to BCD converter.'}, 'question6': {'question': 'Design a combinational circuit using a ROM.The circuit accepts three bit', 'answer': 'A combinational circuit can be designed using a ROM (Read-Only Memory) by storing the truth table of the desired function in the ROM. The inputs of the circuit are connected to the address lines of the ROM, and the output is obtained from the corresponding data lines. The ROM acts as a lookup table, providing the output based on the input combination.'}, 'question7': {'question': 'Design a decimal adder using 4-bit binary parallel adders.', 'answer': 'A decimal adder can be designed using 4-bit binary parallel adders by converting the decimal inputs to binary, adding them using the binary adders, and then converting the binary sum back to decimal. The carry output of each adder is connected to the carry input of the next adder to handle any carry-over.'}, 'question8': {'question': 'Implement the following function using a multiplexer, please provide answers for each question.', 'answer': 'A multiplexer is a combinational logic circuit that selects one of the inputs based on the select lines. The function can be implemented using a 4-to-1 multiplexer with the three inputs connected to the select lines and the fourth input connected to the output. The truth table for the function can be used to determine the select lines for each input. For example, if the function is F = A + B, the select lines would be 00 for A, 01 for B, and 11 for the output.'}}, 'Module 5': {'question1': {'question': 'Draw circuit of an TTL NAND gate and explain the operation.', 'answer': 'A TTL NAND gate is a digital logic gate that outputs a low or 0 signal when both of its inputs are high or 1. The circuit consists of two transistors connected in parallel with their emitters tied together. When both inputs are high, the transistors are turned on, creating a low output. When one or both inputs are low, at least one of the transistors is turned off, resulting in a high output. This operation is based on the principle of Boolean algebra where the NAND function is equivalent to a NOT-AND operation.'}, 'question2': {'question': 'Explain the working of Decimal adder with block diagram and explain the', 'answer': 'A decimal adder is a combinational circuit that adds two decimal numbers using binary addition. It consists of multiple full adder circuits connected in series, with each full adder adding a single digit of the two decimal numbers. The carry output of one full adder is connected to the carry input of the next, allowing for the addition of multiple digits. The final output is the sum of the two decimal numbers in binary form.'}, 'question3': {'question': 'Explain the working of SR latch using NOR gate with the help of logic', 'answer': 'A SR latch is a basic memory element that can store one bit of information. It is constructed using two cross-coupled NOR gates. When both inputs are low, the outputs of the NOR gates are high, keeping the latch in its current state. When one input is high and the other is low, the corresponding output goes low, changing the state of the latch. This change in state is maintained even when the inputs return to their previous state, allowing the latch to store information.'}, 'question4': {'question': 'Explain the working of SR latch with NAND gate with the help of logic diagram', 'answer': 'A SR latch can also be constructed using two cross-coupled NAND gates. When both inputs are high, the outputs of the NAND gates are low, keeping the latch in its current state. When one input is low and the other is high, the corresponding output goes high, changing the state of the latch. This change in state is maintained even when the inputs return to their previous state, allowing the latch to store information.'}, 'question5': {'question': 'Explain the working of RTL and DTL circuit. Explain how fan-out of DTL gate', 'answer': 'RTL (Resistor-Transistor Logic) and DTL (Diode-Transistor Logic) are two types of digital logic families that were commonly used in the early days of digital electronics. RTL circuits use resistors and transistors to implement logic gates, while DTL circuits use diodes and transistors. Both types of circuits have a limited fan-out, which refers to the maximum number of inputs that a gate can drive without affecting its performance. This is due to the relatively high output impedance of the transistors used in these circuits.'}, 'question6': {'question': 'Explain the design procedure of combinational circuit with an example, please provide answers for each question.', 'answer': "The design procedure for a combinational circuit involves the following steps:\n1. Identify the inputs and outputs of the circuit.\n2. Determine the truth table for the desired logic function.\n3. Simplify the logic function using Boolean algebra or Karnaugh maps.\n4. Draw the logic diagram using the simplified expression.\n5. Implement the circuit using the appropriate logic gates.\n\nFor example, let's design a circuit that outputs a high signal when the input is an odd number. The inputs are A (LSB) and B (MSB) and the output is Y. The truth table is:\nA B | Y\n0 0 | 0\n0 1 | 1\n1 0 | 1\n1 1 | 0\n\nSimplifying the logic function, we get Y = A'B + AB'. The logic diagram for this is a XOR gate. By implementing this circuit using two NOT gates and one XOR gate, we can achieve the desired output."}}}
                
                time.sleep(18)
                return Response({
                    'module_questions': module_questions,
                    'structured_reply_text': structured_reply_text,  # Return the structured text
                    'stats':stats
                }, status=status.HTTP_200_OK)
            
            # Print the name of the syllabus file, if it exists
            else:
                for index, pdf in enumerate(pdfs):
                    self.handle_uploaded_file(pdf, f'pdf-{index + 1}.pdf')

                # Uncomment and adjust if syllabus file handling is needed
                if syllabus:
                    self.handle_uploaded_file(syllabus, 'syllabus.pdf')

                main()  # Ensure this is necessary or adjust accordingly

                try:
                    module_questions = self.parse_questions_by_module()
                    # answers=self.module_answers(module_questions)
                    structured_reply_text = self.parse_reply_text()  # Use the new parsing method
                    for topic in structured_reply_text.keys():
                        structured_reply_text[topic]['youtube_link']=self.get_top_video(topic)

                except FileNotFoundError:
                    return Response({'error': 'Required files not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                stats_path = os.path.join(settings.MEDIA_ROOT, 'reply_stats.txt')
                with open(stats_path, 'r') as file:
                    stats = file.read()
                stats=json.loads(stats)
                # print(reply_stats)
                print("final output.......................................................................")
                print("module_questions.....")
                print(module_questions)
                print("structured_reply_text....")
                print(structured_reply_text)
                print("stats....")
                print(stats)
                return Response({
                    'module_questions': module_questions,
                    'structured_reply_text': structured_reply_text,  # Return the structured text
                    'stats':stats
                }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def handle_uploaded_file(self, file, filename):
        pdfs_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
        if not os.path.exists(pdfs_dir):
            os.makedirs(pdfs_dir)
        file_path = os.path.join(pdfs_dir, filename)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
